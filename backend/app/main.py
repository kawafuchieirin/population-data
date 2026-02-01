from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.population import router as population_router
from app.realestate import router as realestate_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """アプリケーションのライフサイクル管理"""
    # 起動時
    print("\n" + "=" * 50)
    print("人口・不動産データAPI 起動")
    print("=" * 50)
    settings.print_status()
    print("\nAPIキーの設定方法:")
    print("  1. backend/secrets.json.example を backend/secrets.json にコピー")
    print("  2. secrets.json にAPIキーを設定")
    print("=" * 50 + "\n")
    yield
    # 終了時
    print("サーバーを終了します...")


app = FastAPI(
    title="人口・不動産データAPI",
    description="e-Statから取得した市区町村レベルの人口データと不動産価格情報を提供するAPI",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(population_router, prefix="/api")
app.include_router(realestate_router, prefix="/api")


@app.get("/")
async def root():
    return {"message": "人口・不動産データAPI", "docs": "/docs"}


@app.get("/api/status")
async def get_status():
    """API設定状態を取得"""
    return {
        "estat_api": "configured" if settings.ESTAT_APP_ID else "not_configured",
        "reinfolib_api": "configured" if settings.REINFOLIB_API_KEY else "not_configured",
    }
