"use client";

import { useEffect, useMemo, useState } from "react";


import { authFetch } from "../lib/auth-fetch";

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

  useEffect(() => {
    void loadJobs();

    const interval = window.setInterval(() => {
      void loadJobs();
    }, 3000);

    return () => window.clearInterval(interval);
  }, []);

  const triggerCleanup = async () => {
    try {
      const response = await authFetch(`${apiBaseUrl}/admin/cleanup?older_than_hours=0`, {
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
          <p>Live history of all conversion jobs across image, sound, video, and document modules.</p>
        </div>

        <div style={{ display: "flex", gap: "10px" }}>
          <button className="primary-button" style={{ background: "transparent", borderColor: "#f87171", color: "#f87171" }} type="button" onClick={async () => {
            if (!confirm("Are you sure you want to stop all active jobs?")) return;
            try {
              const response = await authFetch(`${apiBaseUrl}/admin/stop-all-jobs`, { method: "POST" });
              const payload = await response.json();
              setCleanupMessage(payload.message || "Jobs stopped.");
              await loadJobs();
            } catch(e) {
              setCleanupMessage("Failed to stop jobs.");
            }
          }}>
            Stop all jobs
          </button>
          <button className="primary-button" type="button" onClick={triggerCleanup}>
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
            </tr>
          </thead>
          <tbody>
            {jobs.length === 0 ? (
              <tr>
                <td colSpan={5}>No jobs yet.</td>
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
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </section>
  );
}
