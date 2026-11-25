# 遊戲美術與生圖

[返回全部 Skill 索引](../README.md)

製作角色時，先用定稿圖確認造型，再製作多方向或逐格動畫。道具、地形與介面各有不同的交付規格，下表列出每個 Skill 的原作者指令檔與檢查重點。

## 角色立繪與風格一致性

| Skill 與原作者 | 用途 | 使用條件與檢查重點 |
|---|---|---|
| [assetelier](https://github.com/Haruhiyuki/assetelier/blob/main/assetelier/skills/assetelier/SKILL.md) · Haruhiyuki | 沿用角色定稿圖製作表情、姿勢與劇情插畫 | 變體共用定稿參考圖。比對髮型、服裝配色、人物比例與場景光源。 |

## 角色動畫與多方向圖集

| Skill 與原作者 | 用途 | 使用條件與檢查重點 |
|---|---|---|
| [sprite-pipeline](https://github.com/openai/plugins/blob/main/plugins/game-studio/skills/sprite-pipeline/SKILL.md) · openai | 從基準影格製作走路、待機或受擊動畫 | 搭配生圖工具與 Python。以相同畫格與腳底定位點播放整段，檢查角色是否晃動。 |
| [game-character-sprites](https://github.com/tachikomared/character-animation-creator-skill/blob/main/SKILL.md) · tachikomared | 製作四方向或八方向角色動畫圖集 | 逐一製作各動作與方向。逐方向檢查朝向、步態與配件，保留通過的影格。 |
| [spriteforge](https://github.com/luan/spriteforge/blob/main/skills/spriteforge/SKILL.md) · luan | 用同一個 Blender 模型產出多方向角色與物件 | 需要 Blender 與 uv。適合有非對稱裝備的角色。旋轉後確認裝備仍在正確一側。 |

## 像素道具與地圖圖塊

| Skill 與原作者 | 用途 | 使用條件與檢查重點 |
|---|---|---|
| [generating-dot-assets](https://github.com/abagames/agentic-gamedev-skills/blob/main/.agents/skills/generating-dot-assets/SKILL.md) · abagames | 把道具原圖處理成定尺寸、共用色盤的透明 PNG | 需要生圖工具、Node.js 與 ImageMagick。以遊戲實際尺寸檢查輪廓，核對畫布大小、顏色數與透明邊角。 |
| [tileset](https://github.com/melodic-software/claude-code-plugins/blob/main/plugins/pixel-art/skills/tileset/SKILL.md) · melodic-software | 製作可銜接的地形圖塊與自動拼接素材 | 先指定引擎與圖塊格線。以 3×3 重複鋪排檢查接縫，再用小地圖測試轉角。 |

## 遊戲介面與圖示

| Skill 與原作者 | 用途 | 使用條件與檢查重點 |
|---|---|---|
| [layer-game-ui](https://github.com/layerai/skills/blob/main/plugins/layer/skills/layer-game-ui/SKILL.md) · layerai | 製作成套技能圖示、按鈕與九宮格對話框 | 完整流程需使用 Layer。調整對話框寬度時確認四角保有原形，再以背包的實際尺寸比對圖示留白。 |

## 場景背景與視覺特效

| Skill 與原作者 | 用途 | 使用條件與檢查重點 |
|---|---|---|
| [layer-environments](https://github.com/layerai/skills/blob/main/plugins/layer/skills/layer-environments/SKILL.md) · layerai | 將場景拆成可捲動的遠景、中景與前景 | 完整流程需使用 Layer。捲動時檢查各層地平線、接縫與原本被前景遮住的區域。 |
| [layer-vfx](https://github.com/layerai/skills/blob/main/plugins/layer/skills/layer-vfx/SKILL.md) · layerai | 製作光效、煙霧與技能特效序列圖 | 完整流程需使用 Layer。用加法混合預覽光暈，用透明度混合檢查煙霧的半透明邊緣。 |
