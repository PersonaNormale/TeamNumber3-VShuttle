type ConfidenceBarProps = {
  value: number;
};

export function ConfidenceBar({ value }: ConfidenceBarProps) {
  const percentage = Math.max(0, Math.min(100, Math.round(value * 100)));
  const toneClass = percentage >= 80 ? "is-high" : percentage >= 50 ? "is-medium" : "is-low";

  return (
    <div className="confidence-wrap" aria-label={`Confidenza ${percentage}%`}>
      <div className="confidence-track">
        <div className={`confidence-fill ${toneClass}`} style={{ width: `${percentage}%` }} />
      </div>
      <strong>{percentage}%</strong>
    </div>
  );
}
