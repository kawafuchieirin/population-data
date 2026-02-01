import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";
import type { MunicipalityTimeSeries } from "../types/population";

interface PopulationChartProps {
  data: MunicipalityTimeSeries;
  onClose: () => void;
}

export function PopulationChart({ data, onClose }: PopulationChartProps) {
  const chartData = data.data.map((d) => ({
    year: d.year,
    population: d.population,
    label: `${d.year}年`,
  }));

  // 人口の変化を計算
  const firstYear = data.data[0];
  const lastYear = data.data[data.data.length - 1];
  const change = lastYear.population - firstYear.population;
  const changePercent = ((change / firstYear.population) * 100).toFixed(1);

  return (
    <div className="population-chart-container">
      <div className="chart-header">
        <div className="chart-title">
          <h3>
            {data.prefecture} {data.municipality}
          </h3>
          <span className="chart-subtitle">人口推移（{firstYear.year}年〜{lastYear.year}年）</span>
        </div>
        <button className="chart-close" onClick={onClose}>
          ×
        </button>
      </div>

      <div className="chart-stats">
        <div className="stat-item">
          <span className="stat-label">{firstYear.year}年</span>
          <span className="stat-value">
            {firstYear.population.toLocaleString()}人
          </span>
        </div>
        <div className="stat-arrow">→</div>
        <div className="stat-item">
          <span className="stat-label">{lastYear.year}年</span>
          <span className="stat-value">
            {lastYear.population.toLocaleString()}人
          </span>
        </div>
        <div className="stat-item">
          <span className="stat-label">変化</span>
          <span
            className={`stat-value ${change >= 0 ? "positive" : "negative"}`}
          >
            {change >= 0 ? "+" : ""}
            {change.toLocaleString()}人 ({change >= 0 ? "+" : ""}
            {changePercent}%)
          </span>
        </div>
      </div>

      <div className="chart-wrapper">
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={chartData} margin={{ top: 20, right: 30, left: 20, bottom: 20 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e0e0e0" />
            <XAxis
              dataKey="year"
              tick={{ fontSize: 12 }}
              tickFormatter={(value) => `${value}年`}
            />
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
              formatter={(value) => [
                `${Number(value).toLocaleString()}人`,
                "人口",
              ]}
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
              activeDot={{ r: 6 }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      <div className="chart-data-table">
        <table>
          <thead>
            <tr>
              <th>年</th>
              <th>人口</th>
              <th>前回比</th>
            </tr>
          </thead>
          <tbody>
            {data.data.map((d, index) => {
              const prevPopulation =
                index > 0 ? data.data[index - 1].population : null;
              const diff = prevPopulation
                ? d.population - prevPopulation
                : null;
              return (
                <tr key={d.year}>
                  <td>{d.year}年</td>
                  <td>{d.population.toLocaleString()}人</td>
                  <td
                    className={
                      diff === null ? "" : diff >= 0 ? "positive" : "negative"
                    }
                  >
                    {diff === null
                      ? "-"
                      : `${diff >= 0 ? "+" : ""}${diff.toLocaleString()}`}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
