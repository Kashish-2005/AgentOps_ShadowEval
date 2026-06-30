interface HeaderProps {
  runCount: number;
  backendOnline: boolean;
}

export function Header({ runCount, backendOnline }: HeaderProps) {
  return (
    <header className="app-header">
      <div className="app-header__left">
        <div className="app-header__brand">
          <span className="app-header__name mono">AgentOps</span>
          <span className="app-header__accent mono">ShadowEval</span>
        </div>
        <span className="app-header__version mono">v1.0.0</span>
      </div>
      <div className="app-header__right">
        <div className="app-header__status">
          <span
            className={`status-dot ${backendOnline ? "status-dot--online" : "status-dot--offline"}`}
            aria-label={backendOnline ? "Backend online" : "Backend offline"}
          />
          <span className="status-label">
            {backendOnline ? "Backend Online" : "Backend Offline"}
          </span>
        </div>
        <div className="app-header__divider" aria-hidden="true" />
        <span className="app-header__runs mono">
          {runCount} {runCount === 1 ? "run" : "runs"}
        </span>
      </div>
    </header>
  );
}