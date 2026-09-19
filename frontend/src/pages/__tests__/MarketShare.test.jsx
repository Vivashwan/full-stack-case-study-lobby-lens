import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import "@testing-library/jest-dom";

import { api } from "../../api.js";
import MarketShare from "../MarketShare.jsx";

vi.mock("../../api.js", () => ({
  api: {
    geographies: vi.fn(),
    providerMarketShare: vi.fn(),
  },
}));

const GEOGRAPHIES = [{ id: 1, name: "United Kingdom" }];

const MARKET_SHARE_BODY = {
  geography: { id: 1, name: "United Kingdom" },
  month: "2026-08",
  total_listings: 100,
  results: [
    { provider_id: 1, provider_name: "Aurora Play", unique_games: 10, unique_casinos: 5, listings: 60, market_share_pct: 60 },
    { provider_id: 2, provider_name: "Blue Harbor Games", unique_games: 4, unique_casinos: 3, listings: 40, market_share_pct: 40 },
  ],
};

beforeEach(() => {
  window.history.replaceState(null, "", "/");
  api.geographies.mockResolvedValue(GEOGRAPHIES);
  api.providerMarketShare.mockResolvedValue(MARKET_SHARE_BODY);
});

async function renderAndPickGeography() {
  render(<MarketShare />);
  await screen.findByText("Pick a geography to see its provider market share.");
  fireEvent.change(screen.getByRole("combobox"), { target: { value: "1" } });
}

describe("MarketShare page", () => {
  it("shows the idle state before a geography is picked", async () => {
    render(<MarketShare />);
    expect(await screen.findByText("Pick a geography to see its provider market share.")).toBeInTheDocument();
  });

  it("renders the table sorted by share % descending by default", async () => {
    await renderAndPickGeography();
    const rows = await screen.findAllByRole("row");
    // rows[0] is the header row
    expect(rows[1]).toHaveTextContent("Aurora Play");
    expect(rows[2]).toHaveTextContent("Blue Harbor Games");
  });

  it("reverses the order when the same column header is clicked twice", async () => {
    await renderAndPickGeography();
    await screen.findByText("Aurora Play");

    const shareHeader = screen.getByText("Share %");
    fireEvent.click(shareHeader); // ascending now
    let rows = screen.getAllByRole("row");
    expect(rows[1]).toHaveTextContent("Blue Harbor Games");

    fireEvent.click(shareHeader); // back to descending
    rows = screen.getAllByRole("row");
    expect(rows[1]).toHaveTextContent("Aurora Play");
  });

  it("shows the empty state when the endpoint returns no results", async () => {
    api.providerMarketShare.mockResolvedValueOnce({ geography: { id: 1, name: "UK" }, month: "2020-01", total_listings: 0, results: [] });
    await renderAndPickGeography();
    expect(await screen.findByText("No data for this selection.")).toBeInTheDocument();
  });

  it("shows the error state when the endpoint fails", async () => {
    api.providerMarketShare.mockRejectedValueOnce(new Error("boom"));
    await renderAndPickGeography();
    expect(await screen.findByText(/Something went wrong: boom/)).toBeInTheDocument();
  });

  it("filters rows by provider name", async () => {
    await renderAndPickGeography();
    await screen.findByText("Aurora Play");

    fireEvent.change(screen.getByPlaceholderText("e.g. Aurora"), { target: { value: "blue" } });

    await waitFor(() => expect(screen.queryByText("Aurora Play")).not.toBeInTheDocument());
    expect(screen.getByText("Blue Harbor Games")).toBeInTheDocument();
  });

  it("includes a sanity-check summary line with total listings and share sum", async () => {
    await renderAndPickGeography();
    expect(await screen.findByText(/100 total listings/)).toBeInTheDocument();
    expect(screen.getByText(/shares sum to 100.00%/)).toBeInTheDocument();
  });
});
