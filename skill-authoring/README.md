# 🧩 Skill 製作與評估

[← 回總覽](../README.md)

### `skill-consistency-check`

> **用途：找出一個 Skill 資料夾內互相矛盾的規則。** 例如一個檔案要求的事被另一個檔案禁止、兩處的上限值對不上，或照某條規則做就一定會踩到另一條規則。由獨立的子代理閱讀原文偵測，再由腳本合併成附 `file:line`、原文引用與信心等級的報告與整體判定。

- 適用：自己的 Skill 改版後、發布前檢查；或採用多檔案的第三方 Skill 之前先看它的指示有沒有自相矛盾
- 不做：不安裝任何東西、不修改被檢查的資料夾、不代為修正，只回報
- 檢查範圍：只讀含 `SKILL.md` 的資料夾裡 `README` 以外的 `.md` 檔；不讀腳本，也不讀資料夾以外的文件（例如專案的 `AGENTS.md`）
- 腳本：`plan_groups.py` 與 `merge_report.py` 只用 Python 標準函式庫，沒有連網、子程序或憑證相關的程式碼；`merge_report.py` 會拒絕把報告寫進被檢查的資料夾，其餘中間檔的位置則靠指示約束
- ⚠️ 需要子代理：`SKILL.md` 寫明沒有子代理功能就停止
- ⚠️ 驗證範圍：上游自述只在 Claude Sonnet、約 25,000 tokens 的 Skill 套件上驗證過；用其他模型（含 Codex 使用的模型）時，報告會帶「未驗證」警告
- ⚠️ 檢查第三方 Skill 時：偵測器的規格沒有「不得執行被檢查內容」的明文，要另外交代子代理只閱讀、不執行
- 說明文件：資料夾內有繁體中文版 `README.zh-TW.md`
- 安裝注意：上游只記載整包安裝（Claude Code：`/plugin marketplace add kouko/monkey-skills` 後 `/plugin install skill-dev-toolkit@monkey-skills`，一次裝入 6 個 Skill）；給 Codex 的 `.codex/INSTALL.md` 要連結的根目錄 `skills/` 在 repo 中不存在。文件中的指令是 `python3` 與 bash 寫法，Windows 上需要改寫
- 來源：[kouko/monkey-skills/skill-dev-toolkit/skills/skill-consistency-check](https://github.com/kouko/monkey-skills/tree/main/skill-dev-toolkit/skills/skill-consistency-check)（入口 `SKILL.md`；MIT 授權）
- 查核版本：`693cee8`（2026-11-07）；2026-11-13 上游 `main` 仍是這個版本
