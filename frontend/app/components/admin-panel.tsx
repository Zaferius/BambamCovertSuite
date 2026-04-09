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

type ActiveBot = {
  id: number;
  user_id: number | null;
  username: string;
  has_token: boolean;
  bot_enabled: boolean;
  updated_at: string;
};

type AdminPanelProps = {
  isOpen: boolean;
  setIsOpen: (open: boolean) => void;
};

type SubView = "users" | "storage" | "bot-settings";

const menuItems: Array<{ key: SubView; label: string; icon: string }> = [
  { key: "users", label: "Users", icon: "👥" },
  { key: "storage", label: "Storage", icon: "🗂️" },
  { key: "bot-settings", label: "Telegram Bot Settings", icon: "🤖" },
];

export function AdminPanel({ isOpen, setIsOpen }: AdminPanelProps) {
  const [activeSubView, setActiveSubView] = useState<SubView | null>(null);
  const [activeUsers, setActiveUsers] = useState<ActiveUser[]>([]);
  const [activeBots, setActiveBots] = useState<ActiveBot[]>([]);
  const [source, setSource] = useState<"outputs" | "uploads">("outputs");
  const [files, setFiles] = useState<StoredFile[]>([]);
  const [isLoadingFiles, setIsLoadingFiles] = useState(false);
  const [isLoadingBots, setIsLoadingBots] = useState(false);
  const [botToken, setBotToken] = useState("");
  const [botEnabled, setBotEnabled] = useState(false);
  const [botHasToken, setBotHasToken] = useState(false);
  const [botSaveLoading, setBotSaveLoading] = useState(false);

  const apiBaseUrl = useMemo(
    () => process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000",
    []
  );

  useEffect(() => {
    if (!isOpen || activeSubView !== "users") return;

    const fetchUsers = async () => {
      try {
        const res = await authFetch(`${apiBaseUrl}/auth/online-users`);
        if (res.ok) setActiveUsers(await res.json());
      } catch {}
    };

    fetchUsers();
    const interval = setInterval(fetchUsers, 3000);
    return () => clearInterval(interval);
  }, [isOpen, activeSubView, apiBaseUrl]);

  const fetchFiles = async (activeSource: "outputs" | "uploads") => {
    setIsLoadingFiles(true);
    try {
      const res = await authFetch(`${apiBaseUrl}/admin/files?source=${activeSource}&limit=300`);
      if (res.ok) setFiles((await res.json()) as StoredFile[]);
      else setFiles([]);
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
        const data = await res.json();
        setBotEnabled(data.bot_enabled ?? false);
        setBotHasToken(data.has_token ?? false);
        setBotToken("");
      }
    } catch {}
  };

  const fetchActiveBots = async () => {
    setIsLoadingBots(true);
    try {
      const res = await authFetch(`${apiBaseUrl}/admin/bot-settings/active`);
      if (res.ok) setActiveBots((await res.json()) as ActiveBot[]);
      else setActiveBots([]);
    } catch {
      setActiveBots([]);
    } finally {
      setIsLoadingBots(false);
    }
  };

  useEffect(() => {
    if (!isOpen || activeSubView !== "storage") return;
    void fetchFiles(source);
  }, [isOpen, activeSubView, source]);

  useEffect(() => {
    if (!isOpen || activeSubView !== "bot-settings") return;
    void fetchBotSettings();
    void fetchActiveBots();
  }, [isOpen, activeSubView]);

  const handleSaveBotSettings = async () => {
    setBotSaveLoading(true);
    try {
      const payload: Record<string, unknown> = { bot_enabled: botEnabled };
      if (botToken.trim()) payload.telegram_bot_token = botToken;

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
    } catch {} finally {
      setBotSaveLoading(false);
    }
  };

  const handleDelete = async (file: StoredFile) => {
    if (!window.confirm(`Delete ${file.name}?`)) return;
    const url = `${apiBaseUrl}/admin/files?source=${file.source}&path=${encodeURIComponent(file.relative_path)}`;
    const res = await authFetch(url, { method: "DELETE" });
    if (res.ok) setFiles((prev) => prev.filter((f) => !(f.source === file.source && f.relative_path === file.relative_path)));
  };

  const handleView = async (file: StoredFile) => {
    const url = `${apiBaseUrl}/admin/files/view?source=${file.source}&path=${encodeURIComponent(file.relative_path)}`;
    const res = await authFetch(url);
    if (!res.ok) return;
    const blob = await res.blob();
    const blobUrl = URL.createObjectURL(blob);
    window.open(blobUrl, "_blank", "noopener,noreferrer");
    window.setTimeout(() => URL.revokeObjectURL(blobUrl), 60_000);
  };

  const handleDeleteAllFiles = async () => {
    if (!window.confirm("Delete ALL stored files from uploads and outputs?")) return;
    const res = await authFetch(`${apiBaseUrl}/admin/files/all`, { method: "DELETE" });
    if (res.ok) {
      setFiles([]);
      if (activeSubView === "storage") void fetchFiles(source);
    }
  };

  const formatSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    if (bytes < 1024 * 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
    return `${(bytes / (1024 * 1024 * 1024)).toFixed(2)} GB`;
  };

  const handleClose = () => {
    setIsOpen(false);
    setActiveSubView(null);
  };

  return (
    <>
      <div
        className={`admin-panel-overlay ${isOpen ? "show" : ""}`}
        onClick={handleClose}
      />

      <div className={`admin-panel-sidebar ${isOpen ? "open" : ""}`}>
        <div className="admin-panel-header">
          {activeSubView ? (
            <button className="admin-panel-back" onClick={() => setActiveSubView(null)} title="Back">
              ← {menuItems.find(m => m.key === activeSubView)?.label}
            </button>
          ) : (
            <h3>Admin Panel</h3>
          )}
          <button className="admin-panel-close" onClick={handleClose} title="Close">✕</button>
        </div>

        <div className="admin-panel-content">
          {!activeSubView ? (
            /* Main menu */
            <nav className="admin-menu">
              {menuItems.map((item) => (
                <button
                  key={item.key}
                  className="admin-menu-item"
                  onClick={() => setActiveSubView(item.key)}
                >
                  <span className="admin-menu-icon">{item.icon}</span>
                  <span className="admin-menu-label">{item.label}</span>
                  <span className="admin-menu-arrow">›</span>
                </button>
              ))}
            </nav>
          ) : activeSubView === "users" ? (
            /* Users sub-view */
            <div className="admin-subview">
              {activeUsers.length === 0 ? (
                <p className="admin-empty">No active users</p>
              ) : (
                <ul className="admin-user-list">
                  {activeUsers.map((u) => {
                    const isIdle = u.action === "idle";
                    return (
                      <li key={u.username} className="admin-user-item">
                        <div className="admin-user-info">
                          <span className="admin-user-name">{u.username} {u.is_admin ? "👑" : ""}</span>
                          <div className={`status-dot ${isIdle ? "dot-idle" : "dot-active"}`} />
                        </div>
                        <span className="admin-user-action">{isIdle ? "Idle" : `Processing: ${u.action}`}</span>
                      </li>
                    );
                  })}
                </ul>
              )}
            </div>
          ) : activeSubView === "storage" ? (
            /* Storage sub-view */
            <div className="admin-subview">
              <div className="admin-storage-tabs">
                <button
                  className={`admin-storage-tab ${source === "outputs" ? "active" : ""}`}
                  onClick={() => setSource("outputs")}
                >Outputs</button>
                <button
                  className={`admin-storage-tab ${source === "uploads" ? "active" : ""}`}
                  onClick={() => setSource("uploads")}
                >Uploads</button>
              </div>

              <button
                className="admin-panel-toggle admin-danger-btn"
                onClick={() => void handleDeleteAllFiles()}
              >
                🗑️ Delete All Files
              </button>

              {isLoadingFiles ? (
                <p className="admin-empty">Loading files...</p>
              ) : files.length === 0 ? (
                <p className="admin-empty">No files found</p>
              ) : (
                <ul className="admin-user-list">
                  {files.map((f) => (
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
                        <button className="admin-panel-toggle" style={{ padding: "4px 10px", fontSize: "0.76rem", flex: 1 }} onClick={() => void handleView(f)}>View</button>
                        <button className="admin-panel-toggle" style={{ padding: "4px 10px", fontSize: "0.76rem", borderColor: "#f87171", color: "#fca5a5", flex: 1 }} onClick={() => void handleDelete(f)}>Delete</button>
                      </div>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          ) : activeSubView === "bot-settings" ? (
            /* Bot Settings sub-view */
            <div className="admin-subview">
              <div className="admin-section">
                <h4>Active Bots</h4>
                {isLoadingBots ? (
                  <p className="admin-empty">Loading bots...</p>
                ) : activeBots.length === 0 ? (
                  <p className="admin-empty">No active bots</p>
                ) : (
                  <ul className="admin-user-list">
                    {activeBots.map((bot) => (
                      <li key={bot.id} className="admin-user-item">
                        <div className="admin-user-info">
                          <span className="admin-user-name">{bot.username}</span>
                          <div className={`status-dot ${bot.has_token ? "dot-active" : "dot-idle"}`} />
                        </div>
                        <span className="admin-user-action">{bot.has_token ? "✓ Token configured" : "✗ No token"}</span>
                        <span className="admin-user-action">{new Date(bot.updated_at).toLocaleString()}</span>
                      </li>
                    ))}
                  </ul>
                )}
              </div>

              <div className="admin-section">
                <h4>System Bot (Legacy)</h4>
                <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
                  <div style={{ fontSize: "0.85rem", display: "flex", flexDirection: "column", gap: 4 }}>
                    <span>Status: {botEnabled ? "✓ Enabled" : "✗ Disabled"}</span>
                    <span>Token: {botHasToken ? "✓ Set" : "Not configured"}</span>
                  </div>
                  <div>
                    <label style={{ display: "block", fontSize: "0.8rem", marginBottom: 4, color: "var(--muted)" }}>
                      Telegram Bot Token
                    </label>
                    <input
                      type="password"
                      placeholder="Paste token from @BotFather"
                      value={botToken}
                      onChange={(e) => setBotToken(e.target.value)}
                      style={{ width: "100%", padding: "8px", fontSize: "0.85rem", background: "rgba(0,0,0,0.2)", border: "1px solid var(--border)", borderRadius: "4px", color: "inherit", fontFamily: "monospace" }}
                    />
                    <p style={{ fontSize: "0.75rem", marginTop: 4, color: "var(--muted)" }}>Leave empty to keep current</p>
                  </div>
                  <label style={{ display: "flex", alignItems: "center", gap: 6, cursor: "pointer" }}>
                    <input type="checkbox" checked={botEnabled} onChange={(e) => setBotEnabled(e.target.checked)} style={{ cursor: "pointer" }} />
                    <span style={{ fontSize: "0.85rem" }}>Bot Enabled</span>
                  </label>
                  <button
                    className="admin-panel-toggle"
                    onClick={() => void handleSaveBotSettings()}
                    disabled={botSaveLoading}
                    style={{ padding: "8px 16px", fontSize: "0.85rem", opacity: botSaveLoading ? 0.5 : 1, cursor: botSaveLoading ? "not-allowed" : "pointer", width: "100%" }}
                  >
                    {botSaveLoading ? "Saving..." : "Save Bot Settings"}
                  </button>
                </div>
              </div>
            </div>
          ) : null}
        </div>
      </div>
    </>
  );
}
