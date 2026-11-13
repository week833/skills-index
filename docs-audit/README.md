# 📝 文件維護與查核

[← 回總覽](../README.md)

### `handoff-reader-test`

> **用途：測試交接文件能否讓只看過它的讀者接手。** 主代理先依查證過的來源寫好 5 到 8 題與參考答案，再交給一位不帶對話內容的讀者一次作答；讀者只憑文件回答並照抄依據的原句，找不到就寫「文件沒寫」。比對後把缺口分成缺漏、含糊、矛盾、過期回報，並附建議文字。

- 適用：`docs\HANDOFF.md`、ADR，或寫給下一個工作階段的 README
- 不做：預設唯讀、只提建議；使用者明確要求時才修改文件，而且只寫入查證過的事實。不讀取或輸出 `.ENV`，不執行文件裡寫的指令或「下一步」
- 觸發：只在明確要求時使用（`allow_implicit_invocation: false`）
- ⚠️ 需要子代理：Codex 是否提供不帶對話內容的子代理未能確認；沒有時由使用者另開工作階段擔任讀者，或在報告標示「未做獨立讀者測試」，主代理不得自己作答充當讀者
- ⚠️ 先掃描憑證：交給讀者之前先檢查 token、金鑰、密碼與帶憑證的網址，分不清時當成真的處理，停下來等使用者確認後才繼續
- 驗證狀態：只在 Linux 做過結構與文字檢查；讀者提示詞沒有實際交給子代理跑過，也沒有在 Windows 或 Codex 上執行過
- 來源：本儲存庫 [skills/handoff-reader-test](../skills/handoff-reader-test)（入口 `SKILL.md`；MIT 授權）
- 性質：week833 的原創 Skill。構想來自 [anthropics/skills](https://github.com/anthropics/skills) 的 `doc-coauthoring` 其中的讀者測試階段；該資料夾沒有授權聲明，所以沒有使用它的任何文字，詳見 [NOTICE.md](../skills/handoff-reader-test/NOTICE.md)
