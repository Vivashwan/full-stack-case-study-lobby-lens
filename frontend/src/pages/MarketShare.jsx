import { useEffect, useMemo, useState } from "react";
import { api } from "../api.js";
import GeographySelect from "../components/GeographySelect.jsx";

const DEFAULT_MONTH = "2026-08";

const COLUMNS = [
  { key: "provider_name", label: "Provider", numeric: false },
  { key: "unique_games", label: "Games", numeric: true },
  { key: "unique_casinos", label: "Casinos", numeric: true },
  { key: "listings", label: "Listings", numeric: true },
  { key: "market_share_pct", label: "Share %", numeric: true },
];

function sortRows(rows, sortKey, sortDir) {
  const sorted = [...rows].sort((a, b) => {
    const av = a[sortKey];
    const bv = b[sortKey];
    if (typeof av === "string") return av.localeCompare(bv);
    return av - bv;
  });
  if (sortDir === "desc") sorted.reverse();
  return sorted;
}

function readInitialState() {
  const params = new URLSearchParams(window.location.search);
  return {
    geography: params.get("geography") ?? "",
    month: params.get("month") ?? DEFAULT_MONTH,
    nameFilter: params.get("q") ?? "",
    sortKey: params.get("sort") ?? "market_share_pct",
    sortDir: params.get("dir") === "asc" ? "asc" : "desc",
  };
}

export default function MarketShare() {
  const initial = useMemo(readInitialState, []);
  const [geography, setGeography] = useState(initial.geography);
  const [month, setMonth] = useState(initial.month);
  const [nameFilter, setNameFilter] = useState(initial.nameFilter);
  const [sortKey, setSortKey] = useState(initial.sortKey);
  const [sortDir, setSortDir] = useState(initial.sortDir);

  // Keep the selection shareable via the URL query string (nice to have).
  useEffect(() => {
    const params = new URLSearchParams();
    if (geography) params.set("geography", geography);
    if (month) params.set("month", month);
    if (nameFilter) params.set("q", nameFilter);
    if (sortKey !== "market_share_pct") params.set("sort", sortKey);
    if (sortDir !== "desc") params.set("dir", sortDir);
    const qs = params.toString();
    const url = `${window.location.pathname}${qs ? `?${qs}` : ""}`;
    window.history.replaceState(null, "", url);
  }, [geography, month, nameFilter, sortKey, sortDir]);

  const [data, setData] = useState(null);
  const [status, setStatus] = useState("idle"); // idle | loading | ready | error
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!geography || !month) {
      setData(null);
      setStatus("idle");
      return;
    }
    let cancelled = false;
    setStatus("loading");
    setError(null);
    api
      .providerMarketShare({ geography, month })
      .then((body) => {
        if (cancelled) return;
        setData(body);
        setStatus("ready");
      })
      .catch((e) => {
        if (cancelled) return;
        setError(e.message);
        setStatus("error");
      });
    return () => {
      cancelled = true;
    };
  }, [geography, month]);

  const allRows = data?.results ?? [];

  const filteredRows = useMemo(() => {
    const needle = nameFilter.trim().toLowerCase();
    if (!needle) return allRows;
    return allRows.filter((r) => r.provider_name.toLowerCase().includes(needle));
  }, [allRows, nameFilter]);

  const rows = useMemo(() => sortRows(filteredRows, sortKey, sortDir), [filteredRows, sortKey, sortDir]);

  const maxShare = useMemo(() => Math.max(1, ...allRows.map((r) => r.market_share_pct)), [allRows]);

  function toggleSort(key) {
    if (key === sortKey) {
      setSortDir((d) => (d === "desc" ? "asc" : "desc"));
    } else {
      setSortKey(key);
      setSortDir(key === "provider_name" ? "asc" : "desc");
    }
  }

  const top5Share = useMemo(
    () =>
      [...allRows]
        .sort((a, b) => b.market_share_pct - a.market_share_pct)
        .slice(0, 5)
        .reduce((sum, r) => sum + r.market_share_pct, 0),
    [allRows]
  );
  const sumOfShares = useMemo(() => allRows.reduce((sum, r) => sum + r.market_share_pct, 0), [allRows]);

  return (
    <section>
      <div className="page-head">
        <h1>Provider Market Share</h1>
        <div className="filters">
          <GeographySelect value={geography} onChange={setGeography} />
          <label className="field">
            <span>Month</span>
            <input type="month" value={month} onChange={(e) => setMonth(e.target.value)} />
          </label>
          <label className="field">
            <span>Filter provider</span>
            <input
              type="text"
              placeholder="e.g. Aurora"
              value={nameFilter}
              onChange={(e) => setNameFilter(e.target.value)}
            />
          </label>
        </div>
      </div>

      {status === "idle" && <p className="muted">Pick a geography to see its provider market share.</p>}
      {status === "loading" && <p className="muted">Loading…</p>}
      {status === "error" && <div className="error">Something went wrong: {error}</div>}

      {status === "ready" && allRows.length === 0 && (
        <p className="muted">No data for this selection.</p>
      )}

      {status === "ready" && allRows.length > 0 && (
        <>
          <table>
            <thead>
              <tr>
                {COLUMNS.map((col) => (
                  <th
                    key={col.key}
                    className={col.numeric ? "num sortable" : "sortable"}
                    onClick={() => toggleSort(col.key)}
                  >
                    {col.label}
                    {sortKey === col.key && <span className="sort-arrow">{sortDir === "desc" ? " ▼" : " ▲"}</span>}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {rows.map((r) => (
                <tr key={r.provider_id}>
                  <td>{r.provider_name}</td>
                  <td className="num">{r.unique_games}</td>
                  <td className="num">{r.unique_casinos}</td>
                  <td className="num">{r.listings}</td>
                  <td className="num">
                    <div className="share-cell">
                      <span className="share-bar-track">
                        <span
                          className="share-bar-fill"
                          style={{ width: `${(r.market_share_pct / maxShare) * 100}%` }}
                        />
                      </span>
                      <span className="share-value">{r.market_share_pct.toFixed(2)}%</span>
                    </div>
                  </td>
                </tr>
              ))}
              {rows.length === 0 && (
                <tr>
                  <td colSpan={COLUMNS.length} className="muted">
                    No providers match "{nameFilter}".
                  </td>
                </tr>
              )}
            </tbody>
          </table>

          <p className="muted footer-summary">
            {allRows.length} providers · {data.total_listings.toLocaleString()} total listings · shares sum to{" "}
            {sumOfShares.toFixed(2)}% · top 5 combined share {top5Share.toFixed(2)}%
            {rows.length !== allRows.length && ` · showing ${rows.length} matching "${nameFilter}"`}
          </p>
        </>
      )}
    </section>
  );
}
