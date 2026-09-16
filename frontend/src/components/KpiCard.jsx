export default function KpiCard({ label, value, suffix = "", hint }) {
  return (
    <div className="kpi">
      <div className="kpi-label">{label}</div>
      <div className="kpi-value">
        {value === null || value === undefined ? "—" : `${value.toLocaleString()}${suffix}`}
      </div>
      {hint && <div className="kpi-hint">{hint}</div>}
    </div>
  );
}
