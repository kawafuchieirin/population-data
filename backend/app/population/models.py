from pydantic import BaseModel


class MunicipalityPopulation(BaseModel):
    """市区町村の人口データ"""
    code: str  # 市区町村コード（5桁）
    prefecture: str  # 都道府県名
    municipality: str  # 市区町村名
    population: int  # 人口


class PopulationResponse(BaseModel):
    """人口データAPIレスポンス"""
    year: int
    data: list[MunicipalityPopulation]


class AvailableYearsResponse(BaseModel):
    """利用可能な年リストAPIレスポンス"""
    years: list[int]


class YearlyPopulation(BaseModel):
    """年ごとの人口データ"""
    year: int
    population: int


class MunicipalityTimeSeriesResponse(BaseModel):
    """市区町村の時系列人口データレスポンス"""
    code: str
    prefecture: str
    municipality: str
    data: list[YearlyPopulation]


class MunicipalityListItem(BaseModel):
    """市区町村リストの項目"""
    code: str
    prefecture: str
    municipality: str


class MunicipalityListResponse(BaseModel):
    """市区町村リストAPIレスポンス"""
    municipalities: list[MunicipalityListItem]
