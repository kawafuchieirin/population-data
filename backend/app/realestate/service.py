import gzip
import json
from pathlib import Path

import httpx

from app.config import settings
from .models import RealEstateSummary, RealEstateTransaction

REINFOLIB_API_BASE = "https://www.reinfolib.mlit.go.jp/ex-api/external"

# キャッシュディレクトリ
CACHE_DIR = Path(__file__).parent.parent.parent / "data" / "cache" / "realestate"


class RealEstateService:
    """不動産価格情報取得サービス"""

    def __init__(self):
        self.client = httpx.AsyncClient(timeout=120.0)
        CACHE_DIR.mkdir(parents=True, exist_ok=True)

    @property
    def api_key(self) -> str:
        return settings.REINFOLIB_API_KEY

    async def close(self):
        await self.client.aclose()

    def _get_cache_path(self, year: int, pref_code: str, city_code: str | None) -> Path:
        if city_code:
            return CACHE_DIR / f"realestate_{year}_{pref_code}_{city_code}.json"
        return CACHE_DIR / f"realestate_{year}_{pref_code}.json"

    def _load_cache(
        self, year: int, pref_code: str, city_code: str | None
    ) -> list[RealEstateTransaction] | None:
        cache_path = self._get_cache_path(year, pref_code, city_code)
        if cache_path.exists():
            with open(cache_path, encoding="utf-8") as f:
                data = json.load(f)
                return [RealEstateTransaction(**item) for item in data]
        return None

    def _save_cache(
        self,
        year: int,
        pref_code: str,
        city_code: str | None,
        data: list[RealEstateTransaction],
    ):
        cache_path = self._get_cache_path(year, pref_code, city_code)
        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump([item.model_dump() for item in data], f, ensure_ascii=False)

    async def fetch_transactions(
        self,
        year: int,
        pref_code: str,
        city_code: str | None = None,
        price_classification: str | None = None,
    ) -> list[RealEstateTransaction]:
        """不動産取引データを取得"""
        # キャッシュを確認
        cached = self._load_cache(year, pref_code, city_code)
        if cached:
            return cached

        # APIキーがない場合はサンプルデータを返す
        if not self.api_key:
            return self._get_sample_data(year, pref_code, city_code)

        try:
            data = await self._fetch_from_api(year, pref_code, city_code, price_classification)
            if data:
                self._save_cache(year, pref_code, city_code, data)
                return data
        except Exception as e:
            print(f"ReinfoLib API error: {e}")

        return self._get_sample_data(year, pref_code, city_code)

    async def _fetch_from_api(
        self,
        year: int,
        pref_code: str,
        city_code: str | None,
        price_classification: str | None,
    ) -> list[RealEstateTransaction]:
        """APIからデータを取得"""
        params = {
            "year": str(year),
            "area": pref_code,
        }
        if city_code:
            params["city"] = city_code
        if price_classification:
            params["priceClassification"] = price_classification

        headers = {
            "Ocp-Apim-Subscription-Key": self.api_key,
            "Accept-Encoding": "gzip",
        }

        response = await self.client.get(
            f"{REINFOLIB_API_BASE}/XIT001",
            params=params,
            headers=headers,
        )
        response.raise_for_status()

        # gzip圧縮されている場合はデコード
        content = response.content
        if response.headers.get("Content-Encoding") == "gzip":
            try:
                content = gzip.decompress(content)
            except gzip.BadGzipFile:
                pass  # 既に解凍済みの場合はそのまま使用

        data = json.loads(content)
        return self._parse_api_response(data)

    def _parse_api_response(self, data: dict) -> list[RealEstateTransaction]:
        """APIレスポンスをパース"""
        transactions = []

        # APIレスポンス構造に応じてパース
        items = data.get("data", data.get("Data", []))
        if isinstance(items, dict):
            items = [items]

        for item in items:
            try:
                trade_price = self._parse_int(item.get("TradePrice", item.get("取引価格")))
                area = self._parse_float(item.get("Area", item.get("面積")))

                # 単価を計算（なければ算出）
                unit_price = self._parse_int(item.get("UnitPrice", item.get("単価")))
                if not unit_price and trade_price and area and area > 0:
                    unit_price = int(trade_price / area)

                transactions.append(
                    RealEstateTransaction(
                        trade_price=trade_price,
                        unit_price=unit_price,
                        area=area,
                        prefecture=item.get("Prefecture", item.get("都道府県名", "")),
                        municipality=item.get("Municipality", item.get("市区町村名", "")),
                        district=item.get("DistrictName", item.get("地区名")),
                        trade_date=item.get("Period", item.get("取引時期")),
                        building_year=item.get("BuildingYear", item.get("建築年")),
                        structure=item.get("Structure", item.get("構造")),
                        use=item.get("Use", item.get("用途")),
                        city_planning=item.get("CityPlanning", item.get("都市計画")),
                        price_classification=item.get("PriceClassification", item.get("価格区分")),
                    )
                )
            except Exception as e:
                print(f"Parse error: {e}")
                continue

        return transactions

    def _parse_int(self, value) -> int | None:
        if value is None:
            return None
        if isinstance(value, int):
            return value
        if isinstance(value, str):
            try:
                return int(value.replace(",", ""))
            except ValueError:
                return None
        return None

    def _parse_float(self, value) -> float | None:
        if value is None:
            return None
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            try:
                return float(value.replace(",", ""))
            except ValueError:
                return None
        return None

    def _get_sample_data(
        self, year: int, pref_code: str, city_code: str | None
    ) -> list[RealEstateTransaction]:
        """サンプルデータを返す（APIキー未設定時）"""
        # 都道府県コードに応じたサンプルデータ
        prefectures = {
            "13": "東京都",
            "14": "神奈川県",
            "27": "大阪府",
            "23": "愛知県",
            "01": "北海道",
        }
        pref_name = prefectures.get(pref_code, "東京都")

        # 基準単価（円/㎡）- 都道府県と年による変動
        base_prices = {
            "13": 800000,  # 東京
            "14": 400000,  # 神奈川
            "27": 350000,  # 大阪
            "23": 250000,  # 愛知
            "01": 100000,  # 北海道
        }
        base_price = base_prices.get(pref_code, 200000)

        # 年による変動（2015年を基準）
        year_factor = 1 + (year - 2015) * 0.03

        # サンプルデータ生成
        import random
        random.seed(hash(f"{year}{pref_code}{city_code}"))

        samples = []
        for i in range(50):
            area = random.uniform(50, 200)
            price_factor = random.uniform(0.7, 1.5)
            unit_price = int(base_price * year_factor * price_factor)
            trade_price = int(unit_price * area)

            samples.append(
                RealEstateTransaction(
                    trade_price=trade_price,
                    unit_price=unit_price,
                    area=round(area, 2),
                    prefecture=pref_name,
                    municipality="サンプル市",
                    district=f"サンプル地区{i % 5 + 1}",
                    trade_date=f"{year}年第{random.randint(1, 4)}四半期",
                    building_year=str(random.randint(1990, year)),
                    structure=random.choice(["RC", "SRC", "木造", "鉄骨造"]),
                    use=random.choice(["住宅", "店舗", "事務所", "共同住宅"]),
                    city_planning=random.choice(["商業地域", "住居地域", "工業地域"]),
                    price_classification="取引価格",
                )
            )

        return samples

    async def get_summary_by_municipalities(
        self, year: int, city_codes: list[str]
    ) -> list[RealEstateSummary]:
        """複数市区町村の不動産価格サマリーを取得"""
        summaries = []

        for code in city_codes:
            pref_code = code[:2]
            transactions = await self.fetch_transactions(year, pref_code, code)

            if not transactions:
                continue

            # 単価のリスト
            unit_prices = [t.unit_price for t in transactions if t.unit_price]
            trade_prices = [t.trade_price for t in transactions if t.trade_price]

            if not unit_prices:
                continue

            summaries.append(
                RealEstateSummary(
                    code=code,
                    prefecture=transactions[0].prefecture,
                    municipality=transactions[0].municipality,
                    year=year,
                    transaction_count=len(transactions),
                    avg_unit_price=int(sum(unit_prices) / len(unit_prices)),
                    avg_trade_price=int(sum(trade_prices) / len(trade_prices)) if trade_prices else None,
                    min_unit_price=min(unit_prices),
                    max_unit_price=max(unit_prices),
                )
            )

        return summaries


# シングルトンインスタンス
realestate_service = RealEstateService()
