import { useCallback, useEffect, useState } from "react";
import axios from "axios";
import type {
  AvailableYearsResponse,
  MunicipalityPopulation,
  PopulationResponse,
} from "../types/population";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

export function usePopulation() {
  const [availableYears, setAvailableYears] = useState<number[]>([]);
  const [selectedYear, setSelectedYear] = useState<number | null>(null);
  const [populationData, setPopulationData] = useState<MunicipalityPopulation[]>(
    []
  );
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // 利用可能な年を取得
  useEffect(() => {
    const fetchYears = async () => {
      try {
        const response = await axios.get<AvailableYearsResponse>(
          `${API_URL}/api/population/years`
        );
        setAvailableYears(response.data.years);
        if (response.data.years.length > 0) {
          setSelectedYear(response.data.years[0]);
        }
      } catch (err) {
        setError("年データの取得に失敗しました");
        console.error(err);
      }
    };
    fetchYears();
  }, []);

  // 選択された年の人口データを取得
  const fetchPopulation = useCallback(async (year: number) => {
    setLoading(true);
    setError(null);
    try {
      const response = await axios.get<PopulationResponse>(
        `${API_URL}/api/population`,
        { params: { year } }
      );
      setPopulationData(response.data.data);
    } catch (err) {
      setError("人口データの取得に失敗しました");
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (selectedYear !== null) {
      fetchPopulation(selectedYear);
    }
  }, [selectedYear, fetchPopulation]);

  return {
    availableYears,
    selectedYear,
    setSelectedYear,
    populationData,
    loading,
    error,
  };
}
