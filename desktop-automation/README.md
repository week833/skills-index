# 🖥️ Windows 桌面自動化

[← 回總覽](../README.md)

### [windows-local-action-recorder](https://github.com/week833/windows-local-action-recorder)

> **用途：錄製 Windows 本機操作，整理成可讓 AI（Codex）學習的工作流程，並以多重確認安全重播。**

- 型態：工具（非 Skill；repo 內沒有 `SKILL.md`，「學習」步驟由使用者在 Codex 對話中說「學習最新錄製」觸發）
- 安裝位置：`D:\stock\record`
- 需求：Windows 10/11、Python 3.12；安裝器不修改 PATH 或 registry
- 安全預設：只在本機運作、不上傳；畫面錄製與文字擷取預設關閉；重播預設為 dry-run，實際執行需通過核准、指紋確認與目標視窗綁定，`Ctrl+Alt+F12` 可隨時中止
- 限制：測試只使用模擬（fake）的 UIA／輸入後端，作者沒有宣稱已在實機完成驗證
