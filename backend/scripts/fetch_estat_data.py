#!/usr/bin/env python3
"""
e-Stat APIから国勢調査の人口データを取得するスクリプト

使用方法:
    python scripts/fetch_estat_data.py --year 2020
    python scripts/fetch_estat_data.py --list-tables
    python scripts/fetch_estat_data.py --all

必要な環境変数:
    ESTAT_APP_ID: e-Stat APIのアプリケーションID
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path

import httpx
from dotenv import load_dotenv

# プロジェクトルートを基準にパスを設定
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
DATA_DIR = PROJECT_ROOT / "data"
CACHE_DIR = DATA_DIR / "cache"

load_dotenv(PROJECT_ROOT / ".env")

ESTAT_APP_ID = os.getenv("ESTAT_APP_ID", "")
ESTAT_API_BASE = "https://api.e-stat.go.jp/rest/3.0/app/json"

# 国勢調査の統計表ID（人口総数・市区町村別）
# 実際のe-Stat統計表IDを使用
CENSUS_STATS = {
    2020: {
        "stats_data_id": "0003448237",  # 令和2年国勢調査 人口等基本集計 全国結果
        "description": "令和2年国勢調査",
    },
    2015: {
        "stats_data_id": "0003149105",  # 平成27年国勢調査
        "description": "平成27年国勢調査",
    },
    2010: {
        "stats_data_id": "0003037985",  # 平成22年国勢調査
        "description": "平成22年国勢調査",
    },
    2005: {
        "stats_data_id": "0003004051",  # 平成17年国勢調査
        "description": "平成17年国勢調査",
    },
    2000: {
        "stats_data_id": "0003004005",  # 平成12年国勢調査
        "description": "平成12年国勢調査",
    },
}


def check_app_id():
    """APIキーの確認"""
    if not ESTAT_APP_ID:
        print("エラー: ESTAT_APP_ID が設定されていません。")
        print("")
        print("設定方法:")
        print("  1. https://www.e-stat.go.jp/api/ でユーザー登録")
        print("  2. アプリケーションIDを取得")
        print("  3. backend/.env ファイルに以下を追加:")
        print("     ESTAT_APP_ID=your_app_id_here")
        sys.exit(1)


def search_census_tables(keyword: str = "国勢調査") -> list:
    """国勢調査関連の統計表を検索"""
    check_app_id()

    params = {
        "appId": ESTAT_APP_ID,
        "searchWord": keyword,
        "surveyYears": "2020",
        "limit": 100,
    }

    print(f"統計表を検索中: {keyword}")

    with httpx.Client(timeout=60.0) as client:
        response = client.get(f"{ESTAT_API_BASE}/getStatsList", params=params)
        response.raise_for_status()
        data = response.json()

    if "GET_STATS_LIST" not in data:
        print("統計表が見つかりませんでした")
        return []

    result = data["GET_STATS_LIST"].get("DATALIST_INF", {})
    tables = result.get("TABLE_INF", [])

    if isinstance(tables, dict):
        tables = [tables]

    return tables


def list_available_tables():
    """利用可能な統計表を一覧表示"""
    tables = search_census_tables("国勢調査 人口")

    print(f"\n見つかった統計表: {len(tables)}件\n")
    print("-" * 80)

    for table in tables[:20]:  # 最初の20件を表示
        stat_id = table.get("@id", "N/A")
        title = table.get("TITLE", {})
        if isinstance(title, dict):
            title_text = title.get("$", "N/A")
        else:
            title_text = str(title)

        survey_date = table.get("SURVEY_DATE", "N/A")
        stat_name = table.get("STAT_NAME", {}).get("$", "N/A")

        print(f"ID: {stat_id}")
        print(f"  統計名: {stat_name}")
        print(f"  表題: {title_text[:60]}...")
        print(f"  調査年月: {survey_date}")
        print("-" * 80)


def fetch_population_data(year: int) -> list:
    """指定年の人口データを取得"""
    check_app_id()

    if year not in CENSUS_STATS:
        print(f"エラー: {year}年のデータは利用できません")
        print(f"利用可能な年: {list(CENSUS_STATS.keys())}")
        return []

    stats_info = CENSUS_STATS[year]
    stats_data_id = stats_info["stats_data_id"]

    print(f"{stats_info['description']}のデータを取得中...")
    print(f"統計表ID: {stats_data_id}")

    params = {
        "appId": ESTAT_APP_ID,
        "statsDataId": stats_data_id,
        "metaGetFlg": "Y",
        "cntGetFlg": "N",
        "sectionHeaderFlg": "1",
    }

    with httpx.Client(timeout=120.0) as client:
        # まずメタ情報を取得
        print("メタ情報を取得中...")
        response = client.get(f"{ESTAT_API_BASE}/getMetaInfo", params=params)
        response.raise_for_status()
        meta_data = response.json()

        # メタ情報から分類情報を解析
        class_info = parse_meta_info(meta_data)

        # 統計データを取得（人口総数のみ）
        print("統計データを取得中...")
        data_params = {
            "appId": ESTAT_APP_ID,
            "statsDataId": stats_data_id,
            "limit": 100000,
        }

        # 人口総数のカテゴリコードがあれば絞り込み
        if class_info.get("population_code"):
            data_params["cdCat01"] = class_info["population_code"]

        response = client.get(f"{ESTAT_API_BASE}/getStatsData", params=data_params)
        response.raise_for_status()
        stats_data = response.json()

    # データをパース
    population_list = parse_stats_data(stats_data, class_info, year)

    return population_list


def parse_meta_info(meta_data: dict) -> dict:
    """メタ情報から分類コード情報を抽出"""
    class_info = {
        "area_codes": {},  # 地域コード -> 地域名
        "population_code": None,  # 人口総数のカテゴリコード
    }

    try:
        meta_inf = meta_data.get("GET_META_INFO", {}).get("METADATA_INF", {})
        class_inf = meta_inf.get("CLASS_INF", {}).get("CLASS_OBJ", [])

        if isinstance(class_inf, dict):
            class_inf = [class_inf]

        for class_obj in class_inf:
            class_id = class_obj.get("@id", "")
            class_objs = class_obj.get("CLASS", [])

            if isinstance(class_objs, dict):
                class_objs = [class_objs]

            # 地域分類
            if "area" in class_id.lower():
                for item in class_objs:
                    code = item.get("@code", "")
                    name = item.get("@name", "")
                    # 5桁の市区町村コードのみ
                    if len(code) == 5 and code.isdigit():
                        class_info["area_codes"][code] = name

            # カテゴリ分類（人口総数を探す）
            if "cat" in class_id.lower():
                for item in class_objs:
                    name = item.get("@name", "")
                    if "人口総数" in name or name == "総数":
                        class_info["population_code"] = item.get("@code", "")
                        break

    except Exception as e:
        print(f"メタ情報の解析中にエラー: {e}")

    print(f"地域コード数: {len(class_info['area_codes'])}")
    return class_info


def parse_stats_data(stats_data: dict, class_info: dict, year: int) -> list:
    """統計データをパースして人口データリストを作成"""
    population_list = []

    try:
        data_inf = stats_data.get("GET_STATS_DATA", {}).get("STATISTICAL_DATA", {})
        data_obj = data_inf.get("DATA_INF", {}).get("VALUE", [])

        if isinstance(data_obj, dict):
            data_obj = [data_obj]

        print(f"データ件数: {len(data_obj)}")

        # 地域コードごとに人口を集計
        area_population = {}

        for item in data_obj:
            area_code = item.get("@area", "")
            value = item.get("$", "")

            # 5桁の市区町村コードのみ処理
            if len(area_code) != 5 or not area_code.isdigit():
                continue

            # 数値変換
            try:
                population = int(value.replace(",", ""))
            except (ValueError, AttributeError):
                continue

            # 最初の値または大きい方を採用（人口総数を取得するため）
            if area_code not in area_population:
                area_population[area_code] = population

        # 都道府県名と市区町村名を分離
        for code, population in area_population.items():
            area_name = class_info["area_codes"].get(code, "")
            prefecture, municipality = split_area_name(code, area_name)

            population_list.append({
                "code": code,
                "prefecture": prefecture,
                "municipality": municipality,
                "population": population,
            })

    except Exception as e:
        print(f"統計データの解析中にエラー: {e}")

    print(f"市区町村データ数: {len(population_list)}")
    return population_list


def split_area_name(code: str, area_name: str) -> tuple:
    """地域名を都道府県名と市区町村名に分割"""
    # 都道府県コード（最初の2桁）
    pref_code = code[:2]

    prefectures = {
        "01": "北海道", "02": "青森県", "03": "岩手県", "04": "宮城県",
        "05": "秋田県", "06": "山形県", "07": "福島県", "08": "茨城県",
        "09": "栃木県", "10": "群馬県", "11": "埼玉県", "12": "千葉県",
        "13": "東京都", "14": "神奈川県", "15": "新潟県", "16": "富山県",
        "17": "石川県", "18": "福井県", "19": "山梨県", "20": "長野県",
        "21": "岐阜県", "22": "静岡県", "23": "愛知県", "24": "三重県",
        "25": "滋賀県", "26": "京都府", "27": "大阪府", "28": "兵庫県",
        "29": "奈良県", "30": "和歌山県", "31": "鳥取県", "32": "島根県",
        "33": "岡山県", "34": "広島県", "35": "山口県", "36": "徳島県",
        "37": "香川県", "38": "愛媛県", "39": "高知県", "40": "福岡県",
        "41": "佐賀県", "42": "長崎県", "43": "熊本県", "44": "大分県",
        "45": "宮崎県", "46": "鹿児島県", "47": "沖縄県",
    }

    prefecture = prefectures.get(pref_code, "")

    # 都道府県名を除去して市区町村名を取得
    municipality = area_name
    if prefecture and area_name.startswith(prefecture):
        municipality = area_name[len(prefecture):]

    return prefecture, municipality


def save_to_cache(year: int, data: list):
    """データをキャッシュファイルに保存"""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_file = CACHE_DIR / f"population_{year}.json"

    with open(cache_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"保存完了: {cache_file}")


def fetch_all_years():
    """全ての年のデータを取得"""
    for year in sorted(CENSUS_STATS.keys(), reverse=True):
        print(f"\n{'='*60}")
        print(f"{year}年のデータを取得")
        print("=" * 60)

        data = fetch_population_data(year)
        if data:
            save_to_cache(year, data)

        # API制限対策で少し待機
        time.sleep(2)


def main():
    parser = argparse.ArgumentParser(
        description="e-Stat APIから国勢調査の人口データを取得"
    )
    parser.add_argument(
        "--year", type=int, help="取得する年（2000, 2005, 2010, 2015, 2020）"
    )
    parser.add_argument(
        "--all", action="store_true", help="全ての年のデータを取得"
    )
    parser.add_argument(
        "--list-tables", action="store_true", help="利用可能な統計表を一覧表示"
    )
    parser.add_argument(
        "--search", type=str, help="統計表を検索"
    )

    args = parser.parse_args()

    if args.list_tables:
        list_available_tables()
    elif args.search:
        tables = search_census_tables(args.search)
        print(f"\n見つかった統計表: {len(tables)}件")
        for table in tables[:10]:
            print(f"  ID: {table.get('@id')} - {table.get('TITLE', {}).get('$', '')[:50]}")
    elif args.all:
        fetch_all_years()
    elif args.year:
        data = fetch_population_data(args.year)
        if data:
            save_to_cache(args.year, data)
    else:
        parser.print_help()
        print("\n利用可能な年:")
        for year, info in sorted(CENSUS_STATS.items(), reverse=True):
            print(f"  {year}: {info['description']}")


if __name__ == "__main__":
    main()
