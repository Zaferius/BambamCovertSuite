"use client";

import { FormEvent, useMemo, useState } from "react";

import { ConversionLoader } from "./conversion-loader";
import { buildApiUrl, isCompletedStatus, isFailedStatus } from "../lib/api";
import { authFetch } from "../lib/auth-fetch";
import { useAction } from "../lib/action-context";
import { JOB_STATUS, POLL_INTERVAL_MS, YOUTUBE_AUDIO_FORMATS, YOUTUBE_DOWNLOAD_MODES, YOUTUBE_VIDEO_QUALITIES } from "../lib/app-constants";

type AnalysisItem = {
    url: string;
    normalized_url?: string | null;
    title?: string | null;
    duration_seconds?: number | null;
    thumbnail_url?: string | null;
    platform?: string | null;
    available_qualities: Array<{ value: string; label: string; available: boolean }>;
    available_audio_formats: string[];
    status: string;
    error_message?: string | null;
};

type AnalyzeResponse = {
    items: AnalysisItem[];
};

type JobResponse = {
    job_id: string;
    status: string;
    original_filename: string;
    output_filename?: string | null;
    download_url?: string | null;
    item_count: number;
    progress: number;
    progress_detail?: string | null;
};

type JobStatusResponse = {
    id: string;
    status: string;
    progress: number;
    progress_detail?: string | null;
    output_filename?: string | null;
    output_path?: string | null;
    bundle_path?: string | null;
    error_message?: string | null;
};

function formatDuration(seconds?: number | null): string {
    if (!seconds || seconds <= 0) return "—";
    const hrs = Math.floor(seconds / 3600);
    const mins = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    if (hrs > 0) return `${hrs}:${String(mins).padStart(2, "0")}:${String(secs).padStart(2, "0")}`;
    return `${mins}:${String(secs).padStart(2, "0")}`;
}

export function YouTubeDownloader() {
    const [urlInput, setUrlInput] = useState("");
    const [downloadMode, setDownloadMode] = useState<(typeof YOUTUBE_DOWNLOAD_MODES)[number]>("video");
    const [selectedQuality, setSelectedQuality] = useState<string>("720p");
    const [audioFormat, setAudioFormat] = useState<(typeof YOUTUBE_AUDIO_FORMATS)[number]>("mp3");
    const [analysisItems, setAnalysisItems] = useState<AnalysisItem[]>([]);
    const [isAnalyzing, setIsAnalyzing] = useState(false);
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [jobStatus, setJobStatus] = useState<string | null>(null);
    const [jobProgress, setJobProgress] = useState<number>(0);
    const [jobProgressDetail, setJobProgressDetail] = useState<string | null>(null);
    const [result, setResult] = useState<JobResponse | null>(null);
    const [errorMessage, setErrorMessage] = useState<string | null>(null);
    const [isDownloadingResult, setIsDownloadingResult] = useState(false);
    const [downloadTriggerUrl, setDownloadTriggerUrl] = useState<string | null>(null);

    const { setAction } = useAction();

    const requestDownloadUrl = async (jobId: string): Promise<string> => {
        const response = await authFetch(buildApiUrl(`/youtube/jobs/${jobId}/download-token`), {
            method: "POST",
        });
        const payload = await response.json() as { download_url?: string; detail?: string };
        if (!response.ok || !payload.download_url) {
            throw new Error(payload.detail ?? "Could not prepare download.");
        }
        return buildApiUrl(payload.download_url);
    };

    const triggerBrowserDownload = (url: string, popupWindow: Window | null) => {
        if (popupWindow) {
            popupWindow.location.href = url;
            return;
        }

        window.location.assign(url);
    };

    const parsedUrls = useMemo(
        () => urlInput.split(/\r?\n/).map((value) => value.trim()).filter(Boolean),
        [urlInput],
    );

    const hasReadyItems = analysisItems.some((item) => item.status === "ready");

    const analyzeLinks = async () => {
        if (parsedUrls.length === 0) {
            setErrorMessage("Please paste at least one YouTube link.");
            return;
        }

        setIsAnalyzing(true);
        setErrorMessage(null);
        setResult(null);
        setJobStatus(null);
        setJobProgress(0);
        setJobProgressDetail(null);

        try {
            const response = await authFetch(buildApiUrl("/youtube/analyze"), {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ urls: parsedUrls, download_mode: downloadMode }),
            });
            const payload = (await response.json()) as AnalyzeResponse | { detail?: string };
            if (!response.ok) {
                throw new Error("detail" in payload ? payload.detail ?? "Analyze failed." : "Analyze failed.");
            }
            setAnalysisItems((payload as AnalyzeResponse).items);
        } catch (error) {
            setErrorMessage(error instanceof Error ? error.message : "Analyze failed.");
        } finally {
            setIsAnalyzing(false);
        }
    };

    const pollJobStatus = async (jobId: string) => {
        for (let attempt = 0; attempt < 600; attempt += 1) {
            await new Promise((resolve) => window.setTimeout(resolve, POLL_INTERVAL_MS));

            const response = await authFetch(buildApiUrl(`/youtube/jobs/${jobId}`), { cache: "no-store" });
            const payload = (await response.json()) as JobStatusResponse | { detail?: string };
            if (!response.ok) {
                throw new Error("detail" in payload ? payload.detail ?? "Job status failed." : "Job status failed.");
            }

            const statusPayload = payload as JobStatusResponse;
            setJobStatus(statusPayload.status);
            setJobProgress(statusPayload.progress ?? 0);
            setJobProgressDetail(statusPayload.progress_detail ?? null);

            if (isCompletedStatus(statusPayload.status)) {
                setResult((previous) => previous ? {
                    ...previous,
                    status: JOB_STATUS.completed,
                    output_filename: statusPayload.output_filename ?? previous.output_filename,
                    download_url: `/youtube/jobs/${jobId}/download`,
                    progress: statusPayload.progress ?? 100,
                    progress_detail: statusPayload.progress_detail ?? "Completed",
                } : previous);
                return;
            }

            if (isFailedStatus(statusPayload.status)) {
                throw new Error(statusPayload.error_message ?? "Download failed.");
            }
        }

        throw new Error("Download is taking longer than expected.");
    };

    const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
        event.preventDefault();
        if (!hasReadyItems) {
            setErrorMessage("Analyze valid links before downloading.");
            return;
        }

        const readyUrls = analysisItems.filter((item) => item.status === "ready").map((item) => item.normalized_url || item.url);
        setIsSubmitting(true);
        setErrorMessage(null);
        setResult(null);
        setJobStatus(null);
        setJobProgress(0);
        setJobProgressDetail(null);

        try {
            setAction("Downloading YouTube Media");
            const response = await authFetch(buildApiUrl("/youtube/jobs"), {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    urls: readyUrls,
                    download_mode: downloadMode,
                    selected_quality: selectedQuality,
                    audio_format: audioFormat,
                }),
            });
            const payload = (await response.json()) as JobResponse | { detail?: string };
            if (!response.ok) {
                throw new Error("detail" in payload ? payload.detail ?? "Failed to queue download." : "Failed to queue download.");
            }
            const queued = payload as JobResponse;
            setResult(queued);
            setJobStatus(queued.status);
            setJobProgress(queued.progress);
            setJobProgressDetail(queued.progress_detail ?? "Queued");
            await pollJobStatus(queued.job_id);
        } catch (error) {
            setErrorMessage(error instanceof Error ? error.message : "Failed to queue download.");
        } finally {
            setIsSubmitting(false);
            setAction("idle");
        }
    };

    return (
        <section className="tool-card feature-card">
            <div className="section-heading compact-heading">
                <h2>YouTube Downloader</h2>
                <p>Analyze one or more YouTube links, choose video or audio output, and download with Bambam-style batch workflow.</p>
            </div>

            <form className="converter-form" onSubmit={handleSubmit}>
                <label className="field-group">
                    <span>YouTube links</span>
                    <textarea
                        className="youtube-url-textarea"
                        rows={6}
                        value={urlInput}
                        onChange={(event) => setUrlInput(event.target.value)}
                        placeholder="Paste one YouTube link per line"
                    />
                </label>

                <div className="feature-toggles-row">
                    {YOUTUBE_DOWNLOAD_MODES.map((mode) => (
                        <button
                            key={mode}
                            type="button"
                            className={`feature-toggle-btn${downloadMode === mode ? " active" : ""}`}
                            onClick={() => setDownloadMode(mode)}
                        >
                            <span className="feature-toggle-dot" />
                            {mode === "video" ? "Video" : "Audio"}
                        </button>
                    ))}
                </div>

                <div className="form-grid">
                    <label className="field-group">
                        <span>{downloadMode === "video" ? "Preferred quality" : "Preferred audio quality"}</span>
                        <select value={selectedQuality} onChange={(event) => setSelectedQuality(event.target.value)}>
                            {(downloadMode === "video" ? YOUTUBE_VIDEO_QUALITIES : ["64k", "128k", "192k", "256k", "320k", "best"]).map((quality) => (
                                <option key={quality} value={quality}>{quality}</option>
                            ))}
                        </select>
                    </label>

                    {downloadMode === "audio" && (
                        <label className="field-group">
                            <span>Audio format</span>
                            <select value={audioFormat} onChange={(event) => setAudioFormat(event.target.value as (typeof YOUTUBE_AUDIO_FORMATS)[number])}>
                                {YOUTUBE_AUDIO_FORMATS.map((format) => (
                                    <option key={format} value={format}>{format.toUpperCase()}</option>
                                ))}
                            </select>
                        </label>
                    )}
                </div>

                <div className="youtube-toolbar-row">
                    <button className="primary-button" type="button" onClick={analyzeLinks} disabled={isAnalyzing || parsedUrls.length === 0}>
                        {isAnalyzing ? "Analyzing..." : "Analyze links"}
                    </button>
                    <button className="primary-button" type="submit" disabled={isSubmitting || !hasReadyItems}>
                        {isSubmitting ? "Downloading..." : `Download ${downloadMode}`}
                    </button>
                </div>

                {analysisItems.length > 0 && (
                    <div className="youtube-analysis-list">
                        {analysisItems.map((item, index) => (
                            <article key={`${item.url}-${index}`} className={`youtube-analysis-card${item.status !== "ready" ? " youtube-analysis-card--failed" : ""}`}>
                                <div className="youtube-analysis-card-header">
                                    <div>
                                        <h3>{item.title ?? "Unavailable title"}</h3>
                                        <p>{item.platform ?? "Unknown source"} · {formatDuration(item.duration_seconds)}</p>
                                    </div>
                                    <span className="badge">{item.status}</span>
                                </div>
                                <p className="youtube-analysis-url">{item.normalized_url ?? item.url}</p>
                                {item.thumbnail_url ? <img className="youtube-analysis-thumb" src={item.thumbnail_url} alt={item.title ?? "YouTube thumbnail"} /> : null}
                                {item.status === "ready" ? (
                                    <div className="youtube-analysis-meta">
                                        <div>
                                            <strong>Available qualities:</strong>
                                            <div className="youtube-chip-row">
                                                {item.available_qualities.map((quality) => <span key={quality.value} className="badge">{quality.label}</span>)}
                                            </div>
                                        </div>
                                        {downloadMode === "audio" && item.available_audio_formats.length > 0 ? (
                                            <div>
                                                <strong>Formats:</strong>
                                                <div className="youtube-chip-row">
                                                    {item.available_audio_formats.map((format) => <span key={format} className="badge">{format.toUpperCase()}</span>)}
                                                </div>
                                            </div>
                                        ) : null}
                                    </div>
                                ) : (
                                    <p className="error-text">{item.error_message ?? "This link could not be analyzed."}</p>
                                )}
                            </article>
                        ))}
                    </div>
                )}
            </form>

            {(isSubmitting || isAnalyzing) ? <ConversionLoader isVisible jobStatus={jobStatus ?? (isAnalyzing ? "processing" : "queued")} /> : null}

            {(isSubmitting || result) && (
                <div className="result-card">
                    <h3>YouTube download state</h3>
                    {result ? (
                        <>
                            <p><strong>Job:</strong> {result.job_id}</p>
                            <p><strong>Items:</strong> {result.item_count}</p>
                        </>
                    ) : null}
                    <p><strong>Status:</strong> {jobStatus ?? "idle"}</p>
                    <p><strong>Progress:</strong> {jobProgress}%</p>
                    {jobProgressDetail ? <p><strong>Detail:</strong> {jobProgressDetail}</p> : null}
                    {result?.download_url ? (
                        <button
                            className="primary-button inline-button"
                            type="button"
                            disabled={isDownloadingResult}
                            onClick={async () => {
                                const popupWindow = window.open("about:blank", "_blank", "noopener,noreferrer");
                                try {
                                    setIsDownloadingResult(true);
                                    setErrorMessage(null);
                                    const preparedUrl = await requestDownloadUrl(result.job_id);
                                    setDownloadTriggerUrl(preparedUrl);
                                    triggerBrowserDownload(preparedUrl, popupWindow);
                                } catch (error) {
                                    popupWindow?.close();
                                    setErrorMessage(error instanceof Error ? error.message : "Download failed.");
                                } finally {
                                    setIsDownloadingResult(false);
                                }
                            }}
                        >
                            {isDownloadingResult ? "Preparing download..." : `Download ${result.item_count > 1 ? "zip bundle" : "media file"}`}
                        </button>
                    ) : null}
                </div>
            )}

            {errorMessage ? <p className="error-text">{errorMessage}</p> : null}
            {downloadTriggerUrl ? <p className="selection-hint">Download prepared. If the browser does not show the save dialog automatically, <a href={downloadTriggerUrl} target="_blank" rel="noreferrer">click here</a>.</p> : null}
            <p className="selection-hint">If a chosen quality is unavailable for a link, Bambam automatically falls back to the nearest available quality.</p>
        </section>
    );
}
