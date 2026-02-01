#!/usr/bin/env python3
"""
e-Statから国勢調査の人口データをダウンロードするスクリプト

e-Stat APIを使用せず、統計表ファイルを直接ダウンロードして変換します。

使用方法:
    python scripts/download_census_data.py --year 2020
    python scripts/download_census_data.py --all
"""

import argparse
import csv
import io
import json
import re
import zipfile
from pathlib import Path

import httpx

SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
DATA_DIR = PROJECT_ROOT / "data"
CACHE_DIR = DATA_DIR / "cache"

# 都道府県コード -> 都道府県名
PREFECTURES = {
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

# e-Stat 統計表ダウンロードURL
# 国勢調査 人口等基本集計 全国結果
CENSUS_URLS = {
    2020: {
        "url": "https://www.e-stat.go.jp/stat-search/file-download?statInfId=000032143614&fileKind=1",
        "description": "令和2年国勢調査",
    },
    2015: {
        "url": "https://www.e-stat.go.jp/stat-search/file-download?statInfId=000031524010&fileKind=1",
        "description": "平成27年国勢調査",
    },
}

# 国土数値情報の行政区域データURL（バックアップソース）
KOKUDO_URL = "https://nlftp.mlit.go.jp/ksj/gml/data/N03/N03-2023/N03-20230101_GML.zip"


def download_estat_csv(year: int) -> str | None:
    """e-Statから統計表CSVをダウンロード"""
    if year not in CENSUS_URLS:
        print(f"エラー: {year}年のダウンロードURLが設定されていません")
        return None

    url = CENSUS_URLS[year]["url"]
    print(f"ダウンロード中: {CENSUS_URLS[year]['description']}")
    print(f"URL: {url}")

    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }

    try:
        with httpx.Client(timeout=120.0, follow_redirects=True) as client:
            response = client.get(url, headers=headers)
            response.raise_for_status()

            content_type = response.headers.get("content-type", "")
            print(f"Content-Type: {content_type}")

            if "zip" in content_type or response.content[:4] == b"PK\x03\x04":
                # ZIPファイルの場合
                with zipfile.ZipFile(io.BytesIO(response.content)) as zf:
                    for name in zf.namelist():
                        if name.endswith(".csv"):
                            print(f"CSVファイルを展開: {name}")
                            return zf.read(name).decode("cp932", errors="replace")
            else:
                # CSVファイルの場合
                return response.content.decode("cp932", errors="replace")

    except Exception as e:
        print(f"ダウンロードエラー: {e}")
        return None


def download_population_from_api() -> list:
    """
    公開されている人口データAPIからダウンロード
    RESAS APIやその他のオープンデータを使用
    """
    # ここではフォールバックとして空リストを返す
    return []


def parse_census_csv(csv_content: str, year: int) -> list:
    """国勢調査CSVをパース"""
    population_data = []
    lines = csv_content.split("\n")

    # ヘッダー行を探す
    header_row = -1
    for i, line in enumerate(lines[:20]):
        if "市区町村コード" in line or "団体コード" in line or "地域コード" in line:
            header_row = i
            break

    if header_row == -1:
        # ヘッダーが見つからない場合、数値データが始まる行を探す
        for i, line in enumerate(lines):
            if re.search(r"^\"?\d{5}", line):
                header_row = i - 1 if i > 0 else 0
                break

    print(f"ヘッダー行: {header_row + 1}")

    # CSVパース
    reader = csv.reader(lines[header_row + 1:] if header_row >= 0 else lines)

    for row in reader:
        if len(row) < 3:
            continue

        # 市区町村コード（5桁または6桁）を探す
        code = None
        municipality_name = None
        population = None

        for i, cell in enumerate(row):
            cell = cell.strip().strip('"')

            # 5桁または6桁の市区町村コード
            if re.match(r"^\d{5,6}$", cell):
                code = cell[:5] if len(cell) == 6 else cell

            # 市区町村名（漢字・ひらがな・カタカナを含む）
            elif re.match(r"^[ぁ-んァ-ヶ一-龥々ー]+", cell) and len(cell) >= 2:
                if municipality_name is None:
                    municipality_name = cell

            # 人口値（カンマ区切りの数値）
            elif population is None and re.match(r"^[\d,]+$", cell):
                try:
                    pop = int(cell.replace(",", ""))
                    if pop >= 100:  # 100人以上を人口とみなす
                        population = pop
                except ValueError:
                    pass

        if code and population:
            pref_code = code[:2]
            prefecture = PREFECTURES.get(pref_code, "")

            # 都道府県名を除去
            muni = municipality_name or ""
            if prefecture and muni.startswith(prefecture):
                muni = muni[len(prefecture):]

            population_data.append({
                "code": code,
                "prefecture": prefecture,
                "municipality": muni,
                "population": population,
            })

    # 重複を除去（コードでユニーク化）
    seen = set()
    unique_data = []
    for item in population_data:
        if item["code"] not in seen:
            seen.add(item["code"])
            unique_data.append(item)

    return unique_data


def fetch_ssdse_data(year: int) -> list:
    """
    SSDSE（教育用標準データセット）から人口データを取得
    総務省統計局が提供する教育用データセット
    https://www.nstac.go.jp/use/literacy/ssdse/
    """
    # SSDSEの都道府県別・市区町村別データURL
    ssdse_urls = {
        2020: "https://www.nstac.go.jp/sys/files/SSDSE-2024B.csv",
        2015: "https://www.nstac.go.jp/sys/files/SSDSE-2024B.csv",
    }

    if year not in ssdse_urls:
        return []

    print(f"SSDSE データをダウンロード中...")

    try:
        with httpx.Client(timeout=60.0, follow_redirects=True) as client:
            response = client.get(ssdse_urls[year])
            response.raise_for_status()

            # エンコーディングを試行
            for enc in ["utf-8", "cp932", "shift_jis"]:
                try:
                    content = response.content.decode(enc)
                    break
                except UnicodeDecodeError:
                    continue
            else:
                content = response.content.decode("utf-8", errors="replace")

            return parse_ssdse_csv(content, year)

    except Exception as e:
        print(f"SSDSEダウンロードエラー: {e}")
        return []


def parse_ssdse_csv(csv_content: str, year: int) -> list:
    """SSDSEのCSVをパース"""
    population_data = []
    lines = csv_content.split("\n")

    reader = csv.reader(lines)
    headers = []

    for row in reader:
        if not headers:
            headers = row
            continue

        if len(row) < len(headers):
            continue

        # 市区町村コードと人口を探す
        row_dict = dict(zip(headers, row))

        code = row_dict.get("市区町村コード", row_dict.get("団体コード", ""))
        municipality = row_dict.get("市区町村", row_dict.get("市区町村名", ""))
        prefecture = row_dict.get("都道府県", row_dict.get("都道府県名", ""))

        # 人口列を探す
        population = None
        for key in ["人口総数", "総人口", "人口", f"{year}年人口"]:
            if key in row_dict:
                try:
                    population = int(row_dict[key].replace(",", ""))
                    break
                except (ValueError, AttributeError):
                    pass

        if code and population:
            code = code[:5] if len(code) > 5 else code
            population_data.append({
                "code": code,
                "prefecture": prefecture,
                "municipality": municipality,
                "population": population,
            })

    return population_data


def download_estatdb_data(year: int) -> list:
    """
    e-Stat DBから直接データを取得（API不要のエンドポイント）
    """
    # 国勢調査の統計表ID
    stat_ids = {
        2020: "0003448237",
        2015: "0003149105",
        2010: "0003037985",
    }

    if year not in stat_ids:
        return []

    stat_id = stat_ids[year]
    url = f"https://dashboard.e-stat.go.jp/api/1.0/Json/getData?StatsDataId={stat_id}&MetaGetFlg=Y"

    print(f"e-Stat Dashboard APIからデータ取得中...")

    try:
        with httpx.Client(timeout=120.0) as client:
            response = client.get(url)
            if response.status_code == 200:
                data = response.json()
                return parse_estatdb_response(data, year)
    except Exception as e:
        print(f"e-Stat DB APIエラー: {e}")

    return []


def parse_estatdb_response(data: dict, year: int) -> list:
    """e-Stat Dashboard APIレスポンスをパース"""
    population_data = []

    try:
        values = data.get("GET_STATS", {}).get("STATISTICAL_DATA", {}).get("DATA_INF", {}).get("VALUE", [])

        for item in values:
            area_code = item.get("@area", "")
            value = item.get("$", "")

            if len(area_code) == 5 and area_code.isdigit():
                try:
                    population = int(value.replace(",", ""))
                    pref_code = area_code[:2]

                    population_data.append({
                        "code": area_code,
                        "prefecture": PREFECTURES.get(pref_code, ""),
                        "municipality": "",
                        "population": population,
                    })
                except (ValueError, AttributeError):
                    pass

    except Exception as e:
        print(f"パースエラー: {e}")

    return population_data


def save_to_cache(year: int, data: list):
    """データをキャッシュファイルに保存"""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_file = CACHE_DIR / f"population_{year}.json"

    with open(cache_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"保存完了: {cache_file} ({len(data)}件)")


def download_year(year: int) -> bool:
    """指定年のデータをダウンロード"""
    print(f"\n{'='*60}")
    print(f"{year}年のデータを取得")
    print("=" * 60)

    data = []

    # 方法1: e-Stat CSVダウンロード
    csv_content = download_estat_csv(year)
    if csv_content:
        data = parse_census_csv(csv_content, year)

    # 方法2: e-Stat Dashboard API
    if not data:
        print("e-Stat Dashboard APIを試行...")
        data = download_estatdb_data(year)

    # 方法3: SSDSE データ
    if not data:
        print("SSDSEデータを試行...")
        data = fetch_ssdse_data(year)

    if data:
        save_to_cache(year, data)
        return True
    else:
        print(f"警告: {year}年のデータを取得できませんでした")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="e-Statから国勢調査の人口データをダウンロード"
    )
    parser.add_argument(
        "--year", type=int, help="取得する年（2015, 2020）"
    )
    parser.add_argument(
        "--all", action="store_true", help="全年度のデータを取得"
    )

    args = parser.parse_args()

    if args.all:
        years = [2020, 2015]
        for year in years:
            download_year(year)
    elif args.year:
        download_year(args.year)
    else:
        parser.print_help()
        print("\n利用可能な年: 2015, 2020")


if __name__ == "__main__":
    main()
