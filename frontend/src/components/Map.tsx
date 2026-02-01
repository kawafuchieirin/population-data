import { useCallback, useMemo } from "react";
import { GoogleMap, useJsApiLoader, Marker, InfoWindow } from "@react-google-maps/api";
import { useState } from "react";
import type { MunicipalityPopulation } from "../types/population";

interface MapProps {
  populationData: MunicipalityPopulation[];
  loading: boolean;
}

// 市区町村コードから緯度経度を取得するマッピング（主要都市のみ）
const MUNICIPALITY_COORDS: Record<string, { lat: number; lng: number }> = {
  "01100": { lat: 43.0618, lng: 141.3545 }, // 札幌市
  "04100": { lat: 38.2682, lng: 140.8694 }, // 仙台市
  "11100": { lat: 35.8617, lng: 139.6455 }, // さいたま市
  "12100": { lat: 35.6073, lng: 140.1063 }, // 千葉市
  "13101": { lat: 35.6940, lng: 139.7536 }, // 千代田区
  "13102": { lat: 35.6706, lng: 139.7727 }, // 中央区
  "13103": { lat: 35.6581, lng: 139.7514 }, // 港区
  "13104": { lat: 35.6938, lng: 139.7034 }, // 新宿区
  "13105": { lat: 35.7080, lng: 139.7522 }, // 文京区
  "13106": { lat: 35.7125, lng: 139.7797 }, // 台東区
  "13107": { lat: 35.7108, lng: 139.8019 }, // 墨田区
  "13108": { lat: 35.6729, lng: 139.8171 }, // 江東区
  "13109": { lat: 35.6090, lng: 139.7301 }, // 品川区
  "13110": { lat: 35.6414, lng: 139.6982 }, // 目黒区
  "13111": { lat: 35.5613, lng: 139.7160 }, // 大田区
  "13112": { lat: 35.6461, lng: 139.6532 }, // 世田谷区
  "13113": { lat: 35.6639, lng: 139.6980 }, // 渋谷区
  "13114": { lat: 35.7078, lng: 139.6638 }, // 中野区
  "13115": { lat: 35.6995, lng: 139.6364 }, // 杉並区
  "13116": { lat: 35.7295, lng: 139.7109 }, // 豊島区
  "13117": { lat: 35.7528, lng: 139.7376 }, // 北区
  "13118": { lat: 35.7365, lng: 139.7833 }, // 荒川区
  "13119": { lat: 35.7514, lng: 139.7094 }, // 板橋区
  "13120": { lat: 35.7355, lng: 139.6527 }, // 練馬区
  "13121": { lat: 35.7748, lng: 139.8046 }, // 足立区
  "13122": { lat: 35.7436, lng: 139.8477 }, // 葛飾区
  "13123": { lat: 35.7065, lng: 139.8682 }, // 江戸川区
  "14100": { lat: 35.4437, lng: 139.6380 }, // 横浜市
  "14130": { lat: 35.5309, lng: 139.7029 }, // 川崎市
  "23100": { lat: 35.1815, lng: 136.9066 }, // 名古屋市
  "26100": { lat: 35.0116, lng: 135.7681 }, // 京都市
  "27100": { lat: 34.6937, lng: 135.5023 }, // 大阪市
  "28100": { lat: 34.6901, lng: 135.1956 }, // 神戸市
  "33100": { lat: 34.6551, lng: 133.9195 }, // 岡山市
  "34100": { lat: 34.3853, lng: 132.4553 }, // 広島市
  "40100": { lat: 33.8835, lng: 130.8752 }, // 北九州市
  "40130": { lat: 33.5904, lng: 130.4017 }, // 福岡市
};

const containerStyle = {
  width: "100%",
  height: "100%",
};

const defaultCenter = {
  lat: 35.6762,
  lng: 139.6503,
};

// 人口に応じた色を取得
function getColorByPopulation(population: number): string {
  if (population >= 3000000) return "#d73027"; // 300万以上
  if (population >= 2000000) return "#f46d43"; // 200万以上
  if (population >= 1000000) return "#fdae61"; // 100万以上
  if (population >= 500000) return "#fee08b"; // 50万以上
  if (population >= 200000) return "#d9ef8b"; // 20万以上
  if (population >= 100000) return "#a6d96a"; // 10万以上
  return "#66bd63"; // 10万未満
}

// 人口に応じたマーカーサイズを取得
function getMarkerScale(population: number): number {
  if (population >= 3000000) return 20;
  if (population >= 2000000) return 16;
  if (population >= 1000000) return 12;
  if (population >= 500000) return 10;
  if (population >= 200000) return 8;
  return 6;
}

export function Map({ populationData, loading }: MapProps) {
  const [selectedMunicipality, setSelectedMunicipality] =
    useState<MunicipalityPopulation | null>(null);

  const { isLoaded, loadError } = useJsApiLoader({
    googleMapsApiKey: import.meta.env.VITE_GOOGLE_MAPS_API_KEY || "",
  });

  const markers = useMemo(() => {
    return populationData
      .filter((item) => MUNICIPALITY_COORDS[item.code])
      .map((item) => ({
        ...item,
        position: MUNICIPALITY_COORDS[item.code],
        color: getColorByPopulation(item.population),
        scale: getMarkerScale(item.population),
      }));
  }, [populationData]);

  const handleMarkerClick = useCallback((municipality: MunicipalityPopulation) => {
    setSelectedMunicipality(municipality);
  }, []);

  const handleInfoWindowClose = useCallback(() => {
    setSelectedMunicipality(null);
  }, []);

  if (loadError) {
    return (
      <div className="map-error">
        地図の読み込みに失敗しました。
        <br />
        Google Maps APIキーを確認してください。
      </div>
    );
  }

  if (!isLoaded) {
    return <div className="map-loading">地図を読み込み中...</div>;
  }

  return (
    <GoogleMap
      mapContainerStyle={containerStyle}
      center={defaultCenter}
      zoom={6}
      options={{
        mapTypeControl: false,
        streetViewControl: false,
      }}
    >
      {!loading &&
        markers.map((marker) => (
          <Marker
            key={marker.code}
            position={marker.position}
            onClick={() => handleMarkerClick(marker)}
            icon={{
              path: google.maps.SymbolPath.CIRCLE,
              fillColor: marker.color,
              fillOpacity: 0.8,
              strokeColor: "#ffffff",
              strokeWeight: 2,
              scale: marker.scale,
            }}
          />
        ))}

      {selectedMunicipality && MUNICIPALITY_COORDS[selectedMunicipality.code] && (
        <InfoWindow
          position={MUNICIPALITY_COORDS[selectedMunicipality.code]}
          onCloseClick={handleInfoWindowClose}
        >
          <div className="info-window">
            <h3>
              {selectedMunicipality.prefecture} {selectedMunicipality.municipality}
            </h3>
            <p>人口: {selectedMunicipality.population.toLocaleString()}人</p>
          </div>
        </InfoWindow>
      )}
    </GoogleMap>
  );
}
