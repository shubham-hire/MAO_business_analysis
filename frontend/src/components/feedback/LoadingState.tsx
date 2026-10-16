export function LoadingState() {
  return (
    <div className="run-list" aria-busy="true" aria-label="Loading research runs">
      {["one", "two", "three"].map((item) => (
        <div className="run-card skeleton-card" key={item}>
          <div className="skeleton skeleton-index" />
          <div className="skeleton-content">
            <div className="skeleton skeleton-title" />
            <div className="skeleton skeleton-line" />
          </div>
          <div className="skeleton skeleton-badge" />
        </div>
      ))}
    </div>
  );
}
