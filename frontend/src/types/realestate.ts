export interface RealEstateTransaction {
  trade_price: number | null;
  unit_price: number | null;
  area: number | null;
  prefecture: string;
  municipality: string;
  district: string | null;
  trade_date: string | null;
  building_year: string | null;
  structure: string | null;
  use: string | null;
  city_planning: string | null;
  price_classification: string | null;
}

export interface RealEstateResponse {
  year: number;
  prefecture_code: string;
  city_code: string | null;
  total_count: number;
  data: RealEstateTransaction[];
}

export interface RealEstateSummary {
  code: string;
  prefecture: string;
  municipality: string;
  year: number;
  transaction_count: number;
  avg_unit_price: number | null;
  avg_trade_price: number | null;
  min_unit_price: number | null;
  max_unit_price: number | null;
}

export interface RealEstateYearlyData {
  year: number;
  transaction_count: number;
  avg_unit_price: number;
  min_unit_price: number;
  max_unit_price: number;
}

export interface RealEstateTimeSeries {
  code: string;
  prefecture: string;
  municipality: string;
  data: RealEstateYearlyData[];
}
