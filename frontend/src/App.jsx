import { useState } from "react";
import Overview from "./pages/Overview.jsx";
import MarketShare from "./pages/MarketShare.jsx";

const TABS = [
  { key: "overview", label: "Overview", component: Overview },
  { key: "market-share", label: "Provider Market Share", component: MarketShare },
];

export default function App() {
  const [tab, setTab] = useState("overview");
  const Page = TABS.find((t) => t.key === tab).component;

  return (
    <div className="app">
      <header className="topbar">
        <span className="brand">LobbyLens</span>
        <nav>
          {TABS.map((t) => (
            <button
              key={t.key}
              className={t.key === tab ? "tab active" : "tab"}
              onClick={() => setTab(t.key)}
            >
              {t.label}
            </button>
          ))}
        </nav>
      </header>
      <main>
        <Page />
      </main>
    </div>
  );
}
