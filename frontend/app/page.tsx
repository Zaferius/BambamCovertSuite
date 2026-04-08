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

import { useAuth } from "./lib/auth-context";
import { useAction } from "./lib/action-context";
import { AuthScreen } from "./components/auth-screen";
import { AdminPanel } from "./components/admin-panel";

type ViewKey = "landing" | "image" | "audio" | "video" | "document" | "rename" | "jobs";

const landingToolItems: Array<{ key: Exclude<ViewKey, "landing" | "jobs">; label: string }> = [
  { key: "image", label: "Image Converter" },
  { key: "audio", label: "Sound Converter" },
  { key: "video", label: "Video Converter" },
  { key: "document", label: "Document Converter" },
  { key: "rename", label: "Batch Rename" },
];

const navToolItems: Array<{ key: Exclude<ViewKey, "landing" | "jobs">; label: string }> = [
  { key: "image", label: "Image" },
  { key: "audio", label: "Sound" },
  { key: "video", label: "Video" },
  { key: "document", label: "Document" },
  { key: "rename", label: "Batch Rename" },
];

const navItems: Array<{ key: ViewKey; label: string }> = [
  { key: "landing", label: "Home" },
  ...navToolItems,
  { key: "jobs", label: "Jobs" },
];


function BambamLogo() {
  return (
    <Image className="bambam-logo" src={bambamLogo} alt="Bambam logo" width={220} height={220} priority />
  );
}

export default function HomePage() {
  const [activeView, setActiveView] = useState<ViewKey>("landing");
  const { user, logout, isLoading } = useAuth();
  
  // Track unseen finished jobs per tool
  const [hasFinishedJobs, setHasFinishedJobs] = useState<Record<string, boolean>>({});
  const [lastSeenTime, setLastSeenTime] = useState<Record<string, number>>({});

  const apiBaseUrl = useMemo(
    () => process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000",
    [],
  );

  const { action } = useAction();

  useEffect(() => {
    if (!user) return;

    // Ping server with our current action
    const pingServer = async () => {
      try {
        await authFetch(`${apiBaseUrl}/auth/ping?action=${encodeURIComponent(action)}`, {
          method: "POST"
        });
      } catch (e) {}
    };

    pingServer();
    const pingInterval = setInterval(pingServer, 10000); // 10s ping

    // Quick polling to check for newly finished jobs
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
            
            if (jobTime > seenTime) {
              latestStatus[toolKey] = true;
            }
          }
        }
        
        setHasFinishedJobs(latestStatus);
      } catch(e) {}
    };
    
    void checkJobs();
    const interval = setInterval(checkJobs, 4000);
    return () => {
      clearInterval(interval);
      clearInterval(pingInterval);
    };
  }, [user, lastSeenTime, apiBaseUrl, action]);

  // When a user visits a tab, clear its notification
  useEffect(() => {
    if (activeView !== "landing") {
      setLastSeenTime(prev => ({ ...prev, [activeView]: Date.now() }));
      setHasFinishedJobs(prev => ({ ...prev, [activeView]: false }));
    }
  }, [activeView]);

  if (isLoading) return null;
  if (!user) return <AuthScreen />;

  const renderView = () => {
    if (activeView === "image") return <ImageConverter />;
    if (activeView === "audio") return <AudioConverter />;
    if (activeView === "video") return <VideoConverter />;
    if (activeView === "document") return <DocumentConverter />;
    if (activeView === "rename") return <BatchRenameConverter />;
    if (activeView === "jobs") return <JobsDashboard />;

    return (
      <section className="landing-shell">
        <BambamLogo />
        <h1 className="landing-title">Bambam Converter Suite</h1>
        <p className="landing-version">Version 1.3.1</p>
        <p className="landing-product">Bambam Product 2025</p>

        <div className="landing-actions">
          {landingToolItems.map((item) => (
            <button
              key={item.key}
              type="button"
              className="landing-tool-button"
              onClick={() => setActiveView(item.key)}
              style={{ position: "relative" }}
            >
              {hasFinishedJobs[item.key] && (
                <span className="notification-badge">!</span>
              )}
              {item.label}
            </button>
          ))}
        </div>
      </section>
    );
  };

  return (
    <main className={`page-shell ${activeView === "landing" ? "landing-page-shell" : ""}`}>
      {activeView !== "landing" && (
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
            {user?.is_admin && <AdminPanel />}
            <span className="user-badge">{user?.username} {user?.is_admin ? "👑" : ""}</span>
            <button className="primary-button logout-button" onClick={logout}>
              Logout
            </button>
          </div>
        </header>
      )}

      <section className="tools-section">{renderView()}</section>
    </main>
  );
}
