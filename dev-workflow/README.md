# 🛠️ 開發流程與程式品質

[← 回總覽](../README.md)

## 除錯與完成前驗證（外部上游 obra/superpowers）

以下 2 個 Skill 位於上游 [obra/superpowers](https://github.com/obra/superpowers) 的 `skills/` 目錄，本帳號不存副本，來源一律連到上游。

> ⚠️ **只取這兩個資料夾，不要整包安裝。** 上游只記載整包安裝，會一次裝入全部 15 個 Skill。在 Claude Code 上還會加一個 SessionStart hook，每次開啟工作階段（以及清除、壓縮對話時）就注入 `using-superpowers` 的全文，其中規定「有適用的 Skill 就必須使用」；Codex 版外掛沒有這個 hook，但 15 個 Skill 同樣全部裝入。單獨複製資料夾是上游沒有記載的用法，在 Codex（Windows）上能否自動觸發未能確認。
>
> ⚠️ 上游「使用者指示（含 `AGENTS.md`）優先於 Skill」這一句只寫在 `using-superpowers` 裡，單獨複製這兩個資料夾時不會帶到，需要在自己的 `AGENTS.md` 寫明。

### `systematic-debugging`

> **用途：遇到錯誤、測試失敗或非預期行為時，先找出根因再修。** 分四個階段：調查根因（讀完錯誤訊息、穩定重現、比對近期變更、沿資料流回溯）、比對可運作的範例、一次只驗證一個假設、先做出會失敗的重現再做單一修正。連續三次修正失敗就停下來，和使用者討論架構。

- 適用：驗收或資料檢查失敗、同樣輸入跑出不同結果、橫跨多支程式的錯誤
- 內容：純指示（`SKILL.md` 與 3 份參考文件），另附 1 個 TypeScript 範例與 1 個 bash 腳本；資料夾內沒有網址、連網或憑證相關內容
- ⚠️ 機密：`root-cause-tracing.md` 建議把環境變數一併寫進除錯輸出，主流程也要求在每個元件邊界記錄進出的資料並確認環境設定有傳遞到，而且全篇沒有事後移除診斷碼的步驟；使用時要明訂不得把 token 或含 token 的網址寫進日誌與輸出
- ⚠️ 不要使用 `find-polluter.sh`：它只執行 `npm test` 並忽略失敗，不適用 Python 專案
- ⚠️ 修改範圍：流程會自行加入診斷紀錄與重現用的測試，`defense-in-depth.md` 另外主張在每一層都加上驗證；超出「只改被要求的部分」時以自己的 `AGENTS.md` 為準
- 語言與範例：全英文，範例以 TypeScript／npm／macOS 為主
- 版本：請用 v7.0.2 以後。依上游版本紀錄，v7.0.0 之前的診斷範例會把機密值印進日誌；v7.0.2 之前資料夾內還夾帶 4 份寫成真實情境的壓力測試提示檔
- 來源：[obra/superpowers/skills/systematic-debugging](https://github.com/obra/superpowers/tree/main/skills/systematic-debugging)（入口 `SKILL.md`；MIT 授權）
- 查核版本：`22f0b46`（v7.0.2，2026-11-03）；2026-11-13 上游 `main` 仍是這個版本

### `verification-before-completion`

> **用途：在說「完成、已修正、測試通過」之前，先拿出證據。** 要求代理先找出能證明該說法的指令、當下完整重跑、讀完輸出並確認結束碼，再依實際結果陳述；子代理回報成功時也要自己看差異確認。

- 適用：回報驗收或測試結果、修錯之後、提交或開 PR 之前
- 內容：單一 `SKILL.md`（120 行），沒有腳本與網址，也不引用其他 Skill
- ⚠️ 重跑成本：每次宣稱前都要完整重跑驗證指令，沒有「乾跑」的區分；驗證指令如果會連網抓資料或實際送出訊息，要先在 `AGENTS.md` 指定可以安全重跑的指令
- ⚠️ 回歸測試的紅綠驗證要求「還原修正、確認測試失敗、再恢復修正」，但沒有說明怎麼還原；有未提交的變更時，要避免用會丟失變更的 git 指令
- 語言：全英文，語氣強硬（跳過任一步驟視同說謊）
- 來源：[obra/superpowers/skills/verification-before-completion](https://github.com/obra/superpowers/tree/main/skills/verification-before-completion)（入口 `SKILL.md`；MIT 授權）
- 查核版本：`22f0b46`（v7.0.2，2026-11-03）；2026-11-13 上游 `main` 仍是這個版本
