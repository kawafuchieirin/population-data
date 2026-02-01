import { useMemo, useState } from "react";
import type { MunicipalityListItem } from "../types/population";

interface MunicipalitySearchProps {
  municipalities: MunicipalityListItem[];
  onSelect: (code: string) => void;
  selectedCode: string | null;
}

export function MunicipalitySearch({
  municipalities,
  onSelect,
  selectedCode,
}: MunicipalitySearchProps) {
  const [searchText, setSearchText] = useState("");
  const [isOpen, setIsOpen] = useState(false);

  const filteredMunicipalities = useMemo(() => {
    if (!searchText) return municipalities.slice(0, 50);

    const lower = searchText.toLowerCase();
    return municipalities
      .filter(
        (m) =>
          m.municipality.toLowerCase().includes(lower) ||
          m.prefecture.toLowerCase().includes(lower) ||
          m.code.includes(searchText)
      )
      .slice(0, 50);
  }, [municipalities, searchText]);

  const selectedMunicipality = useMemo(() => {
    if (!selectedCode) return null;
    return municipalities.find((m) => m.code === selectedCode);
  }, [municipalities, selectedCode]);

  return (
    <div className="municipality-search">
      <label className="search-label">市区町村を検索</label>
      <div className="search-input-wrapper">
        <input
          type="text"
          className="search-input"
          placeholder="市区町村名または都道府県名..."
          value={searchText}
          onChange={(e) => {
            setSearchText(e.target.value);
            setIsOpen(true);
          }}
          onFocus={() => setIsOpen(true)}
        />
        {isOpen && filteredMunicipalities.length > 0 && (
          <div className="search-dropdown">
            {filteredMunicipalities.map((m) => (
              <button
                key={m.code}
                className={`search-item ${
                  m.code === selectedCode ? "selected" : ""
                }`}
                onClick={() => {
                  onSelect(m.code);
                  setSearchText("");
                  setIsOpen(false);
                }}
              >
                <span className="search-item-name">
                  {m.prefecture} {m.municipality}
                </span>
                <span className="search-item-code">{m.code}</span>
              </button>
            ))}
          </div>
        )}
      </div>

      {selectedMunicipality && (
        <div className="selected-municipality">
          <span>
            選択中: {selectedMunicipality.prefecture}{" "}
            {selectedMunicipality.municipality}
          </span>
        </div>
      )}

      {isOpen && (
        <div className="search-overlay" onClick={() => setIsOpen(false)} />
      )}
    </div>
  );
}
