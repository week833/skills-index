"""Tests for check_doc_drift.py (standard library unittest; pytest can run it too).

Every test builds throwaway git repositories in a temporary directory, with git
isolated from the user's configuration (HOME and GIT_CONFIG_GLOBAL point to the
temporary directory, GIT_CONFIG_NOSYSTEM=1). Run from the skill folder:

    python -B -m unittest discover -s scripts -p "test_*.py"
    python -B -m pytest -q -p no:cacheprovider scripts/test_check_doc_drift.py
"""

import hashlib
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.dont_write_bytecode = True

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "check_doc_drift.py"
SKILL_DIR = HERE.parent


def _load_module():
    spec = importlib.util.spec_from_file_location("check_doc_drift", str(SCRIPT))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


cdd = _load_module()

TOP_KEYS = ["tool", "format_version", "exit_code", "summary", "run_errors",
            "documents", "unfingerprinted"]
SUMMARY_KEYS = ["documents_scanned", "documents_with_fingerprints",
                "documents_without_fingerprints", "document_errors", "fingerprints",
                "current", "drifted", "error", "fenced_lines", "run_errors"]
DOC_KEYS = ["path", "error", "fingerprints", "fenced_lines"]
FP_KEYS = ["line", "text", "repo", "commit", "paths", "verified", "status", "reason",
           "repository", "commit_full", "head", "committed", "uncommitted"]
PENDING_KEYS = ["staged", "unstaged", "untracked"]
CHANGE_KEYS = ["status", "path", "old_path"]


def fp_line(commit, paths, repo=".", verified="2026-11-13"):
    line = f"<!-- doc-fingerprint: repo={repo} commit={commit} paths={paths}"
    if verified:
        line += f" verified={verified}"
    return line + " -->"


def snapshot(root):
    """Every directory and file under root (including .git) with a content hash."""
    listing = {}
    for path in sorted(Path(root).rglob("*")):
        rel = path.relative_to(root).as_posix()
        if path.is_dir() and not path.is_symlink():
            listing[rel + "/"] = "dir"
        else:
            listing[rel] = hashlib.sha256(path.read_bytes()).hexdigest()
    return listing


class Sandbox:
    def __init__(self):
        self._tmp = tempfile.TemporaryDirectory(prefix="doc-drift-test-")
        self.root = Path(self._tmp.name)
        home = self.root / "home"
        home.mkdir()
        (home / "gitconfig").write_bytes(b"")
        env = {k: v for k, v in os.environ.items() if not k.upper().startswith("GIT_")}
        env.update({
            "HOME": str(home),
            "XDG_CONFIG_HOME": str(home / "xdg"),
            "GIT_CONFIG_GLOBAL": str(home / "gitconfig"),
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_CEILING_DIRECTORIES": str(self.root),
            "GIT_TERMINAL_PROMPT": "0",
            "PYTHONDONTWRITEBYTECODE": "1",
        })
        self.env = env

    def cleanup(self):
        self._tmp.cleanup()

    def git(self, repo, *args, check=True):
        proc = subprocess.run(["git", "-C", str(repo), *args], env=self.env,
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if check and proc.returncode != 0:
            raise AssertionError("git %s failed: %s" % (
                " ".join(args), proc.stderr.decode("utf-8", "replace")))
        return proc.stdout.decode("utf-8")

    def init_repo(self, name):
        repo = self.root / name
        repo.mkdir(parents=True)
        self.git(repo, "-c", "init.defaultBranch=main", "init", "-q")
        return repo

    def write(self, base, rel, text):
        path = Path(base, *rel.split("/"))
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(text.encode("utf-8"))
        return path

    def commit(self, repo, message="change"):
        self.git(repo, "add", "-A")
        self.git(repo, "-c", "user.name=Doc Drift Test",
                 "-c", "user.email=doc-drift-test@example.invalid",
                 "-c", "commit.gpgsign=false", "commit", "-q", "-m", message)
        return self.git(repo, "rev-parse", "HEAD").strip()

    def run(self, *args, cwd=None, env_extra=None, env_drop=(), python_options=()):
        env = dict(self.env)
        for key in env_drop:
            env.pop(key, None)
        env.update(env_extra or {})
        return subprocess.run(
            [sys.executable, "-B", *python_options, str(SCRIPT), *[str(a) for a in args]],
            cwd=str(cwd or self.root), env=env,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)


class DriftTestCase(unittest.TestCase):
    def setUp(self):
        self.box = Sandbox()
        self.addCleanup(self.box.cleanup)
        self.repo = self.box.init_repo("app")
        self.box.write(self.repo, "src/model.py", "def predict():\n    return 1\n")
        self.box.write(self.repo, "src/features/a.py", "A = 1\n")
        self.box.write(self.repo, "config/settings.json", "{}\n")
        self.box.write(self.repo, "notes.txt", "notes\n")
        self.base = self.box.commit(self.repo, "base")

    def doc(self, *lines, rel="docs/guide.md", base=None):
        body = "# 說明文件\n\n" + "\n".join(lines) + "\n"
        return self.box.write(base or self.repo, rel, body)

    def check(self, *args, **kwargs):
        proc = self.box.run("--json", *args, **kwargs)
        self.assertEqual(proc.stderr.decode("utf-8", "replace"), "")
        report = json.loads(proc.stdout.decode("utf-8"))
        self.assertEqual(proc.returncode, report["exit_code"])
        return proc.returncode, report

    def only_fp(self, report):
        self.assertEqual(len(report["documents"]), 1)
        self.assertEqual(len(report["documents"][0]["fingerprints"]), 1)
        return report["documents"][0]["fingerprints"][0]


class StatusTests(DriftTestCase):
    def test_current(self):
        self.doc(fp_line(self.base[:7], "src/model.py,config"))
        code, report = self.check("--docs", self.repo / "docs")
        fp = self.only_fp(report)
        self.assertEqual(code, 0)
        self.assertEqual(fp["status"], "current")
        self.assertEqual(fp["commit_full"], self.base)
        self.assertEqual(fp["head"], self.base)
        self.assertEqual(fp["committed"], [])
        self.assertEqual(fp["uncommitted"], {"staged": [], "unstaged": [], "untracked": []})

    def test_committed_change_inside_watched_path(self):
        self.doc(fp_line(self.base, "src"))
        self.box.write(self.repo, "src/model.py", "def predict():\n    return 2\n")
        self.box.write(self.repo, "src/features/added.py", "N = 1\n")
        head = self.box.commit(self.repo)
        code, report = self.check("--docs", self.repo / "docs")
        fp = self.only_fp(report)
        self.assertEqual(code, 1)
        self.assertEqual(fp["status"], "drifted")
        self.assertEqual(fp["head"], head)
        self.assertCountEqual(fp["committed"], [
            {"status": "M", "path": "src/model.py", "old_path": None},
            {"status": "A", "path": "src/features/added.py", "old_path": None},
        ])

    def test_committed_change_outside_watched_paths(self):
        self.doc(fp_line(self.base, "src"))
        self.box.write(self.repo, "notes.txt", "more notes\n")
        self.box.write(self.repo, "src_old/model.py", "old\n")
        self.box.commit(self.repo)
        code, report = self.check("--docs", self.repo / "docs")
        self.assertEqual(code, 0)
        self.assertEqual(self.only_fp(report)["status"], "current")

    def test_unstaged_edit(self):
        self.doc(fp_line(self.base, "src/model.py"))
        self.box.write(self.repo, "src/model.py", "def predict():\n    return 3\n")
        code, report = self.check("--docs", self.repo / "docs")
        fp = self.only_fp(report)
        self.assertEqual(code, 1)
        self.assertEqual(fp["committed"], [])
        self.assertEqual(fp["uncommitted"]["unstaged"],
                         [{"status": "M", "path": "src/model.py", "old_path": None}])
        self.assertEqual(fp["uncommitted"]["staged"], [])

    def test_staged_edit(self):
        self.doc(fp_line(self.base, "src/model.py"))
        self.box.write(self.repo, "src/model.py", "def predict():\n    return 4\n")
        self.box.git(self.repo, "add", "src/model.py")
        code, report = self.check("--docs", self.repo / "docs")
        fp = self.only_fp(report)
        self.assertEqual(code, 1)
        self.assertEqual(fp["uncommitted"]["staged"],
                         [{"status": "M", "path": "src/model.py", "old_path": None}])
        self.assertEqual(fp["uncommitted"]["unstaged"], [])

    def test_untracked_file_in_watched_directory(self):
        self.doc(fp_line(self.base, "src/features"))
        self.box.write(self.repo, "src/features/new_feature.py", "B = 2\n")
        self.box.write(self.repo, "src/features/new_pkg/deep.py", "D = 1\n")
        code, report = self.check("--docs", self.repo / "docs")
        fp = self.only_fp(report)
        self.assertEqual(code, 1)
        self.assertEqual(fp["uncommitted"]["untracked"],
                         [{"status": "??", "path": "src/features/new_feature.py",
                           "old_path": None},
                          {"status": "??", "path": "src/features/new_pkg/deep.py",
                           "old_path": None}])

    def test_ignored_files_are_not_reported(self):
        self.box.write(self.repo, ".gitignore", "*.log\n")
        base = self.box.commit(self.repo, "ignore logs")
        self.doc(fp_line(base, "src"))
        self.box.write(self.repo, "src/features/run.log", "log\n")
        code, report = self.check("--docs", self.repo / "docs")
        self.assertEqual(code, 0)
        self.assertEqual(self.only_fp(report)["status"], "current")

    def test_deleted_path(self):
        self.doc(fp_line(self.base, "src/features/a.py"))
        self.box.git(self.repo, "rm", "-q", "src/features/a.py")
        self.box.commit(self.repo)
        code, report = self.check("--docs", self.repo / "docs")
        fp = self.only_fp(report)
        self.assertEqual(code, 1)
        self.assertEqual(fp["status"], "drifted")
        self.assertEqual(fp["committed"],
                         [{"status": "D", "path": "src/features/a.py", "old_path": None}])

    def test_renamed_file(self):
        self.doc(fp_line(self.base, "src/model.py,src/features"))
        (self.repo / "lib").mkdir()
        self.box.git(self.repo, "mv", "src/model.py", "lib/model.py")
        self.box.git(self.repo, "mv", "src/features/a.py", "src/features/a2.py")
        self.box.commit(self.repo)
        code, report = self.check("--docs", self.repo / "docs")
        fp = self.only_fp(report)
        self.assertEqual(code, 1)
        self.assertCountEqual(fp["committed"], [
            {"status": "R", "path": "lib/model.py", "old_path": "src/model.py"},
            {"status": "R", "path": "src/features/a2.py", "old_path": "src/features/a.py"},
        ])
        text = self.box.run("--docs", self.repo / "docs").stdout.decode("utf-8")
        self.assertIn("R  src/model.py -> lib/model.py", text)

    def test_staged_rename(self):
        # porcelain v1 with -z prints the new path first and the old path second
        self.doc(fp_line(self.base, "src/model.py"))
        (self.repo / "lib").mkdir()
        self.box.git(self.repo, "mv", "src/model.py", "lib/model.py")
        code, report = self.check("--docs", self.repo / "docs")
        fp = self.only_fp(report)
        self.assertEqual(code, 1)
        self.assertEqual(fp["uncommitted"]["staged"],
                         [{"status": "R", "path": "lib/model.py", "old_path": "src/model.py"}])
        text = self.box.run("--docs", self.repo / "docs").stdout.decode("utf-8")
        self.assertIn("R  src/model.py -> lib/model.py", text)

    @unittest.skipIf(os.name == "nt", "creating symlinks needs extra rights on Windows")
    def test_type_change(self):
        self.doc(fp_line(self.base, "src/features/a.py"))
        target = self.repo / "src" / "features" / "a.py"
        target.unlink()
        target.symlink_to("../model.py")
        self.box.commit(self.repo)
        code, report = self.check("--docs", self.repo / "docs")
        self.assertEqual(code, 1)
        self.assertEqual(self.only_fp(report)["committed"],
                         [{"status": "T", "path": "src/features/a.py", "old_path": None}])

    def test_whole_repository_path(self):
        self.doc(fp_line(self.base, "."))
        self.box.commit(self.repo, "add the document itself")
        code, report = self.check("--docs", self.repo / "docs")
        self.assertEqual(code, 0)
        self.box.write(self.repo, "notes.txt", "changed\n")
        code, report = self.check("--docs", self.repo / "docs")
        self.assertEqual(code, 1)
        self.assertEqual(self.only_fp(report)["uncommitted"]["unstaged"][0]["path"], "notes.txt")

    def test_document_is_not_its_own_drift(self):
        self.doc(fp_line(self.base, "docs,src"))
        self.box.commit(self.repo, "write the document")
        self.box.write(self.repo, "docs/guide.md",
                       "# 說明文件\n\n" + fp_line(self.base, "docs,src") + "\n\n補充一句。\n")
        code, report = self.check("--docs", self.repo / "docs" / "guide.md")
        self.assertEqual(code, 0)
        self.box.write(self.repo, "docs/other.md", "# 另一份文件\n")
        code, report = self.check("--docs", self.repo / "docs" / "guide.md")
        fp = self.only_fp(report)
        self.assertEqual(code, 1)
        self.assertEqual(fp["uncommitted"]["untracked"],
                         [{"status": "??", "path": "docs/other.md", "old_path": None}])

    def test_unmerged_conflict(self):
        self.doc(fp_line(self.base, "src/model.py"))
        self.box.git(self.repo, "checkout", "-q", "-b", "side")
        self.box.write(self.repo, "src/model.py", "def predict():\n    return 'side'\n")
        self.box.commit(self.repo, "side")
        self.box.git(self.repo, "checkout", "-q", "main")
        self.box.write(self.repo, "src/model.py", "def predict():\n    return 'main'\n")
        self.box.commit(self.repo, "main")
        self.box.git(self.repo, "-c", "user.name=t", "-c", "user.email=t@example.invalid",
                     "merge", "-q", "side", check=False)
        code, report = self.check("--docs", self.repo / "docs")
        fp = self.only_fp(report)
        self.assertEqual(code, 1)
        self.assertIn({"status": "U", "path": "src/model.py", "old_path": None},
                      fp["uncommitted"]["unstaged"])


class ErrorTests(DriftTestCase):
    def test_unknown_repo_name(self):
        self.doc(fp_line(self.base, "src", repo="stock"))
        code, report = self.check("--docs", self.repo / "docs")
        fp = self.only_fp(report)
        self.assertEqual(code, 2)
        self.assertEqual(fp["status"], "error")
        self.assertIn("--repo stock=", fp["reason"])

    def test_unknown_commit(self):
        self.doc(fp_line("1234567", "src"))
        code, report = self.check("--docs", self.repo / "docs")
        fp = self.only_fp(report)
        self.assertEqual(code, 2)
        self.assertIn("無法對應到唯一的 commit", fp["reason"])
        self.assertIn("淺層 clone", fp["reason"])
        self.assertIn("不是淺層 clone", fp["reason"])

    def test_commit_missing_from_shallow_clone(self):
        self.box.write(self.repo, "src/model.py", "def predict():\n    return 5\n")
        self.box.commit(self.repo, "second")
        shallow = self.box.root / "shallow"
        subprocess.run(["git", "clone", "-q", "--depth", "1", self.repo.as_uri(), str(shallow)],
                       env=self.box.env, check=True)
        self.doc(fp_line(self.base, "src", repo="clone"), base=self.box.root / "index")
        code, report = self.check("--docs", self.box.root / "index",
                                  "--repo", f"clone={shallow}")
        fp = self.only_fp(report)
        self.assertEqual(code, 2)
        self.assertIn("這個儲存庫是淺層 clone", fp["reason"])

    def test_mistyped_path(self):
        self.doc(fp_line(self.base, "src/modle.py,config"))
        code, report = self.check("--docs", self.repo / "docs")
        fp = self.only_fp(report)
        self.assertEqual(code, 2)
        self.assertIn("都不存在", fp["reason"])
        self.assertIn("src/modle.py", fp["reason"])
        self.assertNotIn("config", fp["reason"].split("：", 1)[1])

    def test_paths_are_case_sensitive(self):
        self.doc(fp_line(self.base, "SRC/model.py"))
        code, report = self.check("--docs", self.repo / "docs")
        self.assertEqual(code, 2)
        self.assertIn("SRC/model.py", self.only_fp(report)["reason"])

    def test_usage_error_and_internal_error_exit_2(self):
        proc = self.box.run("--no-such-option")
        self.assertEqual(proc.returncode, 2)
        self.assertEqual(proc.stdout, b"")
        self.doc(fp_line(self.base, "src"))
        code = ("import json, runpy, sys\n"
                "def boom(*args, **kwargs):\n"
                "    raise RuntimeError('boom')\n"
                "json.dumps = boom\n"
                "sys.argv = [sys.argv[1], '--json', '--docs', sys.argv[2]]\n"
                "runpy.run_path(sys.argv[0], run_name='__main__')\n")
        env = dict(self.box.env, LC_ALL="C", LANG="C")
        env.pop("PYTHONUTF8", None)
        env.pop("PYTHONIOENCODING", None)
        proc = subprocess.run([sys.executable, "-B", "-X", "utf8=0", "-c", code, str(SCRIPT),
                               str(self.repo / "docs")], env=env,
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.assertEqual(proc.returncode, 2)
        self.assertIn("內部錯誤", proc.stderr.decode("utf-8"))
        self.assertIn("RuntimeError: boom", proc.stderr.decode("utf-8"))

    def test_path_that_exists_only_uncommitted(self):
        self.doc(fp_line(self.base, "src/brand_new.py"))
        self.box.write(self.repo, "src/brand_new.py", "C = 3\n")
        code, report = self.check("--docs", self.repo / "docs")
        fp = self.only_fp(report)
        self.assertEqual(code, 2)
        self.assertIn("只出現在未提交的變更", fp["reason"])

    def test_malformed_fingerprint_reports_line_number(self):
        self.doc(fp_line(self.base, "src"), "",
                 f"<!-- doc-fingerprint: repo=. paths=src commit={self.base} -->")
        code, report = self.check("--docs", self.repo / "docs")
        fps = report["documents"][0]["fingerprints"]
        self.assertEqual(code, 2)
        self.assertEqual([fp["status"] for fp in fps], ["current", "error"])
        self.assertEqual(fps[1]["line"], 5)
        self.assertIn("第 5 行", fps[1]["reason"])

    def test_marker_in_prose_outside_a_fence_is_an_error(self):
        self.doc("指紋的標記是 `doc-fingerprint:`，範例要放在程式碼區塊內。")
        code, report = self.check("--docs", self.repo / "docs")
        self.assertEqual(code, 2)
        self.assertEqual(self.only_fp(report)["status"], "error")

    def test_unclosed_fence_hiding_a_fingerprint(self):
        self.doc("```text", fp_line(self.base, "src"))
        code, report = self.check("--docs", self.repo / "docs")
        self.assertEqual(code, 2)
        self.assertIn("沒有結束", report["documents"][0]["error"])
        self.assertEqual(report["summary"]["document_errors"], 1)

    def test_no_documents_and_missing_docs_path(self):
        empty = self.box.root / "empty"
        empty.mkdir()
        code, report = self.check("--docs", empty)
        self.assertEqual(code, 2)
        self.assertIn("找不到任何 .md", report["run_errors"][0])
        code, report = self.check("--docs", self.box.root / "no-such-folder")
        self.assertEqual(code, 2)
        self.assertIn("不存在", report["run_errors"][0])

    def test_malformed_repo_option_is_a_run_error(self):
        self.doc(fp_line(self.base, "src"))
        code, report = self.check("--docs", self.repo / "docs", "--repo", "stock")
        self.assertEqual(code, 2)
        self.assertIn("--repo 的格式應為 名稱=路徑", report["run_errors"][0])
        self.assertEqual(self.only_fp(report)["status"], "current")

    def test_non_utf8_documents(self):
        marker = fp_line(self.base, "src").encode("ascii")
        self.box.write(self.repo, "docs/guide.md", "# ok\n")
        (self.repo / "docs" / "big5-marked.md").write_bytes("說明".encode("cp950") + b"\n" + marker)
        (self.repo / "docs" / "big5-plain.md").write_bytes("說明".encode("cp950") + b"\n")
        code, report = self.check("--docs", "docs", "--list-unfingerprinted", cwd=self.repo)
        self.assertEqual(code, 2)
        self.assertEqual([(d["path"], d["error"] is not None) for d in report["documents"]],
                         [("docs/big5-marked.md", True)])
        self.assertIn("不是 UTF-8 文字", report["documents"][0]["error"])
        self.assertEqual(report["unfingerprinted"], ["docs/big5-plain.md", "docs/guide.md"])

    def test_utf16_documents_with_marker_are_errors(self):
        text = "# 說明\n\n" + fp_line(self.base, "src") + "\n"
        docs = self.repo / "docs"
        docs.mkdir()
        (docs / "utf16-bom.md").write_bytes(b"\xff\xfe" + text.encode("utf-16-le"))
        (docs / "utf16be-bom.md").write_bytes(b"\xfe\xff" + text.encode("utf-16-be"))
        ascii_only = "# notes\n\n" + fp_line(self.base, "src") + "\n"
        (docs / "utf16-no-bom.md").write_bytes(ascii_only.encode("utf-16-le"))
        (docs / "utf16-plain.md").write_bytes(b"\xff\xfe" + "# 沒有指紋\n".encode("utf-16-le"))
        code, report = self.check("--docs", "docs", "--list-unfingerprinted", cwd=self.repo)
        self.assertEqual(code, 2)
        self.assertEqual([d["path"] for d in report["documents"]],
                         ["docs/utf16-bom.md", "docs/utf16-no-bom.md", "docs/utf16be-bom.md"])
        for doc in report["documents"]:
            self.assertIn("不是 UTF-8 文字", doc["error"])
        self.assertEqual(report["unfingerprinted"], ["docs/utf16-plain.md"])

    def test_mistyped_markers_are_errors_not_skipped(self):
        commit = self.base[:7]
        variants = [
            f"<!-- doc-fingerprint：repo=. commit={commit} paths=src -->",
            f"<!-- DOC-FINGERPRINT: repo=. commit={commit} paths=src -->",
            f"<!-- doc-fingerprint repo=. commit={commit} paths=src -->",
            f"<!-- doc-fingerprint : repo=. commit={commit} paths=src -->",
            f"<!--doc-fingerprint：repo=. commit={commit} paths=src-->",
        ]
        self.doc(*variants, "本文件用 doc-fingerprint 註解記錄核對版本。")
        code, report = self.check("--docs", self.repo / "docs")
        fps = report["documents"][0]["fingerprints"]
        self.assertEqual(code, 2)
        self.assertEqual([(fp["line"], fp["status"]) for fp in fps],
                         [(3, "error"), (4, "error"), (5, "error"), (6, "error"), (7, "error")])
        for fp in fps:
            self.assertIn("格式錯誤", fp["reason"])
        self.assertIn("小寫", fps[0]["reason"])

    def test_git_refusing_a_repository_owned_by_someone_else(self):
        probe = subprocess.run(
            ["git", "-C", str(self.repo), "rev-parse", "--show-toplevel"],
            env=dict(self.box.env, GIT_TEST_ASSUME_DIFFERENT_OWNER="1", LC_ALL="C"),
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if b"dubious ownership" not in probe.stderr:
            self.skipTest("this git cannot simulate a repository owned by another user")
        self.doc(fp_line(self.base, "src"))
        index = self.box.root / "index"
        self.doc(fp_line(self.base, "src", repo="app"), rel="README.md", base=index)
        global_config = Path(self.box.env["GIT_CONFIG_GLOBAL"])
        code, report = self.check("--docs", self.repo / "docs", index, "--repo", f"app={self.repo}",
                                  env_extra={"GIT_TEST_ASSUME_DIFFERENT_OWNER": "1"})
        self.assertEqual(code, 2)
        reasons = [doc["fingerprints"][0]["reason"] for doc in report["documents"]]
        self.assertEqual(len(reasons), 2)
        for reason in reasons:
            self.assertIn("safe.directory", reason)
            self.assertIn("擁有者不是目前的使用者", reason)
            self.assertIn("沒有改動 git 設定", reason)
            self.assertNotIn("git config", reason)
            self.assertNotIn("不在 git 工作目錄內", reason)
        self.assertEqual(global_config.read_bytes(), b"")

    def test_work_tree_problem_messages(self):
        lines = ["fatal: detected dubious ownership in repository at '/r'",
                 "To add an exception for this directory, call:",
                 "git config --global --add safe.directory /r"]
        owned = cdd.GitResult(False, b"", " / ".join(lines), lines)
        message = cdd.work_tree_problem(owned, "文件所在的資料夾")
        self.assertIn("fatal: detected dubious ownership in repository at '/r'", message)
        self.assertNotIn("git config", message)
        missing = cdd.GitResult(False, b"", "找不到 git 可執行檔", launched=False)
        self.assertTrue(cdd.work_tree_problem(missing, "x").startswith("無法執行 git："))
        other = cdd.GitResult(False, b"", "fatal: something else")
        self.assertIn("無法由 git 判斷", cdd.work_tree_problem(other, "x"))

    def test_git_not_installed(self):
        self.doc(fp_line(self.base, "src"))
        empty = self.box.root / "no-programs"
        empty.mkdir()
        code, report = self.check("--docs", self.repo / "docs", env_extra={"PATH": str(empty)})
        reason = self.only_fp(report)["reason"]
        self.assertEqual(code, 2)
        self.assertTrue(reason.startswith("無法執行 git：找不到 git"), reason)

    def test_empty_docs_value_is_a_run_error(self):
        self.doc(fp_line(self.base, "src"))
        code, report = self.check("--docs", "", cwd=self.repo)
        self.assertEqual(code, 2)
        self.assertEqual(report["run_errors"], ["--docs 的值是空的"])
        self.assertEqual(report["summary"]["documents_scanned"], 0)

    def test_unreadable_folder_entry_is_a_run_error(self):
        folder = self.box.root / "locked"
        self.box.write(folder, "inner/n.md", "# n\n")
        self.box.write(folder, "a.md", "# a\n")
        original = Path.is_dir

        def is_dir(path, *args, **kwargs):
            if path.name == "inner":
                raise PermissionError(13, "Permission denied")
            return original(path, *args, **kwargs)

        with mock.patch.object(cdd.Path, "is_dir", is_dir):
            documents, errors = cdd.collect_documents([str(folder)], [])
        self.assertEqual([path.name for path, _ in documents], ["a.md"])
        self.assertEqual(len(errors), 1)
        self.assertIn("無法讀取資料夾", errors[0])
        self.assertIn("Permission denied", errors[0])

    def test_hints_for_full_width_comma_and_extra_keys(self):
        self.doc(f"<!-- doc-fingerprint: repo=. commit={self.base} paths=src，config -->",
                 f"<!-- doc-fingerprint: repo=. commit={self.base} paths=src verified=2026-11-13 x=1 -->")
        code, report = self.check("--docs", self.repo / "docs")
        fps = report["documents"][0]["fingerprints"]
        self.assertEqual(code, 2)
        self.assertIn("半形逗號", fps[0]["reason"])
        self.assertIn("其他鍵", fps[1]["reason"])

    def test_command_line_messages_are_chinese(self):
        proc = self.box.run("--no-such-option")
        stderr = proc.stderr.decode("utf-8")
        self.assertEqual(proc.returncode, 2)
        self.assertEqual(proc.stdout, b"")
        self.assertIn("用法：", stderr)
        self.assertIn("命令列參數錯誤", stderr)
        proc = self.box.run("--help")
        text = proc.stdout.decode("utf-8")
        self.assertEqual(proc.returncode, 0)
        for expected in ("用法：", "顯示這段說明後結束", "結束代碼"):
            self.assertIn(expected, text)
        for english in ("usage:", "options:", "optional arguments:", "show this help"):
            self.assertNotIn(english, text)


class LayoutTests(DriftTestCase):
    def test_several_fingerprints_in_one_document(self):
        self.doc(fp_line(self.base, "config"), "", fp_line(self.base[:12], "src"))
        self.box.write(self.repo, "src/model.py", "def predict():\n    return 6\n")
        self.box.commit(self.repo)
        code, report = self.check("--docs", self.repo / "docs")
        fps = report["documents"][0]["fingerprints"]
        self.assertEqual(code, 1)
        self.assertEqual([(fp["line"], fp["status"]) for fp in fps],
                         [(3, "current"), (5, "drifted")])

    def test_repo_dot_with_document_in_subfolder(self):
        self.doc(fp_line(self.base, "src/model.py"), rel="docs/deep/sub/page.md")
        outside = self.box.root / "elsewhere"
        outside.mkdir()
        code, report = self.check("--docs", self.repo / "docs", cwd=outside)
        self.assertEqual(code, 0)
        self.assertEqual(self.only_fp(report)["repository"], self.repo.resolve().as_posix())
        self.box.write(self.repo, "src/model.py", "def predict():\n    return 7\n")
        self.box.commit(self.repo)
        code, report = self.check("--docs", self.repo / "docs", cwd=outside)
        self.assertEqual(code, 1)

    def test_cross_repository_mapping(self):
        lib = self.box.init_repo("lib")
        self.box.write(lib, "pkg/core.py", "X = 1\n")
        lib_base = self.box.commit(lib, "lib base")
        index = self.box.root / "index"
        self.doc(fp_line(lib_base, "pkg", repo="lib"), fp_line(self.base, "src", repo="app"),
                 rel="README.md", base=index)
        self.box.write(lib, "pkg/core.py", "X = 2\n")
        self.box.commit(lib)
        code, report = self.check("--docs", index, "--repo", f"lib={lib}", f"app={self.repo}")
        fps = report["documents"][0]["fingerprints"]
        self.assertEqual(code, 1)
        self.assertEqual([fp["status"] for fp in fps], ["drifted", "current"])
        self.assertEqual(fps[0]["committed"][0]["path"], "pkg/core.py")

        code, report = self.check("--docs", "index", "--repo", "lib=lib", "app=app",
                                  cwd=self.box.root)
        self.assertEqual(code, 1)

        code, report = self.check("--docs", index, "--repo", f"lib={lib / 'pkg'}",
                                  "--repo", f"app={self.box.root / 'home'}")
        reasons = [fp["reason"] for fp in report["documents"][0]["fingerprints"]]
        self.assertEqual(code, 2)
        self.assertIn("不是儲存庫頂層", reasons[0])
        self.assertIn("不在 git 工作目錄內", reasons[1])

        code, report = self.check("--docs", index, "--repo", f"lib={lib}", f"lib={self.repo}",
                                  f"app={self.repo}")
        self.assertEqual(code, 2)
        self.assertIn("--repo lib 指定了兩個不同的路徑", report["run_errors"])

    def test_repo_dot_outside_any_repository(self):
        index = self.box.root / "index"
        self.doc(fp_line(self.base, "src"), rel="README.md", base=index)
        code, report = self.check("--docs", index)
        self.assertEqual(code, 2)
        self.assertIn("repo=. 需要文件位於 git 工作目錄內", self.only_fp(report)["reason"])

    def test_repo_path_with_equals_sign(self):
        lib = self.box.init_repo("lib=v2")
        self.box.write(lib, "pkg/core.py", "X = 1\n")
        lib_base = self.box.commit(lib, "lib base")
        index = self.box.root / "index"
        self.doc(fp_line(lib_base, "pkg", repo="lib"), rel="README.md", base=index)
        code, report = self.check("--docs", index, "--repo", f"lib={lib}")
        self.assertEqual(code, 0)

    def test_cjk_and_spaced_names(self):
        self.box.write(self.repo, "程式 模組/特徵 工程.py", "F = 1\n")
        self.box.write(self.repo, "設定 檔.json", "{}\n")
        base = self.box.commit(self.repo, "cjk")
        self.doc(fp_line(base, "程式 模組,設定 檔.json"), rel="文件 夾/說明 文件.md")
        self.box.write(self.repo, "程式 模組/特徵 工程.py", "F = 2\n")
        self.box.commit(self.repo)
        self.box.write(self.repo, "程式 模組/新 檔案.py", "G = 1\n")
        code, report = self.check("--docs", self.repo / "文件 夾")
        fp = self.only_fp(report)
        self.assertEqual(code, 1)
        self.assertTrue(report["documents"][0]["path"].endswith("文件 夾/說明 文件.md"))
        self.assertEqual(fp["paths"], ["程式 模組", "設定 檔.json"])
        self.assertEqual(fp["committed"],
                         [{"status": "M", "path": "程式 模組/特徵 工程.py", "old_path": None}])
        self.assertEqual(fp["uncommitted"]["untracked"],
                         [{"status": "??", "path": "程式 模組/新 檔案.py", "old_path": None}])
        text = self.box.run("--docs", self.repo / "文件 夾").stdout.decode("utf-8")
        self.assertIn("M  程式 模組/特徵 工程.py", text)
        self.assertIn("?? 程式 模組/新 檔案.py", text)
        raw_json = self.box.run("--json", "--docs", self.repo / "文件 夾").stdout
        self.assertIn("程式 模組/特徵 工程.py".encode("utf-8"), raw_json)
        self.assertNotIn(b"\\u", raw_json)

    def test_crlf_document_with_bom(self):
        # The fingerprint is on line 1, right after the BOM, so a reader that
        # kept the BOM would report a format error on line 1.
        lines = [fp_line(self.base, "src"), "# 標題", "", "```text",
                 "<!-- doc-fingerprint: repo=NAME commit=SHA paths=P1,P2 -->", "```",
                 fp_line(self.base, "config", verified=None)]
        raw = b"\xef\xbb\xbf" + "\r\n".join(lines).encode("utf-8") + b"\r\n"
        path = self.repo / "docs" / "crlf.md"
        path.parent.mkdir(parents=True)
        path.write_bytes(raw)
        code, report = self.check("--docs", path)
        doc = report["documents"][0]
        fps = doc["fingerprints"]
        self.assertEqual(code, 0)
        self.assertEqual([(fp["line"], fp["status"]) for fp in fps], [(1, "current"), (7, "current")])
        self.assertEqual(doc["fenced_lines"], [5])
        self.assertFalse(fps[0]["text"].endswith("\r"))
        self.assertIsNone(fps[1]["verified"])

    def test_fenced_examples_are_listed_but_not_checked(self):
        self.doc("```markdown", "<!-- doc-fingerprint: repo=NAME commit=SHA paths=P1 -->", "```",
                 "~~~", "<!-- doc-fingerprint: repo=. commit=xyz paths= -->", "~~~",
                 "  ````text", "  <!-- doc-fingerprint: bad -->", "  ````",
                 fp_line(self.base, "src"))
        self.doc("```markdown", fp_line(self.base, "src"), "```", rel="docs/only-example.md")
        code, report = self.check("--docs", self.repo / "docs", "--list-unfingerprinted")
        self.assertEqual(code, 0)
        guide, example = report["documents"]
        self.assertEqual(guide["fenced_lines"], [4, 7, 10])
        self.assertEqual([fp["line"] for fp in guide["fingerprints"]], [12])
        self.assertEqual((example["fingerprints"], example["fenced_lines"]), ([], [4]))
        self.assertEqual(report["unfingerprinted"], [example["path"]])
        self.assertEqual(report["summary"]["fenced_lines"], 4)
        text = self.box.run("--docs", self.repo / "docs").stdout.decode("utf-8")
        self.assertIn("程式碼區塊內的標記行（視為範例，未檢查）：第 4、7、10 行", text)
        self.assertIn("程式碼區塊內的標記行 4 行（視為範例，未檢查）", text.rstrip("\n").split("\n")[-1])

    def test_backslash_paths(self):
        self.doc(fp_line(self.base, "src\\features,config\\settings.json"))
        self.box.write(self.repo, "src/features/a.py", "A = 2\n")
        self.box.commit(self.repo)
        code, report = self.check("--docs", self.repo / "docs")
        fp = self.only_fp(report)
        self.assertEqual(code, 1)
        self.assertEqual(fp["paths"], ["src/features", "config/settings.json"])
        self.assertEqual(fp["committed"][0]["path"], "src/features/a.py")

    def test_exclude_and_list_unfingerprinted(self):
        self.doc(fp_line(self.base, "src"))
        self.doc("<!-- doc-fingerprint: broken -->", rel="docs/archive/old.md")
        self.doc("沒有指紋。", rel="docs/plain.md")
        self.doc("沒有指紋。", rel="docs/notes.markdown")
        code, report = self.check("--docs", self.repo / "docs")
        self.assertEqual(code, 2)
        self.assertIsNone(report["unfingerprinted"])
        code, report = self.check("--docs", "docs", "--exclude", "docs\\archive",
                                  "--list-unfingerprinted", cwd=self.repo)
        self.assertEqual(code, 0)
        self.assertEqual(report["unfingerprinted"], ["docs/notes.markdown", "docs/plain.md"])
        text = self.box.run("--docs", "docs", "--exclude", "archive", "*.markdown",
                            "--list-unfingerprinted", cwd=self.repo).stdout.decode("utf-8")
        self.assertIn("沒有指紋的文件（1 份）：\n  docs/plain.md\n", text)
        code, report = self.check("--docs", "docs", "--exclude", "docs*old.md", cwd=self.repo)
        self.assertEqual(code, 0)
        code, report = self.check("--docs", "docs", "--exclude", "ARCHIVE", cwd=self.repo)
        self.assertEqual(code, 2)

        code, report = self.check("--docs", self.repo / "docs", "--exclude", "archive/*")
        self.assertEqual(code, 0)

    def test_explicit_file_is_read_whatever_its_extension(self):
        path = self.box.write(self.repo, "notes/review.txt", fp_line(self.base, "src") + "\n")
        code, report = self.check("--docs", path)
        self.assertEqual(code, 0)
        self.assertEqual(report["summary"]["fingerprints"], 1)

    def test_default_docs_and_skipped_directories(self):
        scan = self.box.root / "scan"
        for skipped in (".git", ".venv", "venv", "node_modules", "__pycache__"):
            self.doc("<!-- doc-fingerprint: broken -->", rel=f"{skipped}/inside.md", base=scan)
        self.doc(fp_line(self.base, "src", repo="app"), rel="UPPER.MD", base=scan)
        code, report = self.check("--repo", f"app={self.repo}", cwd=scan)
        self.assertEqual(code, 0)
        self.assertEqual([d["path"] for d in report["documents"]], ["UPPER.MD"])

    def test_docs_option_forms(self):
        self.doc(fp_line(self.base, "config"), rel="docs/b.md")
        self.doc(fp_line(self.base, "src/model.py"), rel="other/c.md")
        self.doc(fp_line(self.base, "notes.txt"), rel="third/d.md")
        code, report = self.check("--docs", "docs/b.md", "other", "--docs", "third",
                                  cwd=self.repo)
        self.assertEqual(code, 0)
        self.assertEqual([d["path"] for d in report["documents"]],
                         ["docs/b.md", "other/c.md", "third/d.md"])

    def test_documents_without_fingerprints_exit_zero(self):
        self.doc("只有文字。")
        proc = self.box.run("--docs", self.repo / "docs")
        text = proc.stdout.decode("utf-8")
        self.assertEqual(proc.returncode, 0)
        self.assertIn("沒有找到任何指紋，未比對任何文件", text)


class OutputTests(DriftTestCase):
    def test_json_output_is_valid_with_stable_keys(self):
        self.doc(fp_line(self.base, "src"), "<!-- doc-fingerprint: repo=. commit=zz paths=a -->")
        self.doc("沒有指紋。", rel="docs/plain.md")
        self.box.write(self.repo, "src/model.py", "def predict():\n    return 8\n")
        proc = self.box.run("--json", "--list-unfingerprinted", "--docs", self.repo / "docs")
        report = json.loads(proc.stdout.decode("utf-8"))
        self.assertEqual(proc.stderr, b"")
        self.assertEqual(list(report), TOP_KEYS)
        self.assertEqual(list(report["summary"]), SUMMARY_KEYS)
        doc = report["documents"][0]
        self.assertEqual(list(doc), DOC_KEYS)
        for fp in doc["fingerprints"]:
            self.assertEqual(list(fp), FP_KEYS)
            self.assertEqual(list(fp["uncommitted"]), PENDING_KEYS)
        changed = doc["fingerprints"][0]["uncommitted"]["unstaged"][0]
        self.assertEqual(list(changed), CHANGE_KEYS)
        self.assertEqual(report["tool"], "doc-drift-check")
        self.assertEqual(report["format_version"], 1)
        self.assertEqual(report["summary"]["fingerprints"], 2)
        self.assertEqual(report["unfingerprinted"],
                         [(self.repo / "docs" / "plain.md").as_posix()])
        malformed = doc["fingerprints"][1]
        self.assertIn("格式錯誤", malformed["reason"])
        self.assertEqual([malformed[k] for k in ("repo", "commit", "paths", "verified")],
                         [None, None, [], None])

    def test_exit_codes_and_summary_line(self):
        self.doc(fp_line(self.base, "src"))
        for expected in (0, 1, 2):
            if expected == 1:
                self.box.write(self.repo, "src/model.py", "def predict():\n    return 9\n")
            if expected == 2:
                self.doc(fp_line(self.base, "src", repo="missing"), rel="docs/second.md")
            proc = self.box.run("--docs", self.repo / "docs")
            last = proc.stdout.decode("utf-8").rstrip("\n").split("\n")[-1]
            self.assertEqual(proc.returncode, expected)
            self.assertTrue(last.startswith("摘要："), last)
            self.assertTrue(last.endswith(f"結束代碼 {expected}。"), last)

    def test_child_process_with_non_utf8_default_encoding(self):
        probe = subprocess.run(
            [sys.executable, "-X", "utf8=0", "-c",
             "import locale; print(locale.getpreferredencoding(False))"],
            env=dict(self.box.env, LC_ALL="C", LANG="C"), stdout=subprocess.PIPE)
        encoding = probe.stdout.decode("ascii", "replace").strip().lower().replace("-", "")
        if encoding in ("utf8", "cp65001"):
            self.skipTest("cannot imitate a non-UTF-8 default encoding on this system")
        self.box.write(self.repo, "程式 模組/特徵 工程.py", "F = 1\n")
        base = self.box.commit(self.repo, "cjk")
        self.doc(fp_line(base, "程式 模組"), rel="文件 夾/說明 文件.md")
        self.box.write(self.repo, "程式 模組/特徵 工程.py", "F = 2\n")
        kwargs = dict(env_extra={"LC_ALL": "C", "LANG": "C"},
                      env_drop=("PYTHONUTF8", "PYTHONIOENCODING"),
                      python_options=("-X", "utf8=0"))
        proc = self.box.run("--docs", self.repo / "文件 夾", **kwargs)
        text = proc.stdout.decode("utf-8")
        self.assertEqual(proc.returncode, 1, text + proc.stderr.decode("utf-8", "replace"))
        self.assertIn("已漂移（drifted）", text)
        self.assertIn("M  程式 模組/特徵 工程.py", text)
        self.assertIn("文件 夾/說明 文件.md", text)
        proc = self.box.run("--json", "--docs", self.repo / "文件 夾", **kwargs)
        report = json.loads(proc.stdout.decode("utf-8"))
        self.assertEqual(report["documents"][0]["fingerprints"][0]["uncommitted"]["unstaged"][0]
                         ["path"], "程式 模組/特徵 工程.py")

    def test_git_location_variables_are_ignored(self):
        lib = self.box.init_repo("lib")
        self.box.write(lib, "pkg/core.py", "X = 1\n")
        self.box.commit(lib, "lib base")
        self.doc(fp_line(self.base, "src"))
        self.box.write(self.repo, "src/model.py", "def predict():\n    return 10\n")
        code, report = self.check("--docs", self.repo / "docs",
                                  env_extra={"GIT_DIR": str(lib / ".git"),
                                             "GIT_WORK_TREE": str(lib)})
        self.assertEqual(code, 1)
        self.assertEqual(self.only_fp(report)["uncommitted"]["unstaged"][0]["path"],
                         "src/model.py")


class SafetyTests(DriftTestCase):
    def test_script_leaves_both_repositories_unchanged(self):
        lib = self.box.init_repo("lib")
        self.box.write(lib, "pkg/core.py", "X = 1\n")
        self.box.write(lib, "pkg/util.py", "Y = 1\n")
        lib_base = self.box.commit(lib, "lib base")
        self.doc(fp_line(self.base, "src,config"), fp_line(lib_base, "pkg", repo="lib"))
        for repo, rel in ((self.repo, "src/model.py"), (lib, "pkg/core.py")):
            self.box.write(repo, rel, "changed = True\n")
        self.box.write(self.repo, "config/settings.json", '{"staged": true}\n')
        self.box.git(self.repo, "add", "config/settings.json")
        self.box.write(lib, "pkg/untracked.py", "Z = 1\n")
        for stale in (self.repo / "src" / "features" / "a.py", lib / "pkg" / "util.py"):
            os.utime(stale, (1500000000, 1500000000))

        def state(repo):
            status = self.box.git(repo, "--no-optional-locks", "status", "--porcelain=v1", "-z",
                                  "--untracked-files=all")
            return snapshot(repo), status

        before = {repo: state(repo) for repo in (self.repo, lib)}
        for extra in ((), ("--json",), ("--list-unfingerprinted",)):
            proc = self.box.run("--docs", self.repo / "docs", "--repo", f"lib={lib}", *extra)
            self.assertEqual(proc.returncode, 1)
        for repo in (self.repo, lib):
            self.assertEqual(state(repo), before[repo])
        # Control: a plain `git status` does rewrite the index here, so the
        # snapshot above would have noticed a write.
        self.box.git(self.repo, "status", "--porcelain")
        self.assertNotEqual(snapshot(self.repo), before[self.repo][0])

    def test_partial_clone_objects_are_not_fetched(self):
        origin = self.box.init_repo("origin")
        self.box.write(origin, "src/a.py", "".join(f"line {n}\n" for n in range(20)))
        first = self.box.commit(origin, "one")
        self.box.git(origin, "mv", "src/a.py", "src/b.py")
        self.box.write(origin, "src/b.py", "".join(f"line {n}\n" for n in range(21)))
        self.box.commit(origin, "two")
        self.box.git(origin, "config", "uploadpack.allowfilter", "true")
        partial = self.box.root / "partial"
        subprocess.run(["git", "clone", "-q", "--filter=blob:none", origin.as_uri(), str(partial)],
                       env=self.box.env, check=True)
        index = self.box.root / "index"
        self.doc(fp_line(first, "src", repo="p"), rel="README.md", base=index)
        before = snapshot(partial)
        code, report = self.check("--docs", index, "--repo", f"p={partial}")
        self.assertEqual(code, 2)
        self.assertIn("git diff-tree", self.only_fp(report)["reason"])
        self.assertEqual(snapshot(partial), before)

    def test_shipped_documents_carry_no_fingerprints(self):
        code, report = self.check("--docs", SKILL_DIR)
        self.assertEqual(code, 0)
        self.assertEqual(report["summary"]["fingerprints"], 0)
        self.assertEqual(report["run_errors"], [])
        self.assertGreaterEqual(report["summary"]["documents_scanned"], 3)
        examples = {Path(doc["path"]).name: doc["fenced_lines"] for doc in report["documents"]}
        self.assertTrue(examples.get("fingerprint-format.md"))


class ParsingTests(unittest.TestCase):
    def test_valid_line(self):
        fp = cdd.parse_fingerprint_line(
            "  <!-- doc-fingerprint: repo=stock commit=ABCDEF1 "
            "paths=programs\\single stock\\x.py, config/a.json ,./tests/ verified=2026-11-13 -->")
        self.assertEqual(fp.repo, "stock")
        self.assertEqual(fp.commit, "abcdef1")
        self.assertEqual(fp.paths, ["programs/single stock/x.py", "config/a.json", "tests"])
        self.assertEqual(fp.verified, "2026-11-13")

    def test_malformed_lines(self):
        bad = [
            "<!-- doc-fingerprint: repo=. commit=abc123 paths=a -->",
            "<!-- doc-fingerprint: repo=. commit=" + "a" * 41 + " paths=a -->",
            "<!-- doc-fingerprint: repo=. commit=xyz1234 paths=a -->",
            "<!-- doc-fingerprint: repo=a/b commit=abc1234 paths=a -->",
            "<!-- doc-fingerprint: repo=. commit=abc1234 paths= -->",
            "<!-- doc-fingerprint: repo=. commit=abc1234 paths=a, -->",
            "<!-- doc-fingerprint: repo=. commit=abc1234 paths=/abs/a -->",
            "<!-- doc-fingerprint: repo=. commit=abc1234 paths=C:\\stock\\a.py -->",
            "<!-- doc-fingerprint: repo=. commit=abc1234 paths=..\\other\\a.py -->",
            "<!-- doc-fingerprint: repo=. commit=abc1234 paths=a verified=2026-02-30 -->",
            "<!-- doc-fingerprint: repo=. commit=abc1234 paths=a verified=26-1-1 -->",
            "<!-- doc-fingerprint: commit=abc1234 repo=. paths=a -->",
            "<!-- doc-fingerprint: repo=. commit=abc1234 paths=a",
            "見 <!-- doc-fingerprint: repo=. commit=abc1234 paths=a -->",
            "<!-- doc-fingerprint: repo=. commit=abc1234 paths=a --> "
            "<!-- doc-fingerprint: repo=. commit=abc1234 paths=b -->",
        ]
        for line in bad:
            with self.subTest(line=line):
                with self.assertRaises(cdd.FingerprintError):
                    cdd.parse_fingerprint_line(line)

    def test_normalize_repo_path(self):
        cases = {
            "programs\\single_stock_analysis": "programs/single_stock_analysis",
            ".\\src\\": "src",
            "src//a.py": "src/a.py",
            " 程式 模組/特徵 工程.py ": "程式 模組/特徵 工程.py",
            ".": ".",
            "./": ".",
        }
        for raw, expected in cases.items():
            with self.subTest(raw=raw):
                self.assertEqual(cdd.normalize_repo_path(raw), expected)

    def test_windows_style_repo_option(self):
        self.assertEqual(cdd.parse_repo_option("stock=D:\\stock"), ("stock", "D:\\stock"))
        self.assertEqual(cdd.parse_repo_option("mix=D:\\MIX All"), ("mix", "D:\\MIX All"))
        self.assertEqual(cdd.parse_repo_option("a=C:\\x=y"), ("a", "C:\\x=y"))
        self.assertEqual(cdd.parse_repo_option(" stock = D:\\stock "), ("stock", "D:\\stock"))
        for bad in ("stock", "=D:\\stock", "stock=", ".=D:\\stock", "a/b=D:\\x"):
            with self.subTest(value=bad):
                with self.assertRaises(ValueError):
                    cdd.parse_repo_option(bad)

    def test_credentials_in_git_messages_are_redacted(self):
        message = cdd.clean_message(
            "fatal: unable to access 'https://user:secret@example.invalid/r.git/'\nhint: x\n")
        self.assertNotIn("secret", message)
        self.assertIn("https://***@example.invalid/r.git/", message)


if __name__ == "__main__":
    unittest.main()
