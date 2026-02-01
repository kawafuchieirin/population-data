from fastapi import APIRouter, HTTPException, Query

from .models import (
    AvailableYearsResponse,
    MunicipalityListResponse,
    MunicipalityTimeSeriesResponse,
    PopulationResponse,
)
from .service import estat_service

router = APIRouter(tags=["population"])


@router.get("/population", response_model=PopulationResponse)
async def get_population(
    year: int = Query(..., description="取得する年（例: 2020）", ge=2000, le=2025),
):
    """
    指定年の市区町村別人口データを取得

    - **year**: 取得する年（2000-2025）
    """
    available_years = await estat_service.get_available_years()

    if year not in available_years:
        raise HTTPException(
            status_code=400,
            detail=f"指定された年のデータは利用できません。利用可能な年: {available_years}",
        )

    data = await estat_service.get_population_by_year(year)
    return PopulationResponse(year=year, data=data)


@router.get("/population/years", response_model=AvailableYearsResponse)
async def get_available_years():
    """
    利用可能な年のリストを取得
    """
    years = await estat_service.get_available_years()
    return AvailableYearsResponse(years=years)


@router.get("/municipalities", response_model=MunicipalityListResponse)
async def get_municipalities():
    """
    市区町村一覧を取得
    """
    municipalities = await estat_service.get_municipality_list()
    return MunicipalityListResponse(municipalities=municipalities)


@router.get(
    "/population/municipality/{code}",
    response_model=MunicipalityTimeSeriesResponse,
)
async def get_municipality_time_series(code: str):
    """
    指定市区町村の時系列人口データを取得

    - **code**: 市区町村コード（5桁）
    """
    result = await estat_service.get_municipality_time_series(code)

    if result is None:
        raise HTTPException(
            status_code=404,
            detail=f"市区町村コード {code} のデータが見つかりません",
        )

    prefecture, municipality, data = result
    return MunicipalityTimeSeriesResponse(
        code=code,
        prefecture=prefecture,
        municipality=municipality,
        data=data,
    )
