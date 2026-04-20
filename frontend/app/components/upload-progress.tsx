"use client";

import { useState } from "react";

export type FileUploadItem = { name: string; pct: number };

const COLLAPSE_THRESHOLD = 5;

type Props = {
  files: FileUploadItem[];
};

export function UploadProgressPanel({ files }: Props) {
  const [expanded, setExpanded] = useState(true);

  if (files.length === 0) return null;

  const hasMany = files.length > COLLAPSE_THRESHOLD;
  const overallPct = Math.round(
    files.reduce((sum, f) => sum + f.pct, 0) / files.length,
  );

  return (
    <div className="upload-progress-panel">
      <div className="upload-progress-header">
        <span className="upload-progress-dot" />
        <span className="upload-progress-heading">
          Uploading{files.length > 1 ? ` ${files.length} files` : ""}…
        </span>
        <span className="upload-progress-overall-pct">{overallPct}%</span>
        {!hasMany && (
          <div className="upload-progress-overall-track">
            <div className="upload-progress-overall-fill" style={{ width: `${overallPct}%` }} />
          </div>
        )}
      </div>

      {hasMany && (
        <button
          type="button"
          className="upload-progress-toggle"
          onClick={() => setExpanded((v) => !v)}
        >
          <span className="upload-progress-toggle-icon">{expanded ? "▲" : "▼"}</span>
          <span>
            {files.length} files uploading
          </span>
          <span className="upload-progress-overall-pct">{overallPct}%</span>
          <div className="upload-progress-overall-track">
            <div
              className="upload-progress-overall-fill"
              style={{ width: `${overallPct}%` }}
            />
          </div>
        </button>
      )}

      {(!hasMany || expanded) && (
        <ul className="upload-progress-list">
          {files.map((f) => (
            <li key={f.name} className="upload-progress-item">
              <div className="upload-progress-info">
                <span className="upload-progress-name" title={f.name}>
                  {f.name}
                </span>
                <span className="upload-progress-pct">{f.pct}%</span>
              </div>
              <div className="upload-progress-track">
                <div
                  className={`upload-progress-fill${f.pct >= 100 ? " upload-progress-fill--done" : ""}`}
                  style={{ width: `${f.pct}%` }}
                />
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
