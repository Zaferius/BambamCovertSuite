"use client";

import { useEffect, useMemo, useState } from "react";
import Image from "next/image";
import bambamLogo from "@/bambam_logo.png";

import { AudioConverter } from "./components/audio-converter";
import { BatchRenameConverter } from "./components/batch-rename-converter";
import { DocumentConverter } from "./components/document-converter";
import { ImageConverter } from "./components/image-converter";
import { JobsDashboard } from "./components/jobs-dashboard";
import { VideoConverter } from "./components/video-converter";

type ViewKey = "landing" | "image" | "audio" | "video" | "document" | "rename" | "jobs";

type JobItem = {
  id: string;
  status: string;
  updated_at: string;
};

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
    <Image className="bambam-logo" src={bambamLogo} alt="Bambam logo" width={120} height={120} priority />
  );
}


export default function HomePage() {
  const [activeView, setActiveView] = useState<ViewKey>("landing");
  const [apiStatus, setApiStatus] = useState("Unavailable");
  const [jobs, setJobs] = useState<JobItem[]>([]);

  const apiBaseUrl = useMemo(
    () => process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000",
    [],
  );

  useEffect(() => {
    const load = async () => {
      try {
        const healthResponse = await fetch(`${apiBaseUrl}/health`, { cache: "no-store" });
        if (healthResponse.ok) {
          const payload = (await healthResponse.json()) as { status?: string };
          setApiStatus(payload.status ?? "ok");
        } else {
          setApiStatus("Unavailable");
        }
      } catch {
        setApiStatus("Unavailable");
      }

      try {
        const jobsResponse = await fetch(`${apiBaseUrl}/jobs`, { cache: "no-store" });
        if (jobsResponse.ok) {
          const payload = (await jobsResponse.json()) as JobItem[];
          setJobs(payload);
        }
      } catch {
        setJobs([]);
      }
    };

    void load();
    const interval = window.setInterval(() => {
      void load();
    }, 5000);

    return () => window.clearInterval(interval);
  }, [apiBaseUrl]);

  const completedCount = jobs.filter((job) => job.status === "completed").length;
  const failedCount = jobs.filter((job) => job.status === "failed").length;
  const processingCount = jobs.filter((job) => job.status === "processing" || job.status === "queued").length;
  const latestUpdate = jobs.length > 0 ? new Date(jobs[0].updated_at).toLocaleString() : "No jobs yet";

  const renderView = () => {
    if (activeView === "image") return <ImageConverter />;
    if (activeView === "audio") return <AudioConverter />;
    if (activeView === "video") return <VideoConverter />;
    if (activeView === "document") return <DocumentConverter />;
    if (activeView === "rename") return <BatchRenameConverter />;
    if (activeView === "jobs") return <JobsDashboard />;

    return (
      <section className="hero-card landing-card">
        <BambamLogo />
        <h1>Bambam Converter Suite</h1>
        <p className="hero-copy">Version 1.3.0</p>

        <div className="status-grid">
          <div className="status-card">
            <span className="status-label">API Health</span>
            <strong>{apiStatus}</strong>
          </div>
          <div className="status-card">
            <span className="status-label">Total Jobs</span>
            <strong>{jobs.length}</strong>
          </div>
          <div className="status-card">
            <span className="status-label">Processing</span>
            <strong>{processingCount}</strong>
          </div>
          <div className="status-card">
            <span className="status-label">Completed</span>
            <strong>{completedCount}</strong>
          </div>
          <div className="status-card">
            <span className="status-label">Failed</span>
            <strong>{failedCount}</strong>
          </div>
          <div className="status-card">
            <span className="status-label">Last Update</span>
            <strong>{latestUpdate}</strong>
          </div>
        </div>
      </section>
    );
  };

  return (
    <main className="page-shell">
      <header className="top-nav">
        {navItems.map((item) => (
          <button
            key={item.key}
            type="button"
            className={`top-nav-item ${activeView === item.key ? "active" : ""}`}
            onClick={() => setActiveView(item.key)}
          >
            {item.label}
          </button>
        ))}
      </header>

      <section className="tools-section">{renderView()}</section>
    </main>
  );
}
