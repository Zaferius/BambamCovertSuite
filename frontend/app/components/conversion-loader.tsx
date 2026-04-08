"use client";

type Props = {
  isVisible: boolean;
  jobStatus?: string | null;
};

const statusLabels: Record<string, string> = {
  queued: "Queued...",
  processing: "Working...",
  completed: "Completed!",
  failed: "Error",
};

export function ConversionLoader({ isVisible, jobStatus }: Props) {
  if (!isVisible) return null;

  const label = jobStatus ? (statusLabels[jobStatus] ?? jobStatus) : "Uploading...";
  const isDone = jobStatus === "completed";
  const isFailed = jobStatus === "failed";

  return (
    <div className={`conversion-loader${isDone ? " conversion-loader--done" : isFailed ? " conversion-loader--failed" : ""}`}>
      <div className="conversion-loader-inner">
        {!isDone && !isFailed ? (
          <div className="conversion-spinner" />
        ) : isDone ? (
          <div className="conversion-done-icon">✓</div>
        ) : (
          <div className="conversion-fail-icon">✕</div>
        )}
        <span className="conversion-loader-label">{label}</span>
      </div>
    </div>
  );
}
