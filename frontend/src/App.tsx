import { useEffect } from "react";
import { Map } from "./components/Map";
import { TimeSlider } from "./components/TimeSlider";
import { MunicipalitySearch } from "./components/MunicipalitySearch";
import { CombinedChart } from "./components/CombinedChart";
import { usePopulation } from "./hooks/usePopulation";
import { useMunicipalityDetail } from "./hooks/useMunicipalityDetail";
import { useRealEstate } from "./hooks/useRealEstate";
import "./App.css";

function App() {
  const {
    availableYears,
    selectedYear,
    setSelectedYear,
    populationData,
    loading,
    error,
  } = usePopulation();

  const {
    municipalities,
    selectedCode,
    timeSeries,
    loading: detailLoading,
    error: detailError,
    fetchTimeSeries,
    clearSelection,
  } = useMunicipalityDetail();

  const {
    realEstateData,
    loading: realEstateLoading,
    error: realEstateError,
    fetchRealEstateTimeSeries,
    clearRealEstateData,
  } = useRealEstate();

  // 市区町村が選択されたら不動産データも取得
  useEffect(() => {
    if (selectedCode) {
      fetchRealEstateTimeSeries(selectedCode);
    }
  }, [selectedCode, fetchRealEstateTimeSeries]);

  const handleClearSelection = () => {
    clearSelection();
    clearRealEstateData();
  };

  return (
    <div className="app">
      <header className="app-header">
        <h1>市区町村人口・不動産マップ</h1>
        <p>国勢調査データと不動産取引価格の可視化</p>
      </header>

      {(error || detailError || realEstateError) && (
        <div className="error-message">
          {error || detailError || realEstateError}
        </div>
      )}

      <main className="app-main">
        <div className="map-container">
          <Map populationData={populationData} loading={loading} />
        </div>

        <div className="controls">
          <TimeSlider
            years={availableYears}
            selectedYear={selectedYear}
            onYearChange={setSelectedYear}
            loading={loading}
          />

          <div className="section-divider" />

          <MunicipalitySearch
            municipalities={municipalities}
            onSelect={fetchTimeSeries}
            selectedCode={selectedCode}
          />

          {detailLoading && (
            <div className="loading-message">データを読み込み中...</div>
          )}

          <div className="section-divider" />

          <div className="legend">
            <h3>人口凡例</h3>
            <div className="legend-items">
              <div className="legend-item">
                <span
                  className="legend-color"
                  style={{ backgroundColor: "#d73027" }}
                ></span>
                <span>300万人以上</span>
              </div>
              <div className="legend-item">
                <span
                  className="legend-color"
                  style={{ backgroundColor: "#f46d43" }}
                ></span>
                <span>200万人以上</span>
              </div>
              <div className="legend-item">
                <span
                  className="legend-color"
                  style={{ backgroundColor: "#fdae61" }}
                ></span>
                <span>100万人以上</span>
              </div>
              <div className="legend-item">
                <span
                  className="legend-color"
                  style={{ backgroundColor: "#fee08b" }}
                ></span>
                <span>50万人以上</span>
              </div>
              <div className="legend-item">
                <span
                  className="legend-color"
                  style={{ backgroundColor: "#d9ef8b" }}
                ></span>
                <span>20万人以上</span>
              </div>
              <div className="legend-item">
                <span
                  className="legend-color"
                  style={{ backgroundColor: "#a6d96a" }}
                ></span>
                <span>10万人以上</span>
              </div>
              <div className="legend-item">
                <span
                  className="legend-color"
                  style={{ backgroundColor: "#66bd63" }}
                ></span>
                <span>10万人未満</span>
              </div>
            </div>
          </div>

          <div className="section-divider" />

          <div className="api-note">
            <p>
              不動産価格データは国土交通省
              <a
                href="https://www.reinfolib.mlit.go.jp/"
                target="_blank"
                rel="noopener noreferrer"
              >
                不動産情報ライブラリ
              </a>
              より取得
            </p>
          </div>
        </div>
      </main>

      {timeSeries && (
        <div className="chart-modal">
          <div className="chart-modal-backdrop" onClick={handleClearSelection} />
          <div className="chart-modal-content">
            <CombinedChart
              populationData={timeSeries}
              realEstateData={realEstateData}
              realEstateLoading={realEstateLoading}
              onClose={handleClearSelection}
            />
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
