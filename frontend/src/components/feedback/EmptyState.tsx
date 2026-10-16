export function EmptyState({ onStartNewRun }: { onStartNewRun?: () => void }) {
  return (
    <div className="empty-state">
      <div className="empty-orbit" aria-hidden="true"><span>+</span></div>
      <div>
        <div className="section-marker section-marker-dark">NO SNAPSHOTS YET</div>
        <h3>Start with a product question.</h3>
        <p>Define the product, confirm its market, then review evidence you can open and verify.</p>
        <button className="button button-dark" type="button" onClick={onStartNewRun}>Start your first run <span aria-hidden="true">↗</span></button>
      </div>
      <ol className="empty-steps">
        <li><span>01</span> Define the product</li>
        <li><span>02</span> Confirm the market</li>
        <li><span>03</span> Review the evidence</li>
      </ol>
    </div>
  );
}
