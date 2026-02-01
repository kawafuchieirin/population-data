import { useCallback, useState } from "react";
import axios from "axios";
import type { RealEstateTimeSeries } from "../types/realestate";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

export function useRealEstate() {
  const [realEstateData, setRealEstateData] =
    useState<RealEstateTimeSeries | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchRealEstateTimeSeries = useCallback(async (code: string) => {
    setLoading(true);
    setError(null);
    try {
      const response = await axios.get<RealEstateTimeSeries>(
        `${API_URL}/api/realestate/municipality/${code}`
      );
      setRealEstateData(response.data);
    } catch (err) {
      setError("不動産価格データの取得に失敗しました");
      console.error(err);
      setRealEstateData(null);
    } finally {
      setLoading(false);
    }
  }, []);

  const clearRealEstateData = useCallback(() => {
    setRealEstateData(null);
  }, []);

  return {
    realEstateData,
    loading,
    error,
    fetchRealEstateTimeSeries,
    clearRealEstateData,
  };
}
