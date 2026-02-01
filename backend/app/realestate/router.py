from fastapi import APIRouter, HTTPException, Query

from .models import RealEstateResponse, RealEstateSummaryResponse
from .service import realestate_service

router = APIRouter(tags=["realestate"])


@router.get("/realestate/transactions", response_model=RealEstateResponse)
async def get_transactions(
    year: int = Query(..., description="取得する年（2005以降）", ge=2005, le=2025),
    pref_code: str = Query(..., description="都道府県コード（2桁）", min_length=2, max_length=2),
    city_code: str | None = Query(None, description="市区町村コード（5桁）", min_length=5, max_length=5),
):
    """
    不動産取引価格データを取得

    - **year**: 取得する年（2005年以降）
    - **pref_code**: 都道府県コード（2桁、例: 13=東京都）
    - **city_code**: 市区町村コード（5桁、オプション）
    """
    transactions = await realestate_service.fetch_transactions(year, pref_code, city_code)

    return RealEstateResponse(
        year=year,
        prefecture_code=pref_code,
        city_code=city_code,
        total_count=len(transactions),
        data=transactions,
    )


@router.get("/realestate/summary", response_model=RealEstateSummaryResponse)
async def get_summary(
    year: int = Query(..., description="取得する年（2005以降）", ge=2005, le=2025),
    city_codes: str = Query(..., description="市区町村コードのカンマ区切り（例: 13101,13102,13103）"),
):
    """
    複数市区町村の不動産価格サマリーを取得

    - **year**: 取得する年
    - **city_codes**: 市区町村コードのカンマ区切り
    """
    codes = [c.strip() for c in city_codes.split(",") if c.strip()]

    if not codes:
        raise HTTPException(status_code=400, detail="市区町村コードを指定してください")

    if len(codes) > 50:
        raise HTTPException(status_code=400, detail="一度に取得できるのは50市区町村までです")

    summaries = await realestate_service.get_summary_by_municipalities(year, codes)

    return RealEstateSummaryResponse(data=summaries)


@router.get("/realestate/municipality/{code}")
async def get_municipality_realestate_timeseries(
    code: str,
    start_year: int = Query(2015, description="開始年", ge=2005),
    end_year: int = Query(2023, description="終了年", le=2025),
):
    """
    指定市区町村の不動産価格時系列データを取得

    - **code**: 市区町村コード（5桁）
    """
    if len(code) != 5:
        raise HTTPException(status_code=400, detail="市区町村コードは5桁で指定してください")

    pref_code = code[:2]
    time_series = []

    for year in range(start_year, end_year + 1):
        transactions = await realestate_service.fetch_transactions(year, pref_code, code)

        if not transactions:
            continue

        unit_prices = [t.unit_price for t in transactions if t.unit_price]

        if unit_prices:
            time_series.append({
                "year": year,
                "transaction_count": len(transactions),
                "avg_unit_price": int(sum(unit_prices) / len(unit_prices)),
                "min_unit_price": min(unit_prices),
                "max_unit_price": max(unit_prices),
            })

    if not time_series:
        raise HTTPException(
            status_code=404,
            detail=f"市区町村コード {code} の不動産データが見つかりません",
        )

    # 最初のデータから市区町村名を取得
    first_transactions = await realestate_service.fetch_transactions(
        time_series[0]["year"], pref_code, code
    )

    return {
        "code": code,
        "prefecture": first_transactions[0].prefecture if first_transactions else "",
        "municipality": first_transactions[0].municipality if first_transactions else "",
        "data": time_series,
    }
