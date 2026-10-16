import type { ReactNode } from "react";

type AppShellProps = {
  children: ReactNode;
  currentView?: "runs" | "new-run" | "run-detail";
  onNavigateRuns?: () => void;
  onNavigateNewRun?: () => void;
};

export function AppShell({ children, currentView = "runs", onNavigateRuns, onNavigateNewRun }: AppShellProps) {
  return (
    <div className="app-shell">
      <header className="topbar">
        <a className="brand" href="/" aria-label="Tracer landing page">
          <span className="brand-mark" aria-hidden="true">TR</span>
          <span>Tracer<br /><em>Market evidence</em></span>
        </a>
        <nav className="main-nav" aria-label="Main navigation">
          <a className={`nav-link ${currentView !== "new-run" ? "nav-link-active" : ""}`} href="/runs" onClick={(event) => { event.preventDefault(); onNavigateRuns?.(); }}>Runs</a>
          <a className={`nav-link ${currentView === "new-run" ? "nav-link-active" : ""}`} href="/runs/new" onClick={(event) => { event.preventDefault(); onNavigateNewRun?.(); }}>New run</a>
        </nav>
        <button className="account-button" type="button" aria-label="Open account menu">
          <span className="avatar">SH</span>
          <span className="account-name">Shubham</span>
          <span className="chevron" aria-hidden="true">⌄</span>
        </button>
      </header>
      {children}
    </div>
  );
}
