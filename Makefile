.PHONY: help install install-backend install-frontend dev dev-backend dev-frontend build clean setup-env fetch-data fetch-data-all list-tables generate-data

# デフォルトターゲット
help:
	@echo "利用可能なコマンド:"
	@echo ""
	@echo "  make install          - 全ての依存関係をインストール"
	@echo "  make install-backend  - バックエンドの依存関係をインストール"
	@echo "  make install-frontend - フロントエンドの依存関係をインストール"
	@echo ""
	@echo "  make dev              - バックエンドとフロントエンドを同時起動"
	@echo "  make dev-backend      - バックエンド開発サーバーを起動"
	@echo "  make dev-frontend     - フロントエンド開発サーバーを起動"
	@echo ""
	@echo "  make build            - フロントエンドをビルド"
	@echo "  make clean            - ビルド成果物を削除"
	@echo "  make setup-env        - 環境変数ファイルのテンプレートをコピー"
	@echo ""
	@echo "  make generate-data         - 全国市区町村の人口データを生成（815市区町村）"
	@echo ""
	@echo "  make fetch-data YEAR=2020  - e-Stat APIから指定年のデータを取得"
	@echo "  make fetch-data-all        - e-Stat APIから全年のデータを取得"
	@echo "  make list-tables           - 利用可能な統計表を一覧表示"

# Python仮想環境のパス
VENV = backend/venv
PYTHON = $(VENV)/bin/python
PIP = $(VENV)/bin/pip
UVICORN = $(VENV)/bin/uvicorn

# 全ての依存関係をインストール
install: install-backend install-frontend

# バックエンドセットアップ
install-backend: $(VENV)/bin/activate

$(VENV)/bin/activate: backend/requirements.txt
	python3.12 -m venv $(VENV) || python3 -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -r backend/requirements.txt
	touch $(VENV)/bin/activate

# フロントエンドセットアップ
install-frontend: frontend/node_modules

frontend/node_modules: frontend/package.json
	cd frontend && npm install

# 開発サーバー同時起動（バックグラウンドでバックエンド、フォアグラウンドでフロントエンド）
dev:
	@echo "バックエンドとフロントエンドを起動します..."
	@echo "バックエンド: http://localhost:8000"
	@echo "フロントエンド: http://localhost:5173"
	@echo ""
	@trap 'kill %1 2>/dev/null' EXIT; \
	PYTHONPATH=backend $(UVICORN) app.main:app --reload --port 8000 & \
	cd frontend && npm run dev

# バックエンド開発サーバー
dev-backend: install-backend
	PYTHONPATH=backend $(UVICORN) app.main:app --reload --port 8000

# フロントエンド開発サーバー
dev-frontend: install-frontend
	cd frontend && npm run dev

# フロントエンドビルド
build: install-frontend
	cd frontend && npm run build

# クリーンアップ
clean:
	rm -rf frontend/dist
	rm -rf backend/data/cache/*.json
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true

# 環境変数ファイルのセットアップ
setup-env:
	@if [ ! -f backend/.env ]; then \
		cp backend/.env.example backend/.env; \
		echo "backend/.env を作成しました。APIキーを設定してください。"; \
	else \
		echo "backend/.env は既に存在します。"; \
	fi
	@if [ ! -f frontend/.env ]; then \
		cp frontend/.env.example frontend/.env; \
		echo "frontend/.env を作成しました。APIキーを設定してください。"; \
	else \
		echo "frontend/.env は既に存在します。"; \
	fi

# e-Stat APIから指定年のデータを取得
fetch-data: install-backend
ifndef YEAR
	@echo "使用方法: make fetch-data YEAR=2020"
	@echo "利用可能な年: 2000, 2005, 2010, 2015, 2020"
else
	$(PYTHON) backend/scripts/fetch_estat_data.py --year $(YEAR)
endif

# e-Stat APIから全年のデータを取得
fetch-data-all: install-backend
	$(PYTHON) backend/scripts/fetch_estat_data.py --all

# 利用可能な統計表を一覧表示
list-tables: install-backend
	$(PYTHON) backend/scripts/fetch_estat_data.py --list-tables

# 全国市区町村の人口データを生成（2020年国勢調査ベース）
generate-data: install-backend
	$(PYTHON) backend/scripts/generate_full_data.py --all
