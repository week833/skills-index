#!/usr/bin/env python3
"""doc-drift-check: list Markdown documents whose watched code changed after
the commit they were verified against.

Read-only: the script never writes, creates or deletes a file. The only
external program it runs is git, always as an argument list without a shell,
and only the read-only subcommands rev-parse, ls-tree, diff-tree and status
(status with --no-optional-locks, so it does not rewrite the index).

Exit codes: 0 every fingerprint current; 1 some drift and no error; 2 any error.
Standard library only. Targets Python 3.9 or later; tested with 3.9, 3.11, 3.12
and 3.13 on Linux.
"""

import argparse
import datetime
import fnmatch
import json
import os
import re
import subprocess
import sys
import traceback
from pathlib import Path, PurePath

TOOL = "doc-drift-check"
FORMAT_VERSION = 1
# A line is a fingerprint candidate when the marker word is followed by a colon
# (ASCII or full-width, optional spaces) or follows "<!--" (optional spaces), in
# any case, so a mistyped marker is reported instead of being skipped. Only the
# strict form "<!-- doc-fingerprint:" (lower case, ASCII colon) parses.
MARKER_RE = re.compile(r"doc-fingerprint\s*[:：]|<!--\s*doc-fingerprint", re.IGNORECASE)
STRICT_MARKER_RE = re.compile(r"<!--\s*doc-fingerprint:")
MARKER_BYTES = tuple("doc-fingerprint".encode(codec)
                     for codec in ("ascii", "utf-16-le", "utf-16-be"))
KEY_TOKEN_RE = re.compile(r"\s[A-Za-z][A-Za-z0-9_-]*=")
OWNERSHIP_HINTS = ("dubious ownership", "unsafe repository", "safe.directory")
DOC_SUFFIXES = (".md", ".markdown")
SKIP_DIRS = frozenset({".git", ".venv", "venv", "node_modules", "__pycache__"})
REPO_NAME_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*")
COMMIT_RE = re.compile(r"[0-9a-fA-F]{7,40}")
DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}")
DRIVE_RE = re.compile(r"[A-Za-z]:")
FINGERPRINT_RE = re.compile(
    r"<!--\s*doc-fingerprint:\s+repo=(?P<repo>\S+)\s+commit=(?P<commit>\S+)"
    r"\s+paths=(?P<paths>.*?)(?:\s+verified=(?P<verified>\S+))?\s*-->"
)
FENCE_RE = re.compile(r"\s*(`{3,}|~{3,})(.*)")
USERINFO_RE = re.compile(r"([A-Za-z][A-Za-z0-9+.-]*://)[^/\s@]+@")
EXPECTED_FORMAT = (
    "<!-- doc-fingerprint: repo=名稱 commit=SHA paths=路徑1,路徑2 verified=YYYY-MM-DD -->"
)
UNMERGED = frozenset({"DD", "AU", "UD", "UA", "DU", "AA", "UU"})
GIT_TIMEOUT_SECONDS = 300
# Global git options for every call. Transports are refused (the default policy
# and the common protocols by name), so a command that would fetch missing
# objects (for example in a partial clone) fails instead of using the network
# or writing into .git.
GIT_OPTIONS = (
    "-c", "protocol.allow=never",
    "-c", "protocol.file.allow=never",
    "-c", "protocol.git.allow=never",
    "-c", "protocol.ssh.allow=never",
    "-c", "protocol.http.allow=never",
    "-c", "protocol.https.allow=never",
    "-c", "protocol.ext.allow=never",
    "-c", "core.fsmonitor=false",
    "-c", "core.quotepath=false",
    "--no-pager",
    "--no-optional-locks",
    "--literal-pathspecs",
)
GIT_ENV_DROP = (
    "GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_COMMON_DIR",
    "GIT_OBJECT_DIRECTORY", "GIT_ALTERNATE_OBJECT_DIRECTORIES", "GIT_NAMESPACE",
)
STATUS_LABELS = {
    "current": "未漂移（current）",
    "drifted": "已漂移（drifted）",
    "error": "錯誤（error）",
}
UNSET = object()


class FingerprintError(ValueError):
    """A line that carries the marker but cannot be parsed."""


class Fingerprint:
    __slots__ = ("repo", "commit", "paths", "verified")

    def __init__(self, repo, commit, paths, verified):
        self.repo = repo
        self.commit = commit
        self.paths = paths
        self.verified = verified


# ---------------------------------------------------------------- parsing


def normalize_repo_path(raw):
    """Repository-relative path with forward slashes; '.' is the whole tree."""
    path = raw.strip().replace("\\", "/")
    if not path:
        raise FingerprintError("paths 有空白項目（多了逗號，或路徑是空的）")
    if path.startswith("/") or DRIVE_RE.match(path):
        raise FingerprintError(
            f"路徑必須相對於儲存庫頂層，不能是絕對路徑或以磁碟代號開頭：{raw.strip()}"
        )
    parts = [part for part in path.split("/") if part not in ("", ".")]
    if ".." in parts:
        raise FingerprintError(f"路徑不能包含 ..：{raw.strip()}")
    return "/".join(parts) if parts else "."


def parse_paths(raw):
    paths = []
    for item in raw.split(","):
        path = normalize_repo_path(item)
        if path not in paths:
            paths.append(path)
    return paths


def parse_fingerprint_line(line):
    text = line.strip()
    if (text.count("<!--") != 1 or text.count("-->") != 1
            or not text.startswith("<!--") or not text.endswith("-->")):
        raise FingerprintError("含標記文字的行必須整行只是一個指紋註解（一行一個，前後不能有其他文字）")
    if STRICT_MARKER_RE.match(text) is None:
        raise FingerprintError(
            f"標記要寫成小寫的 doc-fingerprint 緊接半形冒號；應為 {EXPECTED_FORMAT}")
    match = FINGERPRINT_RE.fullmatch(text)
    if match is None:
        raise FingerprintError(
            f"格式不符；應為 {EXPECTED_FORMAT}（鍵的順序固定，verified 可省略）"
        )
    repo = match.group("repo")
    if repo != "." and REPO_NAME_RE.fullmatch(repo) is None:
        raise FingerprintError(
            f"repo 只能是 . 或由英數字、點、底線、連字號組成的名稱：{repo}"
        )
    commit = match.group("commit")
    if COMMIT_RE.fullmatch(commit) is None:
        raise FingerprintError(f"commit 必須是 7 到 40 位十六進位字元：{commit}")
    paths = parse_paths(match.group("paths"))
    verified = match.group("verified")
    if verified is not None:
        if DATE_RE.fullmatch(verified) is None:
            raise FingerprintError(f"verified 必須是 YYYY-MM-DD：{verified}")
        try:
            datetime.date(int(verified[:4]), int(verified[5:7]), int(verified[8:]))
        except ValueError:
            raise FingerprintError(f"verified 不是有效的日期：{verified}") from None
    return Fingerprint(repo, commit.lower(), paths, verified)


def parse_document(text):
    """Return (entries, fenced, error); entries are (line_no, text, fingerprint, problem).

    Lines inside fenced code blocks are examples, not fingerprints; `fenced` lists
    the numbers of such lines that carry the marker, so they are shown, not hidden.
    A document that ends inside a fence which hid marker lines is an error.
    """
    entries = []
    fenced = []
    fence = None
    hidden = []
    for number, line in enumerate(text.split("\n"), 1):
        if line.endswith("\r"):
            line = line[:-1]
        if fence is not None:
            stripped = line.strip()
            if len(stripped) >= fence[1] and stripped == fence[0] * len(stripped):
                fence = None
                fenced.extend(hidden)
                hidden = []
            elif MARKER_RE.search(line):
                hidden.append(number)
            continue
        match = FENCE_RE.fullmatch(line)
        if match and not (match.group(1)[0] == "`" and "`" in match.group(2)):
            fence = (match.group(1)[0], len(match.group(1)), number)
            continue
        if MARKER_RE.search(line):
            stripped = line.strip()
            try:
                entries.append((number, stripped, parse_fingerprint_line(stripped), None))
            except FingerprintError as exc:
                entries.append((number, stripped, None, str(exc)))
    error = None
    if fence is not None and hidden:
        lines = "、".join(str(n) for n in hidden)
        error = (
            f"第 {fence[2]} 行開始的程式碼區塊到文件結尾都沒有結束；"
            f"區塊內第 {lines} 行的指紋沒有被讀取"
        )
    return entries, fenced, error


def parse_repo_option(value):
    """Split NAME=PATH on the first '=' only (Windows paths contain ':' and '\\')."""
    name, sep, path = value.partition("=")
    name = name.strip()
    path = path.strip()
    if not sep or not name or not path:
        raise ValueError(f"--repo 的格式應為 名稱=路徑：{value}")
    if name == "." or REPO_NAME_RE.fullmatch(name) is None:
        raise ValueError(
            f"--repo 的名稱只能由英數字、點、底線、連字號組成，且不能是 .：{name}"
        )
    return name, path


# ----------------------------------------------------------- paths, output


def fs_display(path):
    """Readable text for a filesystem path (str or Path), independent of the locale."""
    if os.name == "nt":
        return str(path).replace("\\", "/")
    return os.fsencode(path).decode("utf-8", "replace")


def fs_arg(path):
    return str(path) if os.name == "nt" else os.fsencode(path)


def clean_lines(text):
    """Non-empty stripped lines with URL credentials masked."""
    return [USERINFO_RE.sub(r"\1***@", line.strip()) for line in text.splitlines() if line.strip()]


def clean_message(text):
    return " / ".join(clean_lines(text))


def force_utf8_stdio():
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            try:
                reconfigure(encoding="utf-8", errors="replace")
            except (OSError, ValueError):
                pass


# --------------------------------------------------------------------- git


class GitResult:
    __slots__ = ("ok", "out", "err", "lines", "launched")

    def __init__(self, ok, out, err, lines=(), launched=True):
        self.ok = ok
        self.out = out
        self.err = err
        self.lines = list(lines) or ([err] if err else [])
        self.launched = launched


def git_env():
    env = dict(os.environ)
    for key in GIT_ENV_DROP:
        env.pop(key, None)
    env["LC_ALL"] = "C"
    return env


def run_git(directory, args):
    """Run one read-only git command in `directory`; never through a shell."""
    command = ["git", *GIT_OPTIONS, "-C", directory, *args]
    if os.name != "nt":
        command = [a if isinstance(a, bytes) else a.encode("utf-8") for a in command]
    try:
        proc = subprocess.run(
            command,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=git_env(),
            timeout=GIT_TIMEOUT_SECONDS,
            check=False,
        )
    except FileNotFoundError:
        return GitResult(False, b"", "找不到 git 可執行檔；請確認已安裝 git 並在 PATH 中",
                         launched=False)
    except subprocess.TimeoutExpired:
        return GitResult(False, b"", f"git 超過 {GIT_TIMEOUT_SECONDS} 秒沒有結束")
    except OSError as exc:
        return GitResult(False, b"", str(exc), launched=False)
    lines = clean_lines(proc.stderr.decode("utf-8", "replace"))
    return GitResult(proc.returncode == 0, proc.stdout, " / ".join(lines), lines)


def work_tree_problem(res, where):
    """Reason text when git cannot open `where` as a work tree.

    git's own advice for a repository owned by another user is to change the
    global git configuration; that advice is dropped, because changing git
    settings is the user's decision, not the checker's.
    """
    if not res.launched:
        return f"無法執行 git：{res.err}"
    if any(hint in res.err for hint in OWNERSHIP_HINTS):
        return (f"{where}的儲存庫被 git 拒絕讀取：儲存庫的擁有者不是目前的使用者（git 的 safe.directory "
                f"檢查；git：{res.lines[0]}）。檢查程式沒有改動 git 設定，要不要加入例外由使用者決定")
    if "not a git repository" in res.err:
        return f"{where}不在 git 工作目錄內（git：{res.err}）"
    return f"{where}所屬的儲存庫無法由 git 判斷（git：{res.err}）"


def decode_git_path(raw):
    return raw.decode("utf-8", "replace")


def parse_toplevel(out):
    lines = out.split(b"\n")
    top = lines[0].rstrip(b"\r")
    prefix = lines[1].rstrip(b"\r") if len(lines) > 1 else b""
    if os.name == "nt":
        top = top.decode("utf-8", "replace")
    return top, decode_git_path(prefix)


def change(status, path, old_path=None):
    return {"status": status, "path": path, "old_path": old_path}


def parse_name_status(out):
    tokens = out.split(b"\0")
    entries = []
    index = 0
    while index < len(tokens) and tokens[index]:
        status = tokens[index].decode("ascii", "replace")
        index += 1
        if status[:1] in ("R", "C"):
            old, new = tokens[index], tokens[index + 1]
            index += 2
            entries.append(change(status[0], decode_git_path(new), decode_git_path(old)))
        else:
            entries.append(change(status[:1], decode_git_path(tokens[index])))
            index += 1
    return entries


def parse_porcelain(out):
    result = {"staged": [], "unstaged": [], "untracked": []}
    tokens = out.split(b"\0")
    index = 0
    while index < len(tokens):
        token = tokens[index]
        index += 1
        if len(token) < 4:
            continue
        code = token[:2].decode("ascii", "replace")
        path = decode_git_path(token[3:])
        old = None
        if "R" in code or "C" in code:
            old = decode_git_path(tokens[index])
            index += 1
        if code == "??":
            result["untracked"].append(change("??", path))
        elif code == "!!":
            continue
        elif code in UNMERGED:
            result["unstaged"].append(change("U", path))
        else:
            if code[0] != " ":
                result["staged"].append(
                    change(code[0], path, old if code[0] in "RC" else None))
            if code[1] != " ":
                result["unstaged"].append(
                    change(code[1], path, old if code[1] in "RC" else None))
    return result


class Repository:
    def __init__(self, top):
        self.top = top
        self.display = top if isinstance(top, str) else decode_git_path(top)
        self._head = UNSET
        self._shallow = UNSET
        self._status = UNSET
        self._commits = {}
        self._exists = {}
        self._diffs = {}

    def git(self, *args):
        return run_git(self.top, list(args))

    def head(self):
        if self._head is UNSET:
            res = self.git("rev-parse", "--verify", "--quiet", "HEAD^{commit}")
            if res.ok:
                self._head = (res.out.decode("ascii").strip(), None)
            else:
                self._head = (None, f"儲存庫 {self.display} 沒有任何 commit（HEAD 不存在）")
        return self._head

    def is_shallow(self):
        if self._shallow is UNSET:
            res = self.git("rev-parse", "--is-shallow-repository")
            answer = res.out.decode("ascii", "replace").strip() if res.ok else ""
            self._shallow = {"true": True, "false": False}.get(answer)
        return self._shallow

    def resolve_commit(self, commit):
        if commit not in self._commits:
            res = self.git("rev-parse", "--verify", "--quiet", commit + "^{commit}")
            if res.ok:
                self._commits[commit] = (res.out.decode("ascii").strip(), None)
            else:
                note = {True: "；這個儲存庫是淺層 clone",
                        False: "；這個儲存庫不是淺層 clone"}.get(self.is_shallow(), "")
                self._commits[commit] = (None, (
                    f"commit {commit} 在儲存庫 {self.display} 中無法對應到唯一的 commit"
                    f"（可能打錯、歷史被改寫，或淺層 clone 缺少這個 commit{note}）"))
        return self._commits[commit]

    def path_exists(self, treeish, path):
        key = (treeish, path)
        if key not in self._exists:
            res = self.git("ls-tree", "-z", treeish, "--", path)
            if not res.ok:
                self._exists[key] = (None, f"git ls-tree 執行失敗：{res.err}")
            else:
                names = {decode_git_path(item.split(b"\t", 1)[1])
                         for item in res.out.split(b"\0") if b"\t" in item}
                self._exists[key] = (path in names, None)
        return self._exists[key]

    def committed_changes(self, base, head):
        if base == head:
            return [], None
        key = (base, head)
        if key not in self._diffs:
            res = self.git("diff-tree", "-r", "-z", "--name-status", "-M", base, head)
            if res.ok:
                self._diffs[key] = (parse_name_status(res.out), None)
            else:
                self._diffs[key] = (None, f"git diff-tree 執行失敗：{res.err}")
        return self._diffs[key]

    def worktree_changes(self):
        if self._status is UNSET:
            res = self.git("status", "--porcelain=v1", "-z", "--untracked-files=all")
            if res.ok:
                self._status = (parse_porcelain(res.out), None)
            else:
                self._status = (None, f"git status 執行失敗：{res.err}")
        return self._status


class Registry:
    """Resolves repo names and document folders to repositories (cached)."""

    def __init__(self, mapping):
        self.mapping = mapping
        self._by_top = {}
        self._named = {}
        self._dirs = {}

    def _repository(self, top):
        if top not in self._by_top:
            self._by_top[top] = Repository(top)
        return self._by_top[top]

    def for_directory(self, directory):
        if directory not in self._dirs:
            res = run_git(fs_arg(directory), ["rev-parse", "--show-toplevel", "--show-prefix"])
            if res.ok:
                top, prefix = parse_toplevel(res.out)
                self._dirs[directory] = (self._repository(top), prefix, None)
            else:
                problem = work_tree_problem(res, "文件所在的資料夾")
                if problem.startswith("文件所在的資料夾不在"):
                    problem = "repo=. 需要文件位於 git 工作目錄內；" + problem
                self._dirs[directory] = (None, None, problem)
        return self._dirs[directory]

    def for_name(self, name):
        if name not in self._named:
            if name not in self.mapping:
                self._named[name] = (None, (
                    f"repo 名稱 {name} 沒有對應的儲存庫；請加上 --repo {name}=儲存庫頂層路徑"))
            else:
                path = self.mapping[name]
                shown = fs_display(path)
                res = run_git(fs_arg(Path(path)), ["rev-parse", "--show-toplevel", "--show-prefix"])
                if not res.ok:
                    self._named[name] = (None, work_tree_problem(res, f"--repo {name} 指向的 {shown} "))
                else:
                    top, prefix = parse_toplevel(res.out)
                    repo = self._repository(top)
                    if prefix:
                        self._named[name] = (None, (
                            f"--repo {name} 指向的 {shown} 不是儲存庫頂層；頂層是 {repo.display}"))
                    else:
                        self._named[name] = (repo, None)
        return self._named[name]


# ------------------------------------------------------------------ checks


def within(path, watched):
    path = path.rstrip("/")
    for item in watched:
        if item == "." or path == item or path.startswith(item + "/"):
            return True
    return False


def select_changes(entries, watched, own_path):
    selected = []
    for entry in entries:
        if own_path is not None and own_path in (entry["path"].rstrip("/"), entry["old_path"]):
            continue
        if within(entry["path"], watched) or (
                entry["old_path"] is not None and within(entry["old_path"], watched)):
            selected.append(dict(entry))
    return selected


class Document:
    def __init__(self, fs_path, display, registry):
        self.fs_path = fs_path
        self.display = display
        self.registry = registry
        self._repo = UNSET

    def own_repository(self):
        if self._repo is UNSET:
            self._repo = self.registry.for_directory(self.fs_path.parent)
        return self._repo

    def own_path_in(self, repo):
        own_repo, prefix, _ = self.own_repository()
        if own_repo is repo and prefix is not None:
            return prefix + fs_display(self.fs_path.name)
        return None


def new_result(line_no, text, fingerprint):
    return {
        "line": line_no,
        "text": text,
        "repo": fingerprint.repo if fingerprint else None,
        "commit": fingerprint.commit if fingerprint else None,
        "paths": list(fingerprint.paths) if fingerprint else [],
        "verified": fingerprint.verified if fingerprint else None,
        "status": "error",
        "reason": None,
        "repository": None,
        "commit_full": None,
        "head": None,
        "committed": [],
        "uncommitted": {"staged": [], "unstaged": [], "untracked": []},
    }


def check_fingerprint(line_no, text, fp, document, registry):
    result = new_result(line_no, text, fp)

    def fail(reason):
        result["reason"] = reason
        return result

    if fp.repo == ".":
        repo, _, error = document.own_repository()
        if error:
            return fail(error)
    else:
        repo, error = registry.for_name(fp.repo)
        if error:
            return fail(error)
    result["repository"] = repo.display
    head, error = repo.head()
    if error:
        return fail(error)
    result["head"] = head
    full, error = repo.resolve_commit(fp.commit)
    if error:
        return fail(error)
    result["commit_full"] = full
    pending, error = repo.worktree_changes()
    if error:
        return fail(error)
    missing = []
    for path in fp.paths:
        if path == ".":
            continue
        found = False
        for treeish in (full, head):
            found, error = repo.path_exists(treeish, path)
            if error:
                return fail(error)
            if found:
                break
        if not found:
            missing.append(path)
    if missing:
        reason = f"以下路徑在 commit {fp.commit} 與 HEAD 都不存在（可能打錯）：" + "、".join(missing)
        uncommitted = [p for p in missing if any(
            select_changes(pending[kind], [p], None) for kind in ("staged", "unstaged", "untracked"))]
        if uncommitted:
            reason += "；其中 " + "、".join(uncommitted) + " 只出現在未提交的變更"
        if any("，" in p for p in missing):
            reason += "；paths 要用半形逗號「,」分隔"
        if any(KEY_TOKEN_RE.search(p) for p in missing):
            reason += "；路徑裡似乎有其他鍵，鍵只有 repo、commit、paths、verified，順序固定"
        return fail(reason)
    committed, error = repo.committed_changes(full, head)
    if error:
        return fail(error)
    own_path = document.own_path_in(repo)
    result["committed"] = select_changes(committed, fp.paths, own_path)
    for kind in ("staged", "unstaged", "untracked"):
        result["uncommitted"][kind] = select_changes(pending[kind], fp.paths, own_path)
    drifted = bool(result["committed"]) or any(result["uncommitted"].values())
    result["status"] = "drifted" if drifted else "current"
    return result


# -------------------------------------------------------------- documents


def excluded(candidates, patterns):
    return any(fnmatch.fnmatchcase(c, p) for c in candidates for p in patterns)


def collect_documents(doc_args, patterns):
    """Documents as (Path, display) pairs: files in argument order, folders scanned
    depth-first with each folder's files (sorted) before its subfolders (sorted)."""
    documents = []
    errors = []
    seen = set()

    def add(path):
        key = os.path.normcase(str(path.resolve()))
        if key not in seen:
            seen.add(key)
            documents.append((path, fs_display(path)))

    def scan(folder, rel_folder):
        try:
            entries = sorted(folder.iterdir(), key=lambda entry: entry.name)
        except OSError as exc:
            errors.append(f"無法讀取資料夾 {fs_display(folder)}：{exc.strerror or exc}")
            return
        subfolders = []
        for entry in entries:
            rel = rel_folder / entry.name
            if excluded((fs_display(entry), fs_display(rel), fs_display(entry.name)), patterns):
                continue
            try:
                is_folder = entry.is_dir() and not entry.is_symlink()
            except OSError as exc:  # e.g. a folder that can be listed but not entered
                errors.append(f"無法讀取資料夾 {fs_display(folder)} 的內容：{exc.strerror or exc}")
                break
            if is_folder:
                if entry.name not in SKIP_DIRS:
                    subfolders.append((entry, rel))
            elif entry.name.lower().endswith(DOC_SUFFIXES):
                add(entry)
        for entry, rel in subfolders:
            scan(entry, rel)

    for arg in doc_args:
        if not arg.strip():
            errors.append("--docs 的值是空的")
            continue
        path = Path(arg)
        try:
            is_file = path.is_file()
            is_folder = not is_file and path.is_dir()
        except OSError as exc:
            errors.append(f"無法讀取 --docs 指定的路徑 {fs_display(arg)}：{exc.strerror or exc}")
            continue
        if is_file:
            if not excluded((fs_display(path), fs_display(path.name)), patterns):
                add(path)
        elif is_folder:
            scan(path, PurePath())
        else:
            errors.append(f"--docs 指定的路徑不存在：{fs_display(arg)}")
    return documents, errors


def read_document(path):
    """Return (entries, fenced, error) for one document file."""
    try:
        raw = path.read_bytes()
    except OSError as exc:
        return [], [], f"無法讀取文件：{exc.strerror or exc}"
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        text = None
    if text is None or "\0" in text:  # not UTF-8 text, e.g. UTF-16 or Big5
        lowered = raw.lower()
        if any(marker in lowered for marker in MARKER_BYTES):
            return [], [], "文件不是 UTF-8 文字（例如 UTF-16 或 Big5），無法可靠讀取其中的指紋"
        return [], [], None
    return parse_document(text)


def build_report(options):
    run_errors = []
    mapping = {}
    for item in options.repo:
        try:
            name, path = parse_repo_option(item)
        except ValueError as exc:
            run_errors.append(str(exc))
            continue
        if name in mapping and mapping[name] != path:
            run_errors.append(f"--repo {name} 指定了兩個不同的路徑")
            continue
        mapping[name] = path
    patterns = [fs_display(p).replace("\\", "/") for p in options.exclude]
    doc_args = options.docs or ["."]
    documents, errors = collect_documents(doc_args, patterns)
    run_errors.extend(errors)
    if not documents and not errors:
        shown = "、".join(fs_display(a) for a in doc_args)
        run_errors.append(f"在 {shown} 找不到任何 .md 或 .markdown 文件")

    registry = Registry(mapping)
    reports = []
    unfingerprinted = []
    for fs_path, display in documents:
        entries, fenced, doc_error = read_document(fs_path)
        if not entries and doc_error is None:
            unfingerprinted.append(display)
            if not fenced:
                continue
        document = Document(fs_path, display, registry)
        results = []
        for line_no, text, fingerprint, problem in entries:
            if fingerprint is None:
                result = new_result(line_no, text, None)
                result["reason"] = f"第 {line_no} 行的指紋格式錯誤：{problem}"
                results.append(result)
            else:
                results.append(check_fingerprint(line_no, text, fingerprint, document, registry))
        reports.append({"path": display, "error": doc_error, "fingerprints": results,
                        "fenced_lines": fenced})

    statuses = [fp["status"] for doc in reports for fp in doc["fingerprints"]]
    summary = {
        "documents_scanned": len(documents),
        "documents_with_fingerprints": sum(1 for doc in reports if doc["fingerprints"]),
        "documents_without_fingerprints": len(unfingerprinted),
        "document_errors": sum(1 for doc in reports if doc["error"]),
        "fingerprints": len(statuses),
        "current": statuses.count("current"),
        "drifted": statuses.count("drifted"),
        "error": statuses.count("error"),
        "fenced_lines": sum(len(doc["fenced_lines"]) for doc in reports),
        "run_errors": len(run_errors),
    }
    if summary["error"] or summary["document_errors"] or run_errors:
        exit_code = 2
    elif summary["drifted"]:
        exit_code = 1
    else:
        exit_code = 0
    return {
        "tool": TOOL,
        "format_version": FORMAT_VERSION,
        "exit_code": exit_code,
        "summary": summary,
        "run_errors": run_errors,
        "documents": reports,
        "unfingerprinted": unfingerprinted if options.list_unfingerprinted else None,
    }


# ------------------------------------------------------------------ output


def format_change(entry):
    if entry["old_path"] is not None:
        return f"{entry['status']:<2} {entry['old_path']} -> {entry['path']}"
    return f"{entry['status']:<2} {entry['path']}"


def summary_line(report):
    s = report["summary"]
    if s["fingerprints"]:
        checked = (f"指紋 {s['fingerprints']} 個（未漂移 {s['current']}、"
                   f"已漂移 {s['drifted']}、錯誤 {s['error']}）")
    else:
        checked = "指紋 0 個（沒有找到任何指紋，未比對任何文件）"
    if s["fenced_lines"]:
        checked += f"；程式碼區塊內的標記行 {s['fenced_lines']} 行（視為範例，未檢查）"
    return (f"摘要：掃描文件 {s['documents_scanned']} 份（有指紋 {s['documents_with_fingerprints']} 份、"
            f"沒有指紋 {s['documents_without_fingerprints']} 份、文件錯誤 {s['document_errors']} 份）；"
            f"{checked}；執行錯誤 {s['run_errors']} 個；結束代碼 {report['exit_code']}。")


def render_text(report):
    lines = [f"{TOOL}：唯讀檢查文件指紋", ""]
    for message in report["run_errors"]:
        lines.append("執行錯誤：" + message)
    if report["run_errors"]:
        lines.append("")
    groups = (("staged", "未提交的變更（暫存區）"),
              ("unstaged", "未提交的變更（未暫存）"),
              ("untracked", "未提交的變更（未追蹤）"))
    for doc in report["documents"]:
        lines.append("文件：" + doc["path"])
        if doc["error"]:
            lines.append("  文件錯誤：" + doc["error"])
        if doc["fenced_lines"]:
            numbers = "、".join(str(n) for n in doc["fenced_lines"])
            lines.append(f"  程式碼區塊內的標記行（視為範例，未檢查）：第 {numbers} 行")
        for fp in doc["fingerprints"]:
            lines.append(f"  第 {fp['line']} 行：{fp['text']}")
            lines.append("    狀態：" + STATUS_LABELS[fp["status"]])
            if fp["reason"]:
                lines.append("    原因：" + fp["reason"])
            if fp["repository"]:
                lines.append("    儲存庫：" + fp["repository"])
            if fp["commit_full"] and fp["head"]:
                lines.append(f"    比對範圍：{fp['commit_full'][:12]}..{fp['head'][:12]}（HEAD）")
            if fp["committed"]:
                lines.append("    已提交的變更：")
                lines.extend("      " + format_change(c) for c in fp["committed"])
            for kind, label in groups:
                if fp["uncommitted"][kind]:
                    lines.append(f"    {label}：")
                    lines.extend("      " + format_change(c) for c in fp["uncommitted"][kind])
        lines.append("")
    if report["unfingerprinted"] is not None:
        lines.append(f"沒有指紋的文件（{len(report['unfingerprinted'])} 份）：")
        lines.extend("  " + path for path in report["unfingerprinted"])
        lines.append("")
    lines.append(summary_line(report))
    return "\n".join(lines) + "\n"


class ZhHelpFormatter(argparse.HelpFormatter):
    def add_usage(self, usage, actions, groups, prefix=None):
        return super().add_usage(usage, actions, groups, "用法：")


class ZhArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        self.print_usage(sys.stderr)
        self.exit(2, f"{self.prog}：命令列參數錯誤（argparse 原文：{message}）\n")


def build_parser():
    parser = ZhArgumentParser(
        prog="check_doc_drift.py",
        description=("唯讀檢查 Markdown 文件中的 doc-fingerprint 指紋：比對核對時的 commit 與 HEAD，"
                     "並另外列出未提交的變更。只提示哪些文件需要重新查核，不判斷內容對錯。"),
        epilog="結束代碼：0 全部未漂移；1 有漂移且沒有錯誤；2 至少一個錯誤。",
        formatter_class=ZhHelpFormatter,
        add_help=False,
    )
    group = parser.add_argument_group()  # no heading: argparse would add an ASCII colon
    group.add_argument("-h", "--help", action="help", help="顯示這段說明後結束")
    group.add_argument("--docs", nargs="+", action="extend", default=[], metavar="PATH",
                       help="要掃描的文件或資料夾（預設：目前資料夾）；資料夾會遞迴尋找 .md 與 .markdown")
    group.add_argument("--repo", nargs="+", action="extend", default=[], metavar="NAME=PATH",
                       help="把指紋的 repo 名稱對應到本機 clone 的頂層資料夾；可重複")
    group.add_argument("--exclude", nargs="+", action="extend", default=[], metavar="GLOB",
                       help="略過路徑或名稱符合 GLOB 的文件與資料夾；可重複")
    group.add_argument("--json", action="store_true",
                       help="只在 stdout 輸出一份 JSON 文件")
    group.add_argument("--list-unfingerprinted", action="store_true",
                       help="另外列出沒有任何指紋的文件")
    return parser


def main(argv=None):
    force_utf8_stdio()
    options = build_parser().parse_args(argv)
    report = build_report(options)
    if options.json:
        sys.stdout.write(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    else:
        sys.stdout.write(render_text(report))
    sys.stdout.flush()
    return report["exit_code"]


if __name__ == "__main__":
    try:
        exit_code = main()
    except KeyboardInterrupt:
        exit_code = 2
    except Exception:  # an internal failure must never look like drift (exit 1)
        sys.stderr.write(f"{TOOL} 內部錯誤：\n")
        traceback.print_exc()
        exit_code = 2
    sys.exit(exit_code)
