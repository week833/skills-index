# 📊 簡報製作

[← 回總覽](../README.md)

### `ppt-master`

> **用途：用 AI 生成可直接編輯的 PPTX 簡報。** 可從文件或主題產生投影片，也能重建頁面視覺、建立可重用的品牌／風格／版型工作區、填入原生 PPTX 範本，以及美化既有簡報。

- 適用：建立、重建、重新設計、套範本、美化 PPT／PPTX
- 來源：本帳號 [week833/ppt-master/skills/ppt-master](https://github.com/week833/ppt-master/tree/main/skills/ppt-master)（入口 `SKILL.md`），型態為 Fork，沒有自有修改，停在上游 `5.1.0`（2026-08-28）；Fork 的 `v6` 分支內容也是 `5.1.0`
- 最新版：上游 [hugohe3/ppt-master/skills/ppt-master](https://github.com/hugohe3/ppt-master/tree/main/skills/ppt-master)（持續更新，2026-10-21 查核時為 `6.7.2`）
- 大小：Skill 資料夾約 1.3 萬個檔案、約 80 MB（其中範本約 1.2 萬個檔案、約 25 MB），不建議完整 checkout
- 安裝注意：用 `.claude-plugin/marketplace.json` 安裝時會從上游 hugohe3/ppt-master 取得，不是從本帳號 Fork；Python 後處理腳本需要先在安裝目錄執行 `pip install -r requirements.txt`
