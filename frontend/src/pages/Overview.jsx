import { useEffect, useState } from "react";
import { api } from "../api.js";
import KpiCard from "../components/KpiCard.jsx";
import GeographySelect from "../components/GeographySelect.jsx";

const MONTH = "2026-08";

export default function Overview() {
  const [geography, setGeography] = useState("");
  const [summary, setSummary] = useState(null);
  const [casinos, setCasinos] = useState({ count: 0, results: [] });
  const [page, setPage] = useState(1);
  const [error, setError] = useState(null);

  useEffect(() => {
    api
      .summary({ month: MONTH, geography })
      .then(setSummary)
      .catch((e) => setError(e.message));
  }, [geography]);

  useEffect(() => {
    api
      .casinos({ geography, page })
      .then((data) => {
        setCasinos(data);
        setError(null);
      })
      .catch((e) => setError(e.message));
  }, [geography, page]);

  const pageCount = Math.max(1, Math.ceil(casinos.count / 20));

  // Changing geography can shrink the casino list below the page we're currently on
  // (e.g. viewing page 2 of "All geographies", then picking a small geography). Reset
  // to page 1 in the change handler itself - not in a separate effect keyed on
  // `geography` - so the casinos-fetch effect above never runs with the old page
  // number for the new geography in between.
  function handleGeographyChange(value) {
    setGeography(value);
    setPage(1);
  }

  return (
    <section>
      <div className="page-head">
        <h1>Overview · August 2026</h1>
        <GeographySelect value={geography} onChange={handleGeographyChange} allowAll />
      </div>

      {error && <div className="error">Something went wrong: {error}</div>}

      <div className="kpis">
        <KpiCard label="Scrape runs" value={summary?.total_runs} />
        <KpiCard label="Approved runs" value={summary?.approved_runs} />
        <KpiCard label="Failed runs" value={summary?.failed_runs} />
        <KpiCard label="Approval rate" value={summary?.approval_rate_pct} suffix="%" />
        <KpiCard label="Active casinos" value={summary?.active_casinos} />
      </div>

      <h2>Casinos</h2>
      <table>
        <thead>
          <tr>
            <th>Casino</th>
            <th>Operator</th>
            <th>Geography</th>
            <th>Status</th>
            <th className="num">Approved runs</th>
          </tr>
        </thead>
        <tbody>
          {casinos.results.map((c) => (
            <tr key={c.id}>
              <td>{c.name}</td>
              <td>{c.operator_name}</td>
              <td>{c.geography_name}</td>
              <td>
                <span className={c.is_active ? "pill ok" : "pill off"}>
                  {c.is_active ? "Active" : "Inactive"}
                </span>
              </td>
              <td className="num">{c.approved_runs}</td>
            </tr>
          ))}
        </tbody>
      </table>

      <div className="pager">
        <button disabled={page <= 1} onClick={() => setPage(page - 1)}>
          ← Prev
        </button>
        <span>
          Page {page} of {pageCount}
        </span>
        <button disabled={page >= pageCount} onClick={() => setPage(page + 1)}>
          Next →
        </button>
      </div>
    </section>
  );
}
