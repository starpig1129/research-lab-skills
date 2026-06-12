# examples/report-slides — 週報簡報範例

這個目錄展示 `/report-slides` 技能的輸出樣貌。所有投影片都由 [`slide_data_weekly_progress.json`](slide_data_weekly_progress.json) 這個資料檔驅動，對應 `../research-log/` 裡三篇實驗日誌的內容。

## 這是什麼？

這是一份**每週 lab meeting 進度報告**，從實驗日誌自動生成。重點在：

- 這不是論文，這是**中繼匯報**——研究還在進行中
- slide03 的時間線顯示三週的演進，包含兩個 `amended` 修正標記
- 日誌裡的失敗（P7 梯度發散、rubric 截斷、score-boundary confusion）都反映在簡報的「下一步」裡
- 從 `slide_data.json` 到最終簡報，整個流程是資料驅動的，不是手工排版的

## 輸出格式

`/report-slides` 生成以下三種輸出：

### 1. SVG 原始檔（本目錄的 `.svg` 檔案）

每張投影片是一個獨立的 SVG 檔案，可以在任何向量編輯器（Inkscape、Figma、Illustrator）中直接開啟修改。尺寸固定為 1200×675（16:9）。

### 2. PPTX（`deck.pptx`）

**PPTX 的可編輯性是核心功能**。SVG 以原生方式嵌入 PowerPoint，每一個文字、圖形、顏色都可以在 PowerPoint 或 Keynote 裡直接點擊修改，不需要回來改原始碼。

從 SVG 檔案生成 PPTX：

```bash
# 確保已安裝依賴
pip install python-pptx

# 找到 to_pptx.py 路徑（安裝後位於 scripts/ 目錄）
python scripts/to_pptx.py \
  --slides examples/report-slides/slide*.svg \
  --output examples/report-slides/deck.pptx
```

或者直接用 `/report-slides` 技能生成，它會同時輸出 SVG 和 PPTX。

### 3. `slide_data.json`（資料來源）

Path A（Python 資料驅動）投影片的資料定義檔。修改數字或文字後，用 `--slide N` 重新渲染單張投影片：

```bash
python scripts/generate_slides.py \
  --data slide_data_weekly_progress.json \
  --slide 4 \
  --output slide04_bar_chart.svg
```

## 投影片列表

| 檔案 | 類型 | 技術說明 |
|------|------|---------|
| `slide01_title.svg` | Title | 純 SVG，decorative layout |
| `slide02_two_column.svg` | Two-column | 紅/綠 color-coded 卡片 |
| `slide03_timeline.svg` | Timeline | 3-node + `marker-end` 箭頭 + `amended` badges |
| `slide04_bar_chart.svg` | Bar chart | 分組長條圖，`Best Model` badge |
| `slide05_table.svg` | Table | 6-row × 5-col，DIF 顏色標記 |
| `slide06_metric_cards.svg` | Metric cards | 4 張 KPI 卡，amber pending 樣式 |
| `slide07_conclusion.svg` | Conclusion | 結論 + next steps 側邊色條 |
| `slide08_architecture.svg` | **Architecture** | 三層系統架構圖（Data / Model / Evaluation）+ drop shadow + gradient |
| `slide09_flowchart.svg` | **Flowchart** | 研究決策流程圖：菱形決策節點、彩色路徑分支、三欄佈局 |

## 風格規範

所有投影片遵循 `default` 風格調色板：

| 用途 | 顏色 |
|------|------|
| Primary / 標題 | `#1e3a5f` |
| Positive / 達標 | `#059669` |
| Warning / 待定 | `#d97706` |
| Danger / 失敗 | `#dc2626` |
| Muted / 標注 | `#64748b` |

切換風格：

```bash
bash "$(find ~/.claude -path "*/report-slides/scripts/set-style.sh" | head -1)" minimal
```
