export interface MunicipalityPopulation {
  code: string;
  prefecture: string;
  municipality: string;
  population: number;
}

export interface PopulationResponse {
  year: number;
  data: MunicipalityPopulation[];
}

export interface AvailableYearsResponse {
  years: number[];
}

export interface YearlyPopulation {
  year: number;
  population: number;
}

export interface MunicipalityTimeSeries {
  code: string;
  prefecture: string;
  municipality: string;
  data: YearlyPopulation[];
}

export interface MunicipalityListItem {
  code: string;
  prefecture: string;
  municipality: string;
}

export interface MunicipalityListResponse {
  municipalities: MunicipalityListItem[];
}
