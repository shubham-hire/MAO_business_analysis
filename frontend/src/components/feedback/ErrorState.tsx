export function ErrorState({ message, onRetry }: { message: string; onRetry: () => void }) {
  return (
    <div className="feedback-panel feedback-error" role="alert">
      <span className="feedback-icon" aria-hidden="true">!</span>
      <div>
        <h3>Research runs are unavailable</h3>
        <p>{message}</p>
        <button className="button button-dark" type="button" onClick={onRetry}>Try again</button>
      </div>
    </div>
  );
}
