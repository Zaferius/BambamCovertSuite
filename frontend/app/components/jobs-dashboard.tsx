"use client";

import { useEffect, useMemo, useState } from "react";


import { authFetch } from "../lib/auth-fetch";
import { useAuth } from "../lib/auth-context";

type JobItem = {
  id: string;
  job_type: string;
  status: string;
  original_filename: string;
  output_filename?: string | null;
  error_message?: string | null;
  created_at: string;
  updated_at: string;
};


export function JobsDashboard() {
  const { user } = useAuth();
  const [jobs, setJobs] = useState<JobItem[]>([]);
  const [cleanupMessage, setCleanupMessage] = useState<string | null>(null);

  const apiBaseUrl = useMemo(
    () => process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000",
    [],
  );

  const loadJobs = async () => {
    const response = await authFetch(`${apiBaseUrl}/jobs`, { cache: "no-store" });
    if (!response.ok) {
      return;
    }
    const payload = (await response.json()) as JobItem[];
    setJobs(payload);
  };

  const getDownloadUrl = (job: JobItem) => {
    if (job.status !== "completed") {
      return null;
    }

    if (job.job_type.startsWith("batch_")) {
      return `${apiBaseUrl}/batch/jobs/${job.id}/download`;
    }

    if (job.job_type === "image") {
      return `${apiBaseUrl}/image/jobs/${job.id}/download`;
    }
    if (job.job_type === "audio") {
      return `${apiBaseUrl}/audio/jobs/${job.id}/download`;
    }
    if (job.job_type === "video") {
      return `${apiBaseUrl}/video/jobs/${job.id}/download`;
    }
    if (job.job_type === "document") {
      return `${apiBaseUrl}/document/jobs/${job.id}/download`;
    }

    return null;
  };

  useEffect(() => {
    void loadJobs();

    const interval = window.setInterval(() => {
      void loadJobs();
    }, 3000);

    return () => window.clearInterval(interval);
  }, []);

  const triggerCleanup = async () => {
    try {
      const endpoint = user?.is_admin ? `${apiBaseUrl}/admin/cleanup?older_than_hours=0` : `${apiBaseUrl}/jobs/cleanup?older_than_hours=0`;
      const response = await authFetch(endpoint, {
        method: "POST",
      });

      if (!response.ok) {
        setCleanupMessage(`Cleanup failed: server returned ${response.status}`);
        return;
      }

      const payload = (await response.json()) as { deleted_jobs?: number };
      setCleanupMessage(`Cleanup removed ${payload.deleted_jobs ?? 0} finished jobs.`);
      await loadJobs();
    } catch (err) {
      setCleanupMessage(`Cleanup failed: ${err instanceof Error ? err.message : "network error"}`);
    }
  };

  return (
    <section className="tool-card feature-card">
      <div className="dashboard-header">
        <div className="section-heading compact-heading">
          <h2>Job dashboard</h2>
          <p className="jobs-dashboard-subtitle">Live history of all conversion jobs across image, sound, video, and document modules.</p>
        </div>

        <div className="jobs-actions">
          {user?.is_admin && (
            <button className="primary-button jobs-action-button jobs-action-button-danger" type="button" onClick={async () => {
              if (!confirm("Are you sure you want to stop ALL active jobs for ALL users?")) return;
              try {
                const response = await authFetch(`${apiBaseUrl}/admin/stop-all-jobs`, { method: "POST" });
                const payload = await response.json();
                setCleanupMessage(payload.message || "All jobs stopped.");
                await loadJobs();
              } catch(e) {
                setCleanupMessage("Failed to stop all jobs.");
              }
            }}>
              Stop all jobs
            </button>
          )}
          <button className="primary-button jobs-action-button jobs-action-button-danger" type="button" onClick={async () => {
            if (!confirm("Are you sure you want to stop YOUR active jobs?")) return;
            try {
              const response = await authFetch(`${apiBaseUrl}/jobs/stop`, { method: "POST" });
              const payload = await response.json();
              setCleanupMessage(payload.message || "Your jobs stopped.");
              await loadJobs();
            } catch(e) {
              setCleanupMessage("Failed to stop jobs.");
            }
          }}>
            Stop jobs
          </button>
          <button className="primary-button jobs-action-button" type="button" onClick={triggerCleanup}>
            Cleanup finished jobs
          </button>
        </div>
      </div>

      {cleanupMessage ? <p className="selection-hint">{cleanupMessage}</p> : null}

      <div className="jobs-table-wrap">
        <table className="jobs-table">
          <thead>
            <tr>
              <th>Type</th>
              <th>Source</th>
              <th>Status</th>
              <th>Output</th>
              <th>Updated</th>
              <th>Download</th>
            </tr>
          </thead>
          <tbody>
            {jobs.length === 0 ? (
              <tr>
                <td colSpan={6}>No jobs yet.</td>
              </tr>
            ) : (
              jobs.map((job) => (
                <tr key={job.id}>
                  <td>{job.job_type}</td>
                  <td>
                    <div>{job.original_filename}</div>
                    <small>{job.id}</small>
                  </td>
                  <td>{job.status}</td>
                  <td>{job.output_filename ?? job.error_message ?? "—"}</td>
                  <td>{new Date(job.updated_at).toLocaleString()}</td>
                  <td>
                    {getDownloadUrl(job) ? (
                      <button
                        className="primary-button"
                        style={{ padding: "6px 10px", fontSize: "0.78rem" }}
                        type="button"
                        onClick={() => {
                          const url = getDownloadUrl(job);
                          if (!url) return;
                          window.open(url, "_blank", "noopener,noreferrer");
                        }}
                      >
                        Download
                      </button>
                    ) : (
                      <span style={{ color: "var(--muted)" }}>—</span>
                    )}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </section>
  );
}
