# 📊 簡報製作

[← 回總覽](../README.md)

### `ppt-master`

> **用途：用 AI 生成可直接編輯的 PPTX 簡報。** 可從文件或主題產生投影片，也能重建頁面視覺、建立可重用的品牌／風格／版型／簡報工作區、填入原生 PPTX 範本、美化既有簡報；還能為簡報加入旁白或動畫，或做成由簡報產生的旁白自動播放影片。

- 適用：建立、重建、重新設計、套範本、美化 PPT／PPTX 或課件；為簡報加旁白、動畫，或輸出旁白自動播放影片
- 版本：`6.8.0`（commit `5e8856b`，對應上游標籤 `v6.8.0`）
- 來源：本帳號 [week833/ppt-master/skills/ppt-master](https://github.com/week833/ppt-master/tree/main/skills/ppt-master)（入口 `SKILL.md`），型態為 Fork，沒有自有修改；2026-10-30 查核時 `main` 與 `v6` 兩個分支都和上游 `main` 相同
- 上游：[hugohe3/ppt-master/skills/ppt-master](https://github.com/hugohe3/ppt-master/tree/main/skills/ppt-master)。上游只有 `main` 分支，`v6` 是本帳號 Fork 自己的分支
- 大小：Skill 資料夾 13,051 個檔案、約 37.7 MiB；其中範本 12,450 個檔案、約 24.4 MiB（21 個品牌、2 套簡報、7 種版型、14 種風格、圖表與表格 SVG、5 套圖示庫、3 個音效包），不建議完整 checkout
- 安裝注意：用 `.claude-plugin/marketplace.json` 安裝時會從上游 hugohe3/ppt-master 取得，不是從本帳號 Fork；Python 後處理腳本需要先在安裝目錄執行 `pip install -r requirements.txt`
