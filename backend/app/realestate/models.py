from pydantic import BaseModel


class RealEstateTransaction(BaseModel):
    """不動産取引データ"""
    trade_price: int | None = None  # 取引価格
    unit_price: int | None = None  # 単価（円/㎡）
    area: float | None = None  # 面積（㎡）
    prefecture: str  # 都道府県名
    municipality: str  # 市区町村名
    district: str | None = None  # 地区名
    trade_date: str | None = None  # 取引時期
    building_year: str | None = None  # 建築年
    structure: str | None = None  # 構造
    use: str | None = None  # 用途
    city_planning: str | None = None  # 都市計画
    price_classification: str | None = None  # 価格区分（取引/成約）


class RealEstateResponse(BaseModel):
    """不動産価格APIレスポンス"""
    year: int
    prefecture_code: str
    city_code: str | None = None
    total_count: int
    data: list[RealEstateTransaction]


class RealEstateSummary(BaseModel):
    """不動産価格サマリー"""
    code: str  # 市区町村コード
    prefecture: str
    municipality: str
    year: int
    transaction_count: int  # 取引件数
    avg_unit_price: int | None = None  # 平均単価（円/㎡）
    avg_trade_price: int | None = None  # 平均取引価格
    min_unit_price: int | None = None  # 最低単価
    max_unit_price: int | None = None  # 最高単価


class RealEstateSummaryResponse(BaseModel):
    """不動産価格サマリーレスポンス"""
    data: list[RealEstateSummary]
