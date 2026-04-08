"use client";

import { useEffect, useState, useMemo } from "react";
import { authFetch } from "../lib/auth-fetch";

type ActiveUser = {
  username: string;
  is_admin: boolean;
  action: string;
  last_seen: number;
};

type StoredFile = {
  source: "outputs" | "uploads";
  name: string;
  relative_path: string;
  size: number;
  modified_at: string;
};

export function AdminPanel() {
  const [isOpen, setIsOpen] = useState(false);
  const [activeUsers, setActiveUsers] = useState<ActiveUser[]>([]);
  const [source, setSource] = useState<"outputs" | "uploads">("outputs");
  const [files, setFiles] = useState<StoredFile[]>([]);
  const [isLoadingFiles, setIsLoadingFiles] = useState(false);

  const apiBaseUrl = useMemo(
    () => process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000",
    []
  );

  useEffect(() => {
    if (!isOpen) return;

    const fetchUsers = async () => {
      try {
        const res = await authFetch(`${apiBaseUrl}/auth/online-users`);
        if (res.ok) {
          const data = await res.json();
          setActiveUsers(data);
        }
      } catch (err) {}
    };

    fetchUsers();
    const interval = setInterval(fetchUsers, 3000);
    return () => clearInterval(interval);
  }, [isOpen, apiBaseUrl]);

  const fetchFiles = async (activeSource: "outputs" | "uploads") => {
    setIsLoadingFiles(true);
    try {
      const res = await authFetch(`${apiBaseUrl}/admin/files?source=${activeSource}&limit=300`);
      if (res.ok) {
        const data = (await res.json()) as StoredFile[];
        setFiles(data);
      }
    } catch {
      setFiles([]);
    } finally {
      setIsLoadingFiles(false);
    }
  };

  useEffect(() => {
    if (!isOpen) return;
    void fetchFiles(source);
  }, [isOpen, source]);

  const handleDelete = async (file: StoredFile) => {
    const ok = window.confirm(`Delete ${file.name}?`);
    if (!ok) return;
    const url = `${apiBaseUrl}/admin/files?source=${file.source}&path=${encodeURIComponent(file.relative_path)}`;
    const res = await authFetch(url, { method: "DELETE" });
    if (res.ok) {
      setFiles((prev) => prev.filter((f) => !(f.source === file.source && f.relative_path === file.relative_path)));
    }
  };

  const formatSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    if (bytes < 1024 * 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
    return `${(bytes / (1024 * 1024 * 1024)).toFixed(2)} GB`;
  };

  return (
    <div className="admin-panel-wrapper">
      <button 
        className="admin-panel-toggle" 
        onClick={() => setIsOpen(!isOpen)}
        title="Admin Panel: Active Users"
      >
        <span style={{ fontSize: "16px" }}>👥</span> 
        Admin Panel
      </button>

      {isOpen && (
        <div className="admin-panel-dropdown">
          <div className="admin-panel-header">
            <h4>Active Users</h4>
          </div>
          {activeUsers.length === 0 ? (
            <p className="admin-empty">No active users</p>
          ) : (
            <ul className="admin-user-list">
              {activeUsers.map((u) => {
                const isIdle = u.action === "idle";
                return (
                  <li key={u.username} className="admin-user-item">
                    <div className="admin-user-info">
                      <span className="admin-user-name">
                        {u.username} {u.is_admin ? "👑" : ""}
                      </span>
                      <div className={`status-dot ${isIdle ? "dot-idle" : "dot-active"}`} />
                    </div>
                    <span className="admin-user-action">
                      {isIdle ? "Idle" : `Processing: ${u.action}`}
                    </span>
                  </li>
                );
              })}
            </ul>
          )}

          <div className="admin-panel-header" style={{ borderTop: "1px solid var(--border)" }}>
            <h4>Stored Files</h4>
          </div>

          <div style={{ display: "flex", gap: 8, padding: "10px 12px" }}>
            <button
              className="admin-panel-toggle"
              style={{ padding: "4px 10px", fontSize: "0.8rem", background: source === "outputs" ? "rgba(180,77,255,0.3)" : "rgba(180,77,255,0.12)" }}
              onClick={() => setSource("outputs")}
            >
              Outputs
            </button>
            <button
              className="admin-panel-toggle"
              style={{ padding: "4px 10px", fontSize: "0.8rem", background: source === "uploads" ? "rgba(180,77,255,0.3)" : "rgba(180,77,255,0.12)" }}
              onClick={() => setSource("uploads")}
            >
              Uploads
            </button>
          </div>

          {isLoadingFiles ? (
            <p className="admin-empty">Loading files...</p>
          ) : files.length === 0 ? (
            <p className="admin-empty">No files found</p>
          ) : (
            <ul className="admin-user-list">
              {files.map((f) => {
                const viewUrl = `${apiBaseUrl}/admin/files/view?source=${f.source}&path=${encodeURIComponent(f.relative_path)}`;
                return (
                  <li key={`${f.source}:${f.relative_path}`} className="admin-user-item">
                    <div className="admin-user-info" style={{ alignItems: "flex-start" }}>
                      <span className="admin-user-name" style={{ fontSize: "0.84rem", maxWidth: 180, overflow: "hidden", textOverflow: "ellipsis" }} title={f.relative_path}>
                        {f.name}
                      </span>
                      <span style={{ color: "var(--muted)", fontSize: "0.72rem" }}>{formatSize(f.size)}</span>
                    </div>
                    <span className="admin-user-action">{new Date(f.modified_at).toLocaleString()}</span>
                    <div style={{ display: "flex", gap: 8, marginTop: 8 }}>
                      <a className="admin-panel-toggle" style={{ padding: "4px 10px", fontSize: "0.76rem" }} href={viewUrl} target="_blank" rel="noreferrer">
                        View
                      </a>
                      <button
                        className="admin-panel-toggle"
                        style={{ padding: "4px 10px", fontSize: "0.76rem", borderColor: "#f87171", color: "#fca5a5" }}
                        onClick={() => void handleDelete(f)}
                      >
                        Delete
                      </button>
                    </div>
                  </li>
                );
              })}
            </ul>
          )}
        </div>
      )}
    </div>
  );
}
