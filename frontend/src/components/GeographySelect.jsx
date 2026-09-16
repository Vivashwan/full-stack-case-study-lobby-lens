import { useEffect, useState } from "react";
import { api } from "../api.js";

/**
 * Dropdown of geographies.
 * `value` is a geography id as a string ("" = none selected).
 * Pass allowAll to offer an "All geographies" option.
 */
export default function GeographySelect({ value, onChange, allowAll = false }) {
  const [options, setOptions] = useState([]);

  useEffect(() => {
    api.geographies().then(setOptions).catch(() => setOptions([]));
  }, []);

  return (
    <label className="field">
      <span>Geography</span>
      <select value={value} onChange={(e) => onChange(e.target.value)}>
        {allowAll ? <option value="">All geographies</option> : <option value="">Select…</option>}
        {options.map((g) => (
          <option key={g.id} value={String(g.id)}>
            {g.name}
          </option>
        ))}
      </select>
    </label>
  );
}
