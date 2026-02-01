import { useMemo, useState } from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
  ComposedChart,
  Bar,
} from "recharts";
import type { MunicipalityTimeSeries } from "../types/population";
import type { RealEstateTimeSeries } from "../types/realestate";

interface CombinedChartProps {
  populationData: MunicipalityTimeSeries;
  realEstateData: RealEstateTimeSeries | null;
  realEstateLoading: boolean;
  onClose: () => void;
}

type TabType = "population" | "realestate" | "combined";

export function CombinedChart({
  populationData,
  realEstateData,
  realEstateLoading,
  onClose,
}: CombinedChartProps) {
  const [activeTab, setActiveTab] = useState<TabType>("combined");

  // 人口データと不動産データを統合
  const combinedData = useMemo(() => {
    const dataMap = new Map<number, {
      year: number;
      population?: number;
      avg_unit_price?: number;
      transaction_count?: number;
    }>();

    // 人口データを追加
    populationData.data.forEach((d) => {
      dataMap.set(d.year, {
        year: d.year,
        population: d.population,
      });
    });

    // 不動産データを追加
    if (realEstateData) {
      realEstateData.data.forEach((d) => {
        const existing = dataMap.get(d.year) || { year: d.year };
        dataMap.set(d.year, {
          ...existing,
          avg_unit_price: d.avg_unit_price,
          transaction_count: d.transaction_count,
        });
      });
    }

    return Array.from(dataMap.values()).sort((a, b) => a.year - b.year);
  }, [populationData, realEstateData]);

  // 人口の変化を計算
  const firstPopYear = populationData.data[0];
  const lastPopYear = populationData.data[populationData.data.length - 1];
  const popChange = lastPopYear.population - firstPopYear.population;
  const popChangePercent = ((popChange / firstPopYear.population) * 100).toFixed(1);

  // 不動産価格の変化を計算
  const priceChange = useMemo(() => {
    if (!realEstateData || realEstateData.data.length < 2) return null;
    const first = realEstateData.data[0];
    const last = realEstateData.data[realEstateData.data.length - 1];
    const change = last.avg_unit_price - first.avg_unit_price;
    const changePercent = ((change / first.avg_unit_price) * 100).toFixed(1);
    return { first, last, change, changePercent };
  }, [realEstateData]);

  return (
    <div className="population-chart-container">
      <div className="chart-header">
        <div className="chart-title">
          <h3>
            {populationData.prefecture} {populationData.municipality}
          </h3>
          <span className="chart-subtitle">
            人口・不動産価格推移
          </span>
        </div>
        <button className="chart-close" onClick={onClose}>
          ×
        </button>
      </div>

      {/* タブ切り替え */}
      <div className="chart-tabs">
        <button
          className={`chart-tab ${activeTab === "combined" ? "active" : ""}`}
          onClick={() => setActiveTab("combined")}
        >
          総合
        </button>
        <button
          className={`chart-tab ${activeTab === "population" ? "active" : ""}`}
          onClick={() => setActiveTab("population")}
        >
          人口
        </button>
        <button
          className={`chart-tab ${activeTab === "realestate" ? "active" : ""}`}
          onClick={() => setActiveTab("realestate")}
          disabled={!realEstateData && !realEstateLoading}
        >
          不動産価格
          {realEstateLoading && " (読込中...)"}
        </button>
      </div>

      {/* 統計サマリー */}
      <div className="chart-stats">
        <div className="stat-group">
          <div className="stat-group-title">人口</div>
          <div className="stat-row">
            <div className="stat-item">
              <span className="stat-label">{firstPopYear.year}年</span>
              <span className="stat-value">
                {firstPopYear.population.toLocaleString()}人
              </span>
            </div>
            <div className="stat-arrow">→</div>
            <div className="stat-item">
              <span className="stat-label">{lastPopYear.year}年</span>
              <span className="stat-value">
                {lastPopYear.population.toLocaleString()}人
              </span>
            </div>
            <div className="stat-item">
              <span className="stat-label">変化</span>
              <span className={`stat-value ${popChange >= 0 ? "positive" : "negative"}`}>
                {popChange >= 0 ? "+" : ""}{popChange.toLocaleString()}人
                ({popChange >= 0 ? "+" : ""}{popChangePercent}%)
              </span>
            </div>
          </div>
        </div>

        {priceChange && (
          <div className="stat-group">
            <div className="stat-group-title">平均単価（円/㎡）</div>
            <div className="stat-row">
              <div className="stat-item">
                <span className="stat-label">{priceChange.first.year}年</span>
                <span className="stat-value">
                  ¥{priceChange.first.avg_unit_price.toLocaleString()}
                </span>
              </div>
              <div className="stat-arrow">→</div>
              <div className="stat-item">
                <span className="stat-label">{priceChange.last.year}年</span>
                <span className="stat-value">
                  ¥{priceChange.last.avg_unit_price.toLocaleString()}
                </span>
              </div>
              <div className="stat-item">
                <span className="stat-label">変化</span>
                <span className={`stat-value ${priceChange.change >= 0 ? "positive" : "negative"}`}>
                  {priceChange.change >= 0 ? "+" : ""}¥{priceChange.change.toLocaleString()}
                  ({priceChange.change >= 0 ? "+" : ""}{priceChange.changePercent}%)
                </span>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* グラフ */}
      <div className="chart-wrapper">
        {activeTab === "combined" && (
          <ResponsiveContainer width="100%" height={350}>
            <ComposedChart data={combinedData} margin={{ top: 20, right: 60, left: 20, bottom: 20 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e0e0e0" />
              <XAxis
                dataKey="year"
                tick={{ fontSize: 12 }}
                tickFormatter={(value) => `${value}`}
              />
              <YAxis
                yAxisId="left"
                tick={{ fontSize: 12 }}
                tickFormatter={(value) =>
                  value >= 1000000
                    ? `${(value / 1000000).toFixed(1)}M`
                    : value >= 1000
                    ? `${(value / 1000).toFixed(0)}K`
                    : value.toString()
                }
                label={{ value: "人口", angle: -90, position: "insideLeft", fontSize: 12 }}
              />
              <YAxis
                yAxisId="right"
                orientation="right"
                tick={{ fontSize: 12 }}
                tickFormatter={(value) =>
                  value >= 1000000
                    ? `${(value / 1000000).toFixed(1)}M`
                    : value >= 1000
                    ? `${(value / 1000).toFixed(0)}K`
                    : value.toString()
                }
                label={{ value: "円/㎡", angle: 90, position: "insideRight", fontSize: 12 }}
              />
              <Tooltip
                formatter={(value, name) => {
                  if (name === "人口") return [`${Number(value).toLocaleString()}人`, name];
                  if (name === "平均単価") return [`¥${Number(value).toLocaleString()}/㎡`, name];
                  return [value, name];
                }}
                labelFormatter={(label) => `${label}年`}
              />
              <Legend />
              <Line
                yAxisId="left"
                type="monotone"
                dataKey="population"
                name="人口"
                stroke="#1a1a2e"
                strokeWidth={2}
                dot={{ fill: "#1a1a2e", strokeWidth: 2, r: 4 }}
                connectNulls
              />
              {realEstateData && (
                <Line
                  yAxisId="right"
                  type="monotone"
                  dataKey="avg_unit_price"
                  name="平均単価"
                  stroke="#e67e22"
                  strokeWidth={2}
                  dot={{ fill: "#e67e22", strokeWidth: 2, r: 4 }}
                  connectNulls
                />
              )}
            </ComposedChart>
          </ResponsiveContainer>
        )}

        {activeTab === "population" && (
          <ResponsiveContainer width="100%" height={350}>
            <LineChart data={populationData.data} margin={{ top: 20, right: 30, left: 20, bottom: 20 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e0e0e0" />
              <XAxis dataKey="year" tick={{ fontSize: 12 }} tickFormatter={(value) => `${value}年`} />
              <YAxis
                tick={{ fontSize: 12 }}
                tickFormatter={(value) =>
                  value >= 1000000
                    ? `${(value / 1000000).toFixed(1)}M`
                    : value >= 1000
                    ? `${(value / 1000).toFixed(0)}K`
                    : value.toString()
                }
              />
              <Tooltip
                formatter={(value) => [`${Number(value).toLocaleString()}人`, "人口"]}
                labelFormatter={(label) => `${label}年`}
              />
              <Legend />
              <Line
                type="monotone"
                dataKey="population"
                name="人口"
                stroke="#1a1a2e"
                strokeWidth={2}
                dot={{ fill: "#1a1a2e", strokeWidth: 2, r: 4 }}
              />
            </LineChart>
          </ResponsiveContainer>
        )}

        {activeTab === "realestate" && realEstateData && (
          <ResponsiveContainer width="100%" height={350}>
            <ComposedChart data={realEstateData.data} margin={{ top: 20, right: 30, left: 20, bottom: 20 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e0e0e0" />
              <XAxis dataKey="year" tick={{ fontSize: 12 }} tickFormatter={(value) => `${value}年`} />
              <YAxis
                yAxisId="left"
                tick={{ fontSize: 12 }}
                tickFormatter={(value) =>
                  value >= 1000000
                    ? `${(value / 1000000).toFixed(1)}M`
                    : value >= 1000
                    ? `${(value / 1000).toFixed(0)}K`
                    : `¥${value}`
                }
              />
              <YAxis
                yAxisId="right"
                orientation="right"
                tick={{ fontSize: 12 }}
                label={{ value: "件数", angle: 90, position: "insideRight", fontSize: 12 }}
              />
              <Tooltip
                formatter={(value, name) => {
                  if (name === "取引件数") return [`${Number(value).toLocaleString()}件`, name];
                  return [`¥${Number(value).toLocaleString()}/㎡`, name];
                }}
                labelFormatter={(label) => `${label}年`}
              />
              <Legend />
              <Bar
                yAxisId="right"
                dataKey="transaction_count"
                name="取引件数"
                fill="#3498db"
                opacity={0.5}
              />
              <Line
                yAxisId="left"
                type="monotone"
                dataKey="avg_unit_price"
                name="平均単価"
                stroke="#e67e22"
                strokeWidth={2}
                dot={{ fill: "#e67e22", strokeWidth: 2, r: 4 }}
              />
            </ComposedChart>
          </ResponsiveContainer>
        )}

        {activeTab === "realestate" && !realEstateData && !realEstateLoading && (
          <div className="no-data-message">
            不動産価格データがありません
          </div>
        )}
      </div>

      {/* データテーブル */}
      <div className="chart-data-table">
        <table>
          <thead>
            <tr>
              <th>年</th>
              <th>人口</th>
              <th>人口変化</th>
              {realEstateData && (
                <>
                  <th>平均単価</th>
                  <th>取引件数</th>
                </>
              )}
            </tr>
          </thead>
          <tbody>
            {combinedData.map((d, index) => {
              const prevPop = index > 0 ? combinedData[index - 1].population : null;
              const popDiff = prevPop && d.population ? d.population - prevPop : null;
              return (
                <tr key={d.year}>
                  <td>{d.year}年</td>
                  <td>{d.population?.toLocaleString() ?? "-"}人</td>
                  <td className={popDiff === null ? "" : popDiff >= 0 ? "positive" : "negative"}>
                    {popDiff === null ? "-" : `${popDiff >= 0 ? "+" : ""}${popDiff.toLocaleString()}`}
                  </td>
                  {realEstateData && (
                    <>
                      <td>{d.avg_unit_price ? `¥${d.avg_unit_price.toLocaleString()}` : "-"}</td>
                      <td>{d.transaction_count?.toLocaleString() ?? "-"}件</td>
                    </>
                  )}
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
