interface TimeSliderProps {
  years: number[];
  selectedYear: number | null;
  onYearChange: (year: number) => void;
  loading: boolean;
}

export function TimeSlider({
  years,
  selectedYear,
  onYearChange,
  loading,
}: TimeSliderProps) {
  if (years.length === 0) {
    return null;
  }

  const minYear = Math.min(...years);
  const maxYear = Math.max(...years);

  const handleSliderChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = parseInt(e.target.value, 10);
    // スライダー値を最も近い利用可能な年に変換
    const closestYear = years.reduce((prev, curr) =>
      Math.abs(curr - value) < Math.abs(prev - value) ? curr : prev
    );
    onYearChange(closestYear);
  };

  return (
    <div className="time-slider">
      <div className="time-slider-header">
        <span className="time-slider-label">年を選択</span>
        <span className="time-slider-value">
          {selectedYear !== null ? `${selectedYear}年` : "-"}
          {loading && <span className="loading-indicator">読み込み中...</span>}
        </span>
      </div>

      <input
        type="range"
        min={minYear}
        max={maxYear}
        value={selectedYear ?? minYear}
        onChange={handleSliderChange}
        className="time-slider-input"
        disabled={loading}
      />

      <div className="time-slider-ticks">
        {years.map((year) => (
          <button
            key={year}
            className={`time-slider-tick ${
              year === selectedYear ? "active" : ""
            }`}
            onClick={() => onYearChange(year)}
            disabled={loading}
          >
            {year}
          </button>
        ))}
      </div>
    </div>
  );
}
