import type { ReactNode } from "react";

type AppShellProps = {
  children: ReactNode;
  onNavigateNewRun?: () => void;
};

export function AppShell({ children, onNavigateNewRun }: AppShellProps) {
  return (
    <div className="app-shell">
      <header className="topbar">
        <a className="brand" href="/" aria-label="Market Feasibility Intelligence home">
          <span className="brand-mark" aria-hidden="true">MF</span>
          <span>Market Feasibility<br /><em>Intelligence</em></span>
        </a>
        <nav className="main-nav" aria-label="Main navigation">
          <a className="nav-link nav-link-active" href="#runs">Runs</a>
          <a className="nav-link" href="#new-run" onClick={onNavigateNewRun}>New run</a>
          <a className="nav-link" href="#admin">Admin</a>
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
