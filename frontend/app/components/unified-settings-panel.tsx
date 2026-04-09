"use client";

import { useEffect, useState, useMemo } from "react";
import { authFetch } from "../lib/auth-fetch";
import { useAuth } from "../lib/auth-context";

// ── Types ─────────────────────────────────────────────────────────────────────

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

type WorkerItem = {
  worker_id: string;
  display_name?: string;
  hostname?: string;
  pid?: number;
  status: "idle" | "busy" | "offline";
  online: boolean;
  current_job_id?: string | null;
  current_job_type?: string | null;
  last_seen?: number;
  started_at?: number;
  last_error?: string | null;
};

type WorkerSummary = {
  target_workers: number;
  online_workers: number;
  busy_workers: number;
  idle_workers: number;
  queue_size: number;
  health: "healthy" | "degraded" | "down";
  api_ok?: boolean;
  redis_ok?: boolean;
};

type UserJob = {
  id: string;
  job_type: string;
  status: string;
  original_filename?: string;
  output_filename?: string;
  created_at: string;
  updated_at: string;
};

type SubView = "users" | "storage" | "bot-settings" | "workers" | "account";

// ── Props ─────────────────────────────────────────────────────────────────────

type Props = {
  isOpen: boolean;
  setIsOpen: (open: boolean) => void;
};

// ── Main Component ────────────────────────────────────────────────────────────

export function UnifiedSettingsPanel({ isOpen, setIsOpen }: Props) {
  const { user, logout } = useAuth();
  const isAdmin = user?.is_admin ?? false;

  const [activeSubView, setActiveSubView] = useState<SubView | null>(null);

  const apiBaseUrl = useMemo(
    () => process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000",
    []
  );

  const handleClose = () => {
    setIsOpen(false);
    setActiveSubView(null);
  };

  const menuItems: Array<{ key: SubView; label: string; icon: string; adminOnly?: boolean }> = [
    { key: "account", label: "Account", icon: "👤" },
    ...(isAdmin ? [{ key: "users" as SubView, label: "Users", icon: "👥", adminOnly: true }] : []),
    ...(isAdmin ? [{ key: "workers" as SubView, label: "Workers", icon: "🧰", adminOnly: true }] : []),
    { key: "storage", label: "Storage", icon: "🗂️" },
    { key: "bot-settings", label: "Bot Settings", icon: "🤖" },
  ];

  const currentLabel = menuItems.find((m) => m.key === activeSubView)?.label ?? "";

  return (
    <>
      <div
        className={`admin-panel-overlay ${isOpen ? "show" : ""}`}
        onClick={handleClose}
      />
      <div className={`admin-panel-sidebar ${isOpen ? "open" : ""}`}>
        <div className="admin-panel-header">
          {activeSubView ? (
            <button className="admin-panel-back" onClick={() => setActiveSubView(null)}>
              ← {currentLabel}
            </button>
          ) : (
            <h3>⚙️ {isAdmin ? "Admin Settings" : "Settings"}</h3>
          )}
          <button className="admin-panel-close" onClick={handleClose} title="Close">✕</button>
        </div>

        <div className="admin-panel-content">
          {!activeSubView ? (
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
          ) : activeSubView === "account" ? (
            <AccountView user={user} logout={logout} />
          ) : activeSubView === "users" && isAdmin ? (
            <UsersView isOpen={isOpen} apiBaseUrl={apiBaseUrl} />
          ) : activeSubView === "workers" && isAdmin ? (
            <WorkersView isOpen={isOpen} apiBaseUrl={apiBaseUrl} />
          ) : activeSubView === "storage" ? (
            isAdmin
              ? <AdminStorageView apiBaseUrl={apiBaseUrl} isOpen={isOpen} />
              : <UserStorageView apiBaseUrl={apiBaseUrl} isOpen={isOpen} />
          ) : activeSubView === "bot-settings" ? (
            isAdmin
              ? <AdminBotSettingsView apiBaseUrl={apiBaseUrl} isOpen={isOpen} />
              : <UserBotSettingsView apiBaseUrl={apiBaseUrl} />
          ) : null}
        </div>
      </div>
    </>
  );
}

// ── Account Sub-View ──────────────────────────────────────────────────────────

function AccountView({
  user,
  logout,
}: {
  user: { username: string; is_admin: boolean } | null;
  logout: () => void;
}) {
  return (
    <div className="admin-subview">
      <div className="admin-section">
        <h4>Account Info</h4>
        <div style={{ display: "flex", flexDirection: "column", gap: 8, fontSize: "0.9rem" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <span style={{ color: "var(--muted)" }}>Username</span>
            <strong>{user?.username}</strong>
          </div>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <span style={{ color: "var(--muted)" }}>Role</span>
            <span>{user?.is_admin ? "👑 Admin" : "User"}</span>
          </div>
        </div>
      </div>
      <div className="admin-section">
        <button
          className="admin-panel-toggle"
          style={{ width: "100%", justifyContent: "center", padding: "10px", borderColor: "#f87171", color: "#fca5a5" }}
          onClick={logout}
        >
          Logout
        </button>
      </div>
    </div>
  );
}

// ── Users Sub-View (Admin only) ───────────────────────────────────────────────

function UsersView({ isOpen, apiBaseUrl }: { isOpen: boolean; apiBaseUrl: string }) {
  const [activeUsers, setActiveUsers] = useState<ActiveUser[]>([]);

  useEffect(() => {
    if (!isOpen) return;
    const fetch_ = async () => {
      try {
        const res = await authFetch(`${apiBaseUrl}/auth/online-users`);
        if (res.ok) setActiveUsers(await res.json());
      } catch {}
    };
    fetch_();
    const interval = setInterval(fetch_, 3000);
    return () => clearInterval(interval);
  }, [isOpen, apiBaseUrl]);

  return (
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
  );
}

// ── Admin Storage Sub-View ────────────────────────────────────────────────────

function AdminStorageView({ apiBaseUrl, isOpen }: { apiBaseUrl: string; isOpen: boolean }) {
  const [source, setSource] = useState<"outputs" | "uploads">("outputs");
  const [files, setFiles] = useState<StoredFile[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  const fetchFiles = async (src: "outputs" | "uploads") => {
    setIsLoading(true);
    try {
      const res = await authFetch(`${apiBaseUrl}/admin/files?source=${src}&limit=300`);
      if (res.ok) setFiles((await res.json()) as StoredFile[]);
      else setFiles([]);
    } catch {
      setFiles([]);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (!isOpen) return;
    void fetchFiles(source);
  }, [isOpen, source]);

  const handleView = async (file: StoredFile) => {
    const res = await authFetch(`${apiBaseUrl}/admin/files/view?source=${file.source}&path=${encodeURIComponent(file.relative_path)}`);
    if (!res.ok) return;
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    window.open(url, "_blank", "noopener,noreferrer");
    setTimeout(() => URL.revokeObjectURL(url), 60_000);
  };

  const handleDelete = async (file: StoredFile) => {
    if (!confirm(`Delete ${file.name}?`)) return;
    const res = await authFetch(`${apiBaseUrl}/admin/files?source=${file.source}&path=${encodeURIComponent(file.relative_path)}`, { method: "DELETE" });
    if (res.ok) setFiles((p) => p.filter((f) => !(f.source === file.source && f.relative_path === file.relative_path)));
  };

  const handleDeleteAll = async () => {
    if (!confirm("Delete ALL stored files from uploads and outputs?")) return;
    const res = await authFetch(`${apiBaseUrl}/admin/files/all`, { method: "DELETE" });
    if (res.ok) { setFiles([]); void fetchFiles(source); }
  };

  return (
    <div className="admin-subview">
      <div className="admin-storage-tabs">
        <button className={`admin-storage-tab ${source === "outputs" ? "active" : ""}`} onClick={() => setSource("outputs")}>Outputs</button>
        <button className={`admin-storage-tab ${source === "uploads" ? "active" : ""}`} onClick={() => setSource("uploads")}>Uploads</button>
      </div>
      <button className="admin-panel-toggle admin-danger-btn" onClick={() => void handleDeleteAll()}>🗑️ Delete All Files</button>
      <StoredFileList files={files} isLoading={isLoading} onView={handleView} onDelete={handleDelete} />
    </div>
  );
}

// ── User Storage Sub-View ─────────────────────────────────────────────────────

function UserStorageView({ apiBaseUrl, isOpen }: { apiBaseUrl: string; isOpen: boolean }) {
  const [jobs, setJobs] = useState<UserJob[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    if (!isOpen) return;
    const fetch_ = async () => {
      setIsLoading(true);
      try {
        const res = await authFetch(`${apiBaseUrl}/jobs`, { cache: "no-store" });
        if (res.ok) setJobs(await res.json());
      } catch {} finally {
        setIsLoading(false);
      }
    };
    void fetch_();
  }, [isOpen, apiBaseUrl]);

  const completedJobs = jobs.filter((j) => j.status === "completed");

  const handleDownload = async (job: UserJob) => {
    const jobType = job.job_type;
    const isBatch = jobType.startsWith("batch_");
    const typeSlug = isBatch
      ? jobType.replace("batch_", "")
      : jobType.replace("_conversion", "");
    const downloadPath = isBatch
      ? `/batch/jobs/${job.id}/download`
      : `/${typeSlug}/jobs/${job.id}/download`;

    try {
      const res = await authFetch(`${apiBaseUrl}${downloadPath}`);
      if (!res.ok) return;
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = job.output_filename ?? `${job.id}_converted`;
      a.click();
      setTimeout(() => URL.revokeObjectURL(url), 60_000);
    } catch {}
  };

  if (isLoading) return <p className="admin-empty">Loading your files...</p>;
  if (completedJobs.length === 0) return <p className="admin-empty">No completed jobs yet</p>;

  return (
    <div className="admin-subview">
      <ul className="admin-user-list">
        {completedJobs.map((job) => (
          <li key={job.id} className="admin-user-item">
            <div className="admin-user-info">
              <span className="admin-user-name" style={{ fontSize: "0.84rem" }} title={job.id}>
                {job.original_filename ?? job.id}
              </span>
              <span style={{ color: "var(--muted)", fontSize: "0.72rem", textTransform: "capitalize" }}>
                {job.job_type.replace(/_/g, " ")}
              </span>
            </div>
            <span className="admin-user-action">{new Date(job.updated_at).toLocaleString()}</span>
            <div style={{ marginTop: 8 }}>
              <button
                className="admin-panel-toggle"
                style={{ padding: "4px 10px", fontSize: "0.76rem", width: "100%" }}
                onClick={() => void handleDownload(job)}
              >
                ⬇ Download
              </button>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}

// ── Admin Bot Settings Sub-View ───────────────────────────────────────────────

function AdminBotSettingsView({ apiBaseUrl, isOpen }: { apiBaseUrl: string; isOpen: boolean }) {
  const [activeBots, setActiveBots] = useState<ActiveBot[]>([]);
  const [isLoadingBots, setIsLoadingBots] = useState(false);
  const [botToken, setBotToken] = useState("");
  const [botEnabled, setBotEnabled] = useState(false);
  const [botHasToken, setBotHasToken] = useState(false);
  const [botSaveLoading, setBotSaveLoading] = useState(false);

  useEffect(() => {
    if (!isOpen) return;
    const fetchBots = async () => {
      setIsLoadingBots(true);
      try {
        const res = await authFetch(`${apiBaseUrl}/admin/bot-settings/active`);
        if (res.ok) setActiveBots(await res.json());
      } catch {} finally { setIsLoadingBots(false); }
    };
    const fetchSettings = async () => {
      try {
        const res = await authFetch(`${apiBaseUrl}/admin/bot-settings`);
        if (res.ok) {
          const d = await res.json();
          setBotEnabled(d.bot_enabled ?? false);
          setBotHasToken(d.has_token ?? false);
        }
      } catch {}
    };
    void fetchBots();
    void fetchSettings();
  }, [isOpen, apiBaseUrl]);

  const handleSave = async () => {
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
        const d = await res.json();
        setBotToken("");
        setBotHasToken(d.has_token);
        setBotEnabled(d.bot_enabled);
      }
    } catch {} finally { setBotSaveLoading(false); }
  };

  return (
    <div className="admin-subview">
      <div className="admin-section">
        <h4>Active Bots</h4>
        {isLoadingBots ? (
          <p className="admin-empty">Loading...</p>
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
            <label style={{ display: "block", fontSize: "0.8rem", marginBottom: 4, color: "var(--muted)" }}>Telegram Bot Token</label>
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
            <input type="checkbox" checked={botEnabled} onChange={(e) => setBotEnabled(e.target.checked)} />
            <span style={{ fontSize: "0.85rem" }}>Bot Enabled</span>
          </label>
          <button
            className="admin-panel-toggle"
            onClick={() => void handleSave()}
            disabled={botSaveLoading}
            style={{ padding: "8px 16px", fontSize: "0.85rem", opacity: botSaveLoading ? 0.5 : 1, width: "100%" }}
          >
            {botSaveLoading ? "Saving..." : "Save Bot Settings"}
          </button>
        </div>
      </div>
    </div>
  );
}

// ── User Bot Settings Sub-View ────────────────────────────────────────────────

function UserBotSettingsView({ apiBaseUrl }: { apiBaseUrl: string }) {
  const [botToken, setBotToken] = useState("");
  const [botEnabled, setBotEnabled] = useState(false);
  const [botHasToken, setBotHasToken] = useState(false);
  const [botSaveLoading, setBotSaveLoading] = useState(false);
  const [saveMessage, setSaveMessage] = useState("");

  useEffect(() => {
    const fetch_ = async () => {
      try {
        const res = await authFetch(`${apiBaseUrl}/auth/user/bot-settings`);
        if (res.ok) {
          const d = await res.json();
          setBotEnabled(d.bot_enabled ?? false);
          setBotHasToken(d.has_token ?? false);
        }
      } catch {}
    };
    void fetch_();
  }, [apiBaseUrl]);

  const handleSave = async () => {
    setBotSaveLoading(true);
    setSaveMessage("");
    try {
      const payload: Record<string, unknown> = { bot_enabled: botEnabled };
      if (botToken.trim()) payload.telegram_bot_token = botToken;
      const res = await authFetch(`${apiBaseUrl}/auth/user/bot-settings`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (res.ok) {
        const d = await res.json();
        setBotToken("");
        setBotHasToken(d.has_token);
        setBotEnabled(d.bot_enabled);
        setSaveMessage("✓ Saved successfully!");
        setTimeout(() => setSaveMessage(""), 3000);
      } else {
        setSaveMessage("✗ Failed to save");
      }
    } catch {
      setSaveMessage("✗ Error saving");
    } finally {
      setBotSaveLoading(false);
    }
  };

  return (
    <div className="admin-subview">
      <div className="admin-section">
        <h4>Your Telegram Bot</h4>
        <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          <div style={{ fontSize: "0.85rem", display: "flex", flexDirection: "column", gap: 4 }}>
            <span>Status: {botEnabled ? "✓ Enabled" : "✗ Disabled"}</span>
            <span>Token: {botHasToken ? "✓ Configured" : "✗ Not configured"}</span>
          </div>
          <div>
            <label style={{ display: "block", fontSize: "0.8rem", marginBottom: 4, color: "var(--muted)" }}>Telegram Bot Token</label>
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
            <input type="checkbox" checked={botEnabled} onChange={(e) => setBotEnabled(e.target.checked)} />
            <span style={{ fontSize: "0.85rem" }}>Enable my bot</span>
          </label>
          <button
            className="admin-panel-toggle"
            onClick={() => void handleSave()}
            disabled={botSaveLoading}
            style={{ padding: "8px 16px", fontSize: "0.85rem", opacity: botSaveLoading ? 0.5 : 1, width: "100%" }}
          >
            {botSaveLoading ? "Saving..." : "Save"}
          </button>
          {saveMessage && (
            <span style={{ fontSize: "0.85rem", color: saveMessage.includes("✓") ? "#00e87a" : "#f87171" }}>
              {saveMessage}
            </span>
          )}
        </div>
      </div>

      <div className="admin-section" style={{ fontSize: "0.85rem", color: "var(--muted)" }}>
        <h4 style={{ color: "var(--accent)" }}>How to set up</h4>
        <ol style={{ margin: 0, paddingLeft: "18px", lineHeight: 1.7 }}>
          <li>Open Telegram → message @BotFather</li>
          <li>Send /newbot and follow the prompts</li>
          <li>Copy your bot token and paste above</li>
          <li>Enable your bot and save</li>
          <li>Find your bot on Telegram → send /start</li>
        </ol>
      </div>
    </div>
  );
}

// ── Workers Sub-View (Admin only) ─────────────────────────────────────────────

function WorkersView({ isOpen, apiBaseUrl }: { isOpen: boolean; apiBaseUrl: string }) {
  const [workers, setWorkers] = useState<WorkerItem[]>([]);
  const [summary, setSummary] = useState<WorkerSummary | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [scaleTarget, setScaleTarget] = useState<string>("");
  const [isScaling, setIsScaling] = useState(false);
  const [message, setMessage] = useState<string>("");

  const fetchWorkers = async () => {
    setIsLoading(true);
    try {
      const res = await authFetch(`${apiBaseUrl}/admin/workers`, { cache: "no-store" });
      if (!res.ok) {
        setWorkers([]);
        setSummary(null);
        return;
      }
      const data = await res.json() as { workers: WorkerItem[]; summary: WorkerSummary };
      setWorkers(data.workers ?? []);
      setSummary(data.summary ?? null);
      if (data.summary && !scaleTarget) setScaleTarget(String(data.summary.target_workers));
    } catch {
      setWorkers([]);
      setSummary(null);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (!isOpen) return;
    void fetchWorkers();
    const id = window.setInterval(() => {
      void fetchWorkers();
    }, 5000);
    return () => window.clearInterval(id);
  }, [isOpen, apiBaseUrl]);

  const healthColor = summary?.health === "healthy"
    ? "#22c55e"
    : summary?.health === "degraded"
      ? "#f59e0b"
      : "#ef4444";

  const handleScale = async () => {
    const parsed = Number(scaleTarget);
    if (!Number.isFinite(parsed) || parsed < 1) {
      setMessage("✗ Enter a valid worker count");
      return;
    }
    setIsScaling(true);
    setMessage("");
    try {
      const res = await authFetch(`${apiBaseUrl}/admin/workers/scale`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ target_count: parsed }),
      });
      const payload = await res.json().catch(() => ({}));
      if (!res.ok) {
        setMessage(`✗ ${payload?.detail ?? "Scale failed"}`);
        return;
      }
      setMessage("✓ Scale command applied");
      await fetchWorkers();
    } catch {
      setMessage("✗ Scale command error");
    } finally {
      setIsScaling(false);
    }
  };

  return (
    <div className="admin-subview">
      <div className="admin-section">
        <h4>Workers Overview</h4>
        {summary ? (
          <div className="workers-summary-grid">
            <div className="workers-summary-card"><span>Target</span><strong>{summary.target_workers}</strong></div>
            <div className="workers-summary-card"><span>Online</span><strong>{summary.online_workers}</strong></div>
            <div className="workers-summary-card"><span>Busy</span><strong>{summary.busy_workers}</strong></div>
            <div className="workers-summary-card"><span>Queue</span><strong>{summary.queue_size}</strong></div>
            <div className="workers-summary-card">
              <span>API</span>
              <strong style={{ color: summary.api_ok ? "#22c55e" : "#ef4444" }}>{summary.api_ok ? "OK" : "DOWN"}</strong>
            </div>
            <div className="workers-summary-card">
              <span>Redis</span>
              <strong style={{ color: summary.redis_ok ? "#22c55e" : "#ef4444" }}>{summary.redis_ok ? "OK" : "DOWN"}</strong>
            </div>
            <div className="workers-summary-card" style={{ borderColor: `${healthColor}66` }}>
              <span>Health</span>
              <strong style={{ color: healthColor, textTransform: "capitalize" }}>{summary.health}</strong>
            </div>
          </div>
        ) : (
          <p className="admin-empty">No worker summary available</p>
        )}
      </div>

      <div className="admin-section">
        <h4>Scale Workers</h4>
        <div className="workers-scale-row">
          <input
            type="number"
            min={1}
            step={1}
            value={scaleTarget}
            onChange={(e) => setScaleTarget(e.target.value)}
            className="workers-scale-input"
          />
          <button
            className="admin-panel-toggle"
            onClick={() => void handleScale()}
            disabled={isScaling}
          >
            {isScaling ? "Scaling..." : "Apply Scale"}
          </button>
        </div>
        {message && (
          <p style={{ margin: "8px 0 0", fontSize: "0.82rem", color: message.includes("✓") ? "#22c55e" : "#f87171" }}>
            {message}
          </p>
        )}
      </div>

      <div className="admin-section">
        <div className="admin-section-header">
          <h4>Worker List</h4>
          <button className="admin-panel-toggle" onClick={() => void fetchWorkers()} disabled={isLoading}>
            {isLoading ? "Refreshing..." : "Refresh"}
          </button>
        </div>

        {isLoading && workers.length === 0 ? (
          <p className="admin-empty">Loading workers...</p>
        ) : workers.length === 0 ? (
          <p className="admin-empty">No workers reported yet</p>
        ) : (
          <ul className="admin-user-list">
            {workers.map((w) => {
              const isBusy = w.status === "busy";
              const isOnline = w.online;
              const workerLabel = w.display_name || w.worker_id;
              return (
                <li key={w.worker_id} className="admin-user-item">
                  <div className="admin-user-info">
                    <span className="admin-user-name" style={{ fontSize: "0.84rem" }} title={w.worker_id}>{workerLabel}</span>
                    <div className={`status-dot ${isOnline ? (isBusy ? "dot-active" : "dot-idle") : "dot-offline"}`} />
                  </div>
                  <span className="admin-user-action">
                    {isOnline ? (isBusy ? "Busy" : "Idle") : "Offline"}
                  </span>
                  <span className="admin-user-action">
                    Job: {w.current_job_id ? `${w.current_job_type ?? "job"} (${w.current_job_id.slice(0, 8)}...)` : "None"}
                  </span>
                  <span className="admin-user-action">
                    Last seen: {w.last_seen ? new Date(w.last_seen * 1000).toLocaleString() : "-"}
                  </span>
                </li>
              );
            })}
          </ul>
        )}
      </div>
    </div>
  );
}

// ── Shared File List ──────────────────────────────────────────────────────────

function StoredFileList({
  files,
  isLoading,
  onView,
  onDelete,
}: {
  files: StoredFile[];
  isLoading: boolean;
  onView: (f: StoredFile) => void;
  onDelete: (f: StoredFile) => void;
}) {
  const formatSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    if (bytes < 1024 * 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
    return `${(bytes / (1024 * 1024 * 1024)).toFixed(2)} GB`;
  };

  if (isLoading) return <p className="admin-empty">Loading files...</p>;
  if (files.length === 0) return <p className="admin-empty">No files found</p>;

  return (
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
            <button className="admin-panel-toggle" style={{ padding: "4px 10px", fontSize: "0.76rem", flex: 1 }} onClick={() => onView(f)}>View</button>
            <button className="admin-panel-toggle" style={{ padding: "4px 10px", fontSize: "0.76rem", borderColor: "#f87171", color: "#fca5a5", flex: 1 }} onClick={() => onDelete(f)}>Delete</button>
          </div>
        </li>
      ))}
    </ul>
  );
}
