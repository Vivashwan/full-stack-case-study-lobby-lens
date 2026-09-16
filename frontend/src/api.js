// Small fetch wrapper. All API calls go through here.

export class ApiError extends Error {
  constructor(status, detail) {
    super(detail || `Request failed with status ${status}`);
    this.status = status;
  }
}

export async function getJSON(path, params = {}) {
  const qs = new URLSearchParams(
    Object.entries(params).filter(([, v]) => v !== undefined && v !== null && v !== "")
  ).toString();
  const res = await fetch(`/api${path}${qs ? `?${qs}` : ""}`);
  let body = null;
  try {
    body = await res.json();
  } catch {
    // non-JSON response (e.g. Django debug page)
  }
  if (!res.ok) throw new ApiError(res.status, body?.detail);
  return body;
}

export const api = {
  geographies: () => getJSON("/geographies/"),
  casinos: (params) => getJSON("/casinos/", params),
  summary: (params) => getJSON("/summary/", params),
  providerMarketShare: (params) => getJSON("/provider-market-share/", params),
};
