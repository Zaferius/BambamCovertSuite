"use client";

import { useEffect, useState, useMemo } from "react";
import Image from "next/image";
import bambamLogo from "@/bambam_logo.png";
import { authFetch } from "./lib/auth-fetch";

import { AudioConverter } from "./components/audio-converter";
import { BatchRenameConverter } from "./components/batch-rename-converter";
import { DocumentConverter } from "./components/document-converter";
import { ImageConverter } from "./components/image-converter";
import { JobsDashboard } from "./components/jobs-dashboard";
import { VideoConverter } from "./components/video-converter";
import { UnifiedSettingsPanel } from "./components/unified-settings-panel";

import { useAuth } from "./lib/auth-context";
import { useAction } from "./lib/action-context";
import { AuthScreen } from "./components/auth-screen";
import { APP_VERSION } from "@/lib/version";

type ViewKey = "landing" | "image" | "audio" | "video" | "document" | "rename" | "jobs";

const landingToolItems: Array<{ key: Exclude<ViewKey, "landing" | "jobs">; label: string }> = [
  { key: "image", label: "Image Converter" },
  { key: "audio", label: "Sound Converter" },
  { key: "video", label: "Video Converter" },
  { key: "document", label: "Document Converter" },
  { key: "rename", label: "Batch Rename" },
];

const navItems: Array<{ key: ViewKey; label: string }> = [
  { key: "landing", label: "Home" },
  { key: "image", label: "Image" },
  { key: "audio", label: "Sound" },
  { key: "video", label: "Video" },
  { key: "document", label: "Document" },
  { key: "rename", label: "Batch Rename" },
  { key: "jobs", label: "Jobs" },
];

function BambamLogo() {
  return (
    <Image className="bambam-logo" src={bambamLogo} alt="Bambam logo" width={220} height={220} priority />
  );
}

export default function HomePage() {
  const [activeView, setActiveView] = useState<ViewKey>("landing");
  const [settingsPanelOpen, setSettingsPanelOpen] = useState(false);
  const { user, logout, isLoading } = useAuth();

  const [hasFinishedJobs, setHasFinishedJobs] = useState<Record<string, boolean>>({});
  const [lastSeenTime, setLastSeenTime] = useState<Record<string, number>>({});

  const apiBaseUrl = useMemo(
    () => process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000",
    [],
  );

  const { action } = useAction();

  useEffect(() => {
    if (!user) return;

    const pingServer = async () => {
      try {
        await authFetch(`${apiBaseUrl}/auth/ping?action=${encodeURIComponent(action)}`, { method: "POST" });
      } catch {}
    };

    pingServer();
    const pingInterval = setInterval(pingServer, 10000);

    const checkJobs = async () => {
      try {
        const response = await authFetch(`${apiBaseUrl}/jobs`, { cache: "no-store" });
        if (!response.ok) return;
        const jobs = await response.json();

        const latestStatus: Record<string, boolean> = {};
        for (const job of jobs) {
          if (job.status === "completed") {
            let toolKey = "jobs";
            if (job.job_type.includes("image")) toolKey = "image";
            if (job.job_type.includes("audio")) toolKey = "audio";
            if (job.job_type.includes("video")) toolKey = "video";
            if (job.job_type.includes("document")) toolKey = "document";
            if (job.job_type.includes("rename")) toolKey = "rename";

            const jobTime = new Date(job.updated_at).getTime();
            const seenTime = lastSeenTime[toolKey] || 0;
            if (jobTime > seenTime) latestStatus[toolKey] = true;
          }
        }
        setHasFinishedJobs(latestStatus);
      } catch {}
    };

    void checkJobs();
    const interval = setInterval(checkJobs, 4000);
    return () => {
      clearInterval(interval);
      clearInterval(pingInterval);
    };
  }, [user, lastSeenTime, apiBaseUrl, action]);

  useEffect(() => {
    if (activeView !== "landing") {
      setLastSeenTime(prev => ({ ...prev, [activeView]: Date.now() }));
      setHasFinishedJobs(prev => ({ ...prev, [activeView]: false }));
    }
  }, [activeView]);

  if (isLoading) return null;
  if (!user) return <AuthScreen />;

  const isLanding = activeView === "landing";

  return (
    <main className={isLanding ? "landing-page-shell" : "page-shell"}>
      <UnifiedSettingsPanel isOpen={settingsPanelOpen} setIsOpen={setSettingsPanelOpen} />

      {/* Settings FAB — always visible */}
      <button
        className="settings-fab"
        onClick={() => setSettingsPanelOpen(true)}
        title="Settings"
        aria-label="Settings"
      >
        ⚙️
      </button>

      {!isLanding && (
        <header className="top-nav">
          <div className="top-nav-tabs">
            {navItems.map((item) => (
              <button
                key={item.key}
                type="button"
                className={`top-nav-item ${activeView === item.key ? "active" : ""}`}
                onClick={() => setActiveView(item.key)}
                style={{ position: "relative" }}
              >
                {item.key !== "landing" && hasFinishedJobs[item.key] && (
                  <span className="notification-badge" style={{ top: "-6px", right: "-6px", width: "18px", height: "18px", fontSize: "11px" }}>!</span>
                )}
                {item.label}
              </button>
            ))}
          </div>
          <div className="top-nav-user">
            <span className="user-badge">{user?.username} {user?.is_admin ? "👑" : ""}</span>
            <button className="primary-button logout-button" onClick={logout}>
              Logout
            </button>
          </div>
        </header>
      )}

      <section className="tools-section">
        <section className="landing-shell" style={{ display: isLanding ? "flex" : "none" }}>
          <div className="landing-hero">
            <BambamLogo />
            <h1 className="landing-title">Bambam Converter Suite</h1>
            <p className="landing-version">v{APP_VERSION}</p>
            <p className="landing-product">All-in-one media conversion</p>
          </div>

          <div className="landing-grid">
            {landingToolItems.map((item) => (
              <button
                key={item.key}
                type="button"
                className="landing-tool-button"
                onClick={() => setActiveView(item.key)}
                style={{ position: "relative" }}
              >
                {hasFinishedJobs[item.key] && <span className="notification-badge">!</span>}
                {item.label}
              </button>
            ))}
            <button
              type="button"
              className="landing-tool-button landing-jobs-btn"
              onClick={() => setActiveView("jobs")}
              style={{ position: "relative" }}
            >
              {hasFinishedJobs["jobs"] && <span className="notification-badge">!</span>}
              Jobs
            </button>
          </div>

          <div className="landing-user-row">
            <span className="landing-user-info">
              Signed in as <strong>{user?.username}</strong>
              {user?.is_admin && <span className="landing-crown"> 👑</span>}
            </span>
            <button className="primary-button logout-button" onClick={logout}>Logout</button>
          </div>
        </section>

        <div style={{ display: activeView === "image" ? "block" : "none" }}>
          <ImageConverter />
        </div>
        <div style={{ display: activeView === "audio" ? "block" : "none" }}>
          <AudioConverter />
        </div>
        <div style={{ display: activeView === "video" ? "block" : "none" }}>
          <VideoConverter />
        </div>
        <div style={{ display: activeView === "document" ? "block" : "none" }}>
          <DocumentConverter />
        </div>
        <div style={{ display: activeView === "rename" ? "block" : "none" }}>
          <BatchRenameConverter />
        </div>
        <div style={{ display: activeView === "jobs" ? "block" : "none" }}>
          <JobsDashboard />
        </div>
      </section>
    </main>
  );
}
