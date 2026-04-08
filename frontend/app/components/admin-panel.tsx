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
  owner_username?: string;
};

export function AdminPanel() {
  const [isOpen, setIsOpen] = useState(false);
  const [isStoredFilesOpen, setIsStoredFilesOpen] = useState(false);
  const [isBotSettingsOpen, setIsBotSettingsOpen] = useState(false);
  const [activeUsers, setActiveUsers] = useState<ActiveUser[]>([]);
  const [source, setSource] = useState<"outputs" | "uploads">("outputs");
  const [files, setFiles] = useState<StoredFile[]>([]);
  const [isLoadingFiles, setIsLoadingFiles] = useState(false);
  const [botToken, setBotToken] = useState("");
  const [botEnabled, setBotEnabled] = useState(false);
  const [botHasToken, setBotHasToken] = useState(false);
  const [botSaveLoading, setBotSaveLoading] = useState(false);

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

  const fetchBotSettings = async () => {
    try {
      const res = await authFetch(`${apiBaseUrl}/admin/bot-settings`);
      if (res.ok) {
        const data = (await res.json()) as any;
        setBotEnabled(data.bot_enabled ?? false);
        setBotHasToken(data.has_token ?? false);
        setBotToken(""); // Clear input field
      }
    } catch (err) {}
  };

  const handleSaveBotSettings = async () => {
    setBotSaveLoading(true);
    try {
      const payload: any = { bot_enabled: botEnabled };
      if (botToken.trim()) {
        payload.telegram_bot_token = botToken;
      }

      const res = await authFetch(`${apiBaseUrl}/admin/bot-settings`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (res.ok) {
        const result = await res.json();
        setBotToken("");
        setBotHasToken(result.has_token);
        setBotEnabled(result.bot_enabled);
      }
    } catch (err) {
    } finally {
      setBotSaveLoading(false);
    }
  };

  useEffect(() => {
    if (!isOpen || !isStoredFilesOpen) return;
    void fetchFiles(source);
  }, [isOpen, source, isStoredFilesOpen]);

  useEffect(() => {
    if (!isOpen || !isBotSettingsOpen) return;
    void fetchBotSettings();
  }, [isOpen, isBotSettingsOpen]);

  const handleDelete = async (file: StoredFile) => {
    const ok = window.confirm(`Delete ${file.name}?`);
    if (!ok) return;
    const url = `${apiBaseUrl}/admin/files?source=${file.source}&path=${encodeURIComponent(file.relative_path)}`;
    const res = await authFetch(url, { method: "DELETE" });
    if (res.ok) {
      setFiles((prev) => prev.filter((f) => !(f.source === file.source && f.relative_path === file.relative_path)));
    }
  };

  const handleView = async (file: StoredFile) => {
    const url = `${apiBaseUrl}/admin/files/view?source=${file.source}&path=${encodeURIComponent(file.relative_path)}`;
    const res = await authFetch(url);
    if (!res.ok) {
      return;
    }
    const blob = await res.blob();
    const blobUrl = URL.createObjectURL(blob);
    window.open(blobUrl, "_blank", "noopener,noreferrer");
    window.setTimeout(() => URL.revokeObjectURL(blobUrl), 60_000);
  };

  const handleDeleteAllFiles = async () => {
    const ok = window.confirm("Delete ALL stored files from uploads and outputs?");
    if (!ok) return;

    const res = await authFetch(`${apiBaseUrl}/admin/files/all`, { method: "DELETE" });
    if (!res.ok) {
      return;
    }

    setFiles([]);
    if (isStoredFilesOpen) {
      void fetchFiles(source);
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

          <div className="admin-panel-header" style={{ borderTop: "1px solid var(--border)", display: "flex", alignItems: "center", justifyContent: "space-between", gap: 8 }}>
            <h4>Storage</h4>
            <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <button
                className="admin-panel-toggle"
                style={{ padding: "4px 10px", fontSize: "0.76rem", borderColor: "#f87171", color: "#fca5a5" }}
                onClick={() => void handleDeleteAllFiles()}
              >
                Delete All
              </button>
              <button
                className="admin-panel-toggle"
                style={{ padding: "4px 10px", fontSize: "0.76rem" }}
                onClick={() => setIsStoredFilesOpen((prev) => !prev)}
              >
                {isStoredFilesOpen ? "Hide Stored Files" : "Show Stored Files"}
              </button>
            </div>
          </div>

          {isStoredFilesOpen && (
            <>
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
                    return (
                      <li key={`${f.source}:${f.relative_path}`} className="admin-user-item">
                        <div className="admin-user-info" style={{ alignItems: "flex-start" }}>
                          <span className="admin-user-name" style={{ fontSize: "0.84rem", maxWidth: 180, overflow: "hidden", textOverflow: "ellipsis" }} title={f.relative_path}>
                            {f.name}
                          </span>
                          <span style={{ color: "var(--muted)", fontSize: "0.72rem" }}>{formatSize(f.size)}</span>
                        </div>
                        <span className="admin-user-action">{new Date(f.modified_at).toLocaleString()}</span>
                        <span className="admin-user-action">Owner: {f.owner_username ?? "Unknown"}</span>
                        <div style={{ display: "flex", gap: 8, marginTop: 8 }}>
                          <button
                            className="admin-panel-toggle"
                            style={{ padding: "4px 10px", fontSize: "0.76rem" }}
                            onClick={() => void handleView(f)}
                          >
                            View
                          </button>
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
            </>
          )}

          <div className="admin-panel-header" style={{ borderTop: "1px solid var(--border)", display: "flex", alignItems: "center", justifyContent: "space-between", gap: 8 }}>
            <h4>🤖 Bot Settings</h4>
            <button
              className="admin-panel-toggle"
              style={{ padding: "4px 10px", fontSize: "0.76rem" }}
              onClick={() => setIsBotSettingsOpen((prev) => !prev)}
            >
              {isBotSettingsOpen ? "Hide" : "Show"}
            </button>
          </div>

          {isBotSettingsOpen && (
            <div style={{ padding: "12px", display: "flex", flexDirection: "column", gap: 12 }}>
              <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                <span style={{ fontSize: "0.85rem", flex: 1 }}>Bot Enabled: {botEnabled ? "✓" : "✗"}</span>
                <span style={{ fontSize: "0.85rem", flex: 1 }}>Token: {botHasToken ? "✓" : "Not configured"}</span>
              </div>

              <div>
                <label style={{ display: "block", fontSize: "0.8rem", marginBottom: 4, color: "var(--muted)" }}>
                  Telegram Bot Token
                </label>
                <input
                  type="password"
                  placeholder="Paste your Telegram bot token from @BotFather"
                  value={botToken}
                  onChange={(e) => setBotToken(e.target.value)}
                  style={{
                    width: "100%",
                    padding: "8px",
                    fontSize: "0.85rem",
                    background: "rgba(0,0,0,0.2)",
                    border: "1px solid var(--border)",
                    borderRadius: "4px",
                    color: "inherit",
                    fontFamily: "monospace",
                  }}
                />
                <p style={{ fontSize: "0.75rem", marginTop: 4, color: "var(--muted)" }}>
                  Leave empty to keep current token
                </p>
              </div>

              <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                <label style={{ display: "flex", alignItems: "center", gap: 6, cursor: "pointer" }}>
                  <input
                    type="checkbox"
                    checked={botEnabled}
                    onChange={(e) => setBotEnabled(e.target.checked)}
                    style={{ cursor: "pointer" }}
                  />
                  <span style={{ fontSize: "0.85rem" }}>Bot Enabled</span>
                </label>
              </div>

              <button
                className="admin-panel-toggle"
                onClick={() => void handleSaveBotSettings()}
                disabled={botSaveLoading}
                style={{
                  padding: "8px 16px",
                  fontSize: "0.85rem",
                  opacity: botSaveLoading ? 0.5 : 1,
                  cursor: botSaveLoading ? "not-allowed" : "pointer",
                }}
              >
                {botSaveLoading ? "Saving..." : "Save Bot Settings"}
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
