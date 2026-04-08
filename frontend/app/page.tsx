"use client";

import { useState } from "react";
import Image from "next/image";
import bambamLogo from "@/bambam_logo.png";

import { AudioConverter } from "./components/audio-converter";
import { BatchRenameConverter } from "./components/batch-rename-converter";
import { DocumentConverter } from "./components/document-converter";
import { ImageConverter } from "./components/image-converter";
import { JobsDashboard } from "./components/jobs-dashboard";
import { VideoConverter } from "./components/video-converter";

import { useAuth } from "./lib/auth-context";
import { AuthScreen } from "./components/auth-screen";

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
            >
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
              >
                {item.label}
              </button>
            ))}
          </div>
          <div className="top-nav-user">
            <span className="user-badge">{user?.username} {user?.is_admin ? "👑" : ""}</span>
            <button className="primary-button inline-button logout-button" onClick={logout}>
              Logout
            </button>
          </div>
        </header>
      )}

      <section className="tools-section">{renderView()}</section>
    </main>
  );
}
