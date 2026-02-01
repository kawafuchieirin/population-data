import { useCallback, useEffect, useState } from "react";
import axios from "axios";
import type {
  MunicipalityListItem,
  MunicipalityListResponse,
  MunicipalityTimeSeries,
} from "../types/population";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

export function useMunicipalityDetail() {
  const [municipalities, setMunicipalities] = useState<MunicipalityListItem[]>(
    []
  );
  const [selectedCode, setSelectedCode] = useState<string | null>(null);
  const [timeSeries, setTimeSeries] = useState<MunicipalityTimeSeries | null>(
    null
  );
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // 市区町村一覧を取得
  useEffect(() => {
    const fetchMunicipalities = async () => {
      try {
        const response = await axios.get<MunicipalityListResponse>(
          `${API_URL}/api/municipalities`
        );
        setMunicipalities(response.data.municipalities);
      } catch (err) {
        console.error("市区町村一覧の取得に失敗しました", err);
      }
    };
    fetchMunicipalities();
  }, []);

  // 時系列データを取得
  const fetchTimeSeries = useCallback(async (code: string) => {
    setLoading(true);
    setError(null);
    try {
      const response = await axios.get<MunicipalityTimeSeries>(
        `${API_URL}/api/population/municipality/${code}`
      );
      setTimeSeries(response.data);
      setSelectedCode(code);
    } catch (err) {
      setError("時系列データの取得に失敗しました");
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, []);

  const clearSelection = useCallback(() => {
    setSelectedCode(null);
    setTimeSeries(null);
  }, []);

  return {
    municipalities,
    selectedCode,
    timeSeries,
    loading,
    error,
    fetchTimeSeries,
    clearSelection,
  };
}
