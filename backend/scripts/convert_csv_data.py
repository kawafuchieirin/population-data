#!/usr/bin/env python3
"""
e-StatからダウンロードしたCSVファイルを変換するスクリプト

使用方法:
    1. e-Stat (https://www.e-stat.go.jp/) から国勢調査の人口データCSVをダウンロード
    2. CSVファイルを backend/data/raw/ ディレクトリに配置
    3. python scripts/convert_csv_data.py

CSVダウンロード手順:
    1. https://www.e-stat.go.jp/stat-search/files?stat_infid=000032143614 (2020年)
    2. 「CSV」ボタンをクリックしてダウンロード
    3. ファイル名を population_2020.csv などにリネーム
"""

import argparse
import csv
import json
import re
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
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


def detect_encoding(file_path: Path) -> str:
    """ファイルのエンコーディングを検出"""
    encodings = ["utf-8", "cp932", "shift_jis", "euc-jp"]
    for enc in encodings:
        try:
            with open(file_path, encoding=enc) as f:
                f.read(1000)
            return enc
        except (UnicodeDecodeError, LookupError):
            continue
    return "utf-8"


def parse_population(value: str) -> int | None:
    """人口値をパース"""
    if not value or value in ["-", "…", "x", "X", "*"]:
        return None
    # カンマや空白を除去
    cleaned = re.sub(r"[,\s]", "", value)
    try:
        return int(cleaned)
    except ValueError:
        return None


def convert_estat_csv(csv_path: Path, year: int) -> list:
    """e-StatのCSVファイルを変換"""
    encoding = detect_encoding(csv_path)
    print(f"エンコーディング: {encoding}")

    population_data = []

    with open(csv_path, encoding=encoding, errors="replace") as f:
        # CSVの形式を自動検出
        sample = f.read(4096)
        f.seek(0)

        # ヘッダー行をスキップ（e-StatのCSVは複数行ヘッダーがある場合がある）
        lines = f.readlines()

    # データ行を探す
    data_start = 0
    for i, line in enumerate(lines):
        # 市区町村コードらしき5桁の数字を含む行を探す
        if re.search(r"[0-9]{5}", line):
            data_start = i
            break

    print(f"データ開始行: {data_start + 1}")

    # CSVとしてパース
    reader = csv.reader(lines[data_start:])

    for row in reader:
        if len(row) < 3:
            continue

        # 市区町村コード（5桁）を探す
        code = None
        name = None
        population = None

        for i, cell in enumerate(row):
            cell = cell.strip()

            # 5桁の数字 = 市区町村コード
            if re.match(r"^[0-9]{5}$", cell):
                code = cell
            # 都道府県や市区町村の名前
            elif re.match(r"^[ぁ-んァ-ン一-龥]+[都道府県市区町村]", cell):
                name = cell
            # 人口値（最初に見つかった大きな数値）
            elif population is None:
                pop = parse_population(cell)
                if pop and pop > 100:  # 100人以上を人口とみなす
                    population = pop

        if code and population:
            pref_code = code[:2]
            prefecture = PREFECTURES.get(pref_code, "")

            # 市区町村名を抽出（都道府県名を除去）
            municipality = name or ""
            if prefecture and municipality.startswith(prefecture):
                municipality = municipality[len(prefecture):]

            population_data.append({
                "code": code,
                "prefecture": prefecture,
                "municipality": municipality,
                "population": population,
            })

    return population_data


def generate_sample_data(year: int) -> list:
    """サンプルデータを生成（CSVがない場合のフォールバック）"""
    # 主要市区町村のサンプルデータ（2020年国勢調査ベース）
    base_data = [
        # 政令指定都市
        ("01100", "北海道", "札幌市", 1973395),
        ("04100", "宮城県", "仙台市", 1096704),
        ("11100", "埼玉県", "さいたま市", 1324025),
        ("12100", "千葉県", "千葉市", 974951),
        ("14100", "神奈川県", "横浜市", 3748781),
        ("14130", "神奈川県", "川崎市", 1538262),
        ("14150", "神奈川県", "相模原市", 725493),
        ("15100", "新潟県", "新潟市", 789275),
        ("22100", "静岡県", "静岡市", 693389),
        ("22130", "静岡県", "浜松市", 790718),
        ("23100", "愛知県", "名古屋市", 2320361),
        ("26100", "京都府", "京都市", 1463723),
        ("27100", "大阪府", "大阪市", 2752412),
        ("27140", "大阪府", "堺市", 826161),
        ("28100", "兵庫県", "神戸市", 1525152),
        ("33100", "岡山県", "岡山市", 724691),
        ("34100", "広島県", "広島市", 1200754),
        ("40100", "福岡県", "北九州市", 939029),
        ("40130", "福岡県", "福岡市", 1612392),
        ("43100", "熊本県", "熊本市", 738865),
        # 東京23区
        ("13101", "東京都", "千代田区", 66680),
        ("13102", "東京都", "中央区", 169179),
        ("13103", "東京都", "港区", 260379),
        ("13104", "東京都", "新宿区", 346235),
        ("13105", "東京都", "文京区", 240069),
        ("13106", "東京都", "台東区", 211444),
        ("13107", "東京都", "墨田区", 272085),
        ("13108", "東京都", "江東区", 524310),
        ("13109", "東京都", "品川区", 422488),
        ("13110", "東京都", "目黒区", 288088),
        ("13111", "東京都", "大田区", 748081),
        ("13112", "東京都", "世田谷区", 943664),
        ("13113", "東京都", "渋谷区", 243883),
        ("13114", "東京都", "中野区", 344880),
        ("13115", "東京都", "杉並区", 591108),
        ("13116", "東京都", "豊島区", 301599),
        ("13117", "東京都", "北区", 355213),
        ("13118", "東京都", "荒川区", 217475),
        ("13119", "東京都", "板橋区", 584483),
        ("13120", "東京都", "練馬区", 752608),
        ("13121", "東京都", "足立区", 695043),
        ("13122", "東京都", "葛飾区", 453093),
        ("13123", "東京都", "江戸川区", 697932),
        # 中核市・その他主要都市
        ("01202", "北海道", "函館市", 251084),
        ("01203", "北海道", "旭川市", 329306),
        ("02201", "青森県", "青森市", 275192),
        ("03201", "岩手県", "盛岡市", 289731),
        ("05201", "秋田県", "秋田市", 307672),
        ("06201", "山形県", "山形市", 248252),
        ("07201", "福島県", "福島市", 283348),
        ("07203", "福島県", "郡山市", 324272),
        ("07204", "福島県", "いわき市", 332931),
        ("08201", "茨城県", "水戸市", 270685),
        ("09201", "栃木県", "宇都宮市", 518757),
        ("10201", "群馬県", "前橋市", 336154),
        ("10202", "群馬県", "高崎市", 370884),
        ("11201", "埼玉県", "川越市", 354571),
        ("11202", "埼玉県", "熊谷市", 195781),
        ("11203", "埼玉県", "川口市", 594274),
        ("11222", "埼玉県", "越谷市", 341621),
        ("12203", "千葉県", "市川市", 496676),
        ("12204", "千葉県", "船橋市", 642907),
        ("12207", "千葉県", "松戸市", 498232),
        ("12216", "千葉県", "柏市", 426468),
        ("13201", "東京都", "八王子市", 579355),
        ("13202", "東京都", "立川市", 184183),
        ("13203", "東京都", "武蔵野市", 150149),
        ("13204", "東京都", "三鷹市", 195391),
        ("13208", "東京都", "調布市", 242614),
        ("13210", "東京都", "町田市", 432348),
        ("13215", "東京都", "府中市", 262790),
        ("13219", "東京都", "西東京市", 207388),
        ("14201", "神奈川県", "横須賀市", 389326),
        ("14204", "神奈川県", "平塚市", 258206),
        ("14205", "神奈川県", "鎌倉市", 172710),
        ("14206", "神奈川県", "藤沢市", 436905),
        ("16201", "富山県", "富山市", 413938),
        ("17201", "石川県", "金沢市", 463254),
        ("18201", "福井県", "福井市", 262328),
        ("19201", "山梨県", "甲府市", 188405),
        ("20201", "長野県", "長野市", 372760),
        ("20202", "長野県", "松本市", 241145),
        ("21201", "岐阜県", "岐阜市", 402557),
        ("23201", "愛知県", "豊橋市", 371920),
        ("23202", "愛知県", "岡崎市", 386999),
        ("23211", "愛知県", "豊田市", 421487),
        ("24201", "三重県", "津市", 274552),
        ("24202", "三重県", "四日市市", 311031),
        ("25201", "滋賀県", "大津市", 345070),
        ("27202", "大阪府", "岸和田市", 189988),
        ("27203", "大阪府", "豊中市", 401558),
        ("27204", "大阪府", "池田市", 104143),
        ("27205", "大阪府", "吹田市", 385987),
        ("27207", "大阪府", "高槻市", 351686),
        ("27210", "大阪府", "枚方市", 401090),
        ("27212", "大阪府", "八尾市", 264034),
        ("27227", "大阪府", "東大阪市", 496681),
        ("28201", "兵庫県", "姫路市", 530495),
        ("28202", "兵庫県", "尼崎市", 452563),
        ("28203", "兵庫県", "明石市", 303601),
        ("28204", "兵庫県", "西宮市", 485587),
        ("29201", "奈良県", "奈良市", 354630),
        ("30201", "和歌山県", "和歌山市", 356729),
        ("31201", "鳥取県", "鳥取市", 188465),
        ("32201", "島根県", "松江市", 203616),
        ("33202", "岡山県", "倉敷市", 477118),
        ("34202", "広島県", "呉市", 214592),
        ("34207", "広島県", "福山市", 460709),
        ("35201", "山口県", "下関市", 255051),
        ("35203", "山口県", "山口市", 194910),
        ("36201", "徳島県", "徳島市", 252391),
        ("37201", "香川県", "高松市", 420748),
        ("38201", "愛媛県", "松山市", 511192),
        ("39201", "高知県", "高知市", 326545),
        ("40202", "福岡県", "大牟田市", 111281),
        ("40203", "福岡県", "久留米市", 303316),
        ("41201", "佐賀県", "佐賀市", 233301),
        ("42201", "長崎県", "長崎市", 409118),
        ("42202", "長崎県", "佐世保市", 243223),
        ("44201", "大分県", "大分市", 478146),
        ("45201", "宮崎県", "宮崎市", 401339),
        ("46201", "鹿児島県", "鹿児島市", 593128),
        ("47201", "沖縄県", "那覇市", 317625),
    ]

    # 年による人口変動を適用（概算）
    # 2020年を基準に、5年ごとに約2%の変動を想定
    year_diff = (year - 2020) // 5
    factor = 1 + (year_diff * -0.02)  # 過去は人口が多い傾向

    return [
        {
            "code": code,
            "prefecture": pref,
            "municipality": muni,
            "population": int(pop * factor),
        }
        for code, pref, muni, pop in base_data
    ]


def save_to_cache(year: int, data: list):
    """データをキャッシュファイルに保存"""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_file = CACHE_DIR / f"population_{year}.json"

    with open(cache_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"保存完了: {cache_file} ({len(data)}件)")


def main():
    parser = argparse.ArgumentParser(
        description="e-StatのCSVデータを変換、またはサンプルデータを生成"
    )
    parser.add_argument(
        "--csv", type=str, help="変換するCSVファイルのパス"
    )
    parser.add_argument(
        "--year", type=int, help="データの年"
    )
    parser.add_argument(
        "--generate-sample", action="store_true",
        help="サンプルデータを生成（CSVなしで動作確認用）"
    )
    parser.add_argument(
        "--all-years", action="store_true",
        help="全年度（2000-2020）のサンプルデータを生成"
    )

    args = parser.parse_args()

    if args.all_years:
        years = [2000, 2005, 2010, 2015, 2020]
        print("全年度のサンプルデータを生成します...")
        for year in years:
            data = generate_sample_data(year)
            save_to_cache(year, data)
        print(f"\n完了: {len(years)}年分のデータを生成しました")

    elif args.generate_sample:
        year = args.year or 2020
        print(f"{year}年のサンプルデータを生成...")
        data = generate_sample_data(year)
        save_to_cache(year, data)

    elif args.csv and args.year:
        csv_path = Path(args.csv)
        if not csv_path.exists():
            print(f"エラー: ファイルが見つかりません: {csv_path}")
            return

        print(f"{args.year}年のCSVを変換中: {csv_path}")
        data = convert_estat_csv(csv_path, args.year)

        if data:
            save_to_cache(args.year, data)
        else:
            print("データが抽出できませんでした")

    else:
        parser.print_help()
        print("\n例:")
        print("  # 全年度のサンプルデータを生成")
        print("  python scripts/convert_csv_data.py --all-years")
        print("")
        print("  # CSVを変換")
        print("  python scripts/convert_csv_data.py --csv data/raw/population_2020.csv --year 2020")


if __name__ == "__main__":
    main()
