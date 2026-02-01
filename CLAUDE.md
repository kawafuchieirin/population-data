# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

市区町村レベルの人口データと不動産価格をGoogleマップ上で時系列表示するWebアプリケーション。
- e-Stat APIから国勢調査データを取得
- 不動産情報ライブラリAPIから不動産取引価格を取得
- 人口推移と不動産価格推移を重ねて可視化

## 技術スタック

- **Backend**: Python 3.12+ / FastAPI / httpx
- **Frontend**: React 18 / TypeScript / Vite / Recharts / @react-google-maps/api
- **データソース**:
  - e-Stat API（政府統計総合窓口）
  - 不動産情報ライブラリAPI（国土交通省）

## Development Setup

### クイックスタート

```bash
make install      # 依存関係インストール
make generate-data  # 人口データ生成（815市区町村）
make dev          # 開発サーバー起動
```

### APIキーの設定（推奨）

```bash
# secrets.jsonを作成
cp backend/secrets.json.example backend/secrets.json
# secrets.jsonを編集してAPIキーを設定
```

`backend/secrets.json`:
```json
{
  "estat_app_id": "your_estat_app_id",
  "reinfolib_api_key": "your_reinfolib_api_key",
  "google_maps_api_key": "your_google_maps_api_key"
}
```

### 必要なAPIキー

| API | 用途 | 取得先 |
|-----|------|--------|
| e-Stat | 国勢調査データ | https://www.e-stat.go.jp/api/ |
| 不動産情報ライブラリ | 不動産取引価格 | https://www.reinfolib.mlit.go.jp/ |
| Google Maps | 地図表示 | Google Cloud Console |

※ APIキー未設定時はサンプルデータが表示されます

## Common Commands

```bash
make help           # コマンド一覧
make dev            # バックエンド+フロントエンド起動
make dev-backend    # バックエンドのみ起動 (port 8000)
make dev-frontend   # フロントエンドのみ起動 (port 5173)
make generate-data  # 人口データ生成
make build          # フロントエンドビルド
make clean          # キャッシュ削除
```

### APIエンドポイント

- `GET /api/population?year={year}` - 指定年の人口データ
- `GET /api/population/years` - 利用可能な年リスト
- `GET /api/municipalities` - 市区町村一覧
- `GET /api/population/municipality/{code}` - 市区町村の人口時系列
- `GET /api/realestate/municipality/{code}` - 市区町村の不動産価格時系列
- `GET /api/status` - API設定状態

## プロジェクト構成

```
population-data/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPIエントリーポイント
│   │   ├── config.py            # 設定管理（secrets.json読み込み）
│   │   ├── routers/
│   │   │   ├── population.py    # 人口データAPI
│   │   │   └── realestate.py    # 不動産価格API
│   │   ├── services/
│   │   │   ├── estat.py         # e-Stat API連携
│   │   │   └── realestate.py    # 不動産情報ライブラリAPI連携
│   │   └── models/
│   ├── scripts/                 # データ生成スクリプト
│   ├── data/cache/              # APIレスポンスキャッシュ
│   ├── secrets.json             # APIキー（.gitignore対象）
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Map.tsx          # Googleマップ表示
│   │   │   ├── CombinedChart.tsx # 人口+不動産グラフ
│   │   │   └── TimeSlider.tsx   # 年選択スライダー
│   │   ├── hooks/
│   │   └── App.tsx
│   └── package.json
├── Makefile
├── .gitignore
└── CLAUDE.md
```
