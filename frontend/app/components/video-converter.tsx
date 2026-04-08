"use client";

import { ChangeEvent, FormEvent, SyntheticEvent, useEffect, useMemo, useState } from "react";
import { ConversionLoader } from "./conversion-loader";
import { type FileUploadItem, UploadProgressPanel } from "./upload-progress";
import { distributeProgress, xhrPost } from "../lib/xhr-post";
import { authFetch } from "../lib/auth-fetch";


const videoFormats = ["MP4", "MOV", "MKV", "AVI", "WEBM", "GIF"] as const;

type VideoConversionResponse = {
  job_id: string;
  status: string;
  target_format: string;
  fps: number;
  resize_enabled: boolean;
  width?: number | null;
  height?: number | null;
  original_filename: string;
  output_filename?: string | null;
  download_url?: string | null;
};

type VideoJobStatusResponse = {
  id: string;
  status: string;
  output_path?: string | null;
  error_message?: string | null;
};


export function VideoConverter() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [targetFormat, setTargetFormat] = useState<string>("MP4");
  const [fps, setFps] = useState<number>(0);
  const [resizeEnabled, setResizeEnabled] = useState(false);
  const [isBatchResult, setIsBatchResult] = useState(false);
  const [width, setWidth] = useState<string>("1920");
  const [height, setHeight] = useState<string>("1080");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [uploadProgress, setUploadProgress] = useState<FileUploadItem[]>([]);
  const [trimEnabled, setTrimEnabled] = useState(false);
  const [trimStart, setTrimStart] = useState<number>(0);
  const [trimEnd, setTrimEnd] = useState<number>(0);
  const [videoDuration, setVideoDuration] = useState<number>(0);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [result, setResult] = useState<VideoConversionResponse | null>(null);
  const [jobStatus, setJobStatus] = useState<string | null>(null);

  const apiBaseUrl = useMemo(
    () => process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000",
    [],
  );

  const handleFileChange = (event: ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(event.target.files ?? []);
    const file = files[0] ?? null;

    if (previewUrl) {
      URL.revokeObjectURL(previewUrl);
      setPreviewUrl(null);
    }

    setSelectedFile(file);
    setSelectedFiles(files);
    setVideoDuration(0);
    setTrimStart(0);
    setTrimEnd(0);
    setTrimEnabled(false);

    if (files.length === 1 && file) {
      setPreviewUrl(URL.createObjectURL(file));
      setTrimEnabled(true);
    }

    setErrorMessage(null);
    setResult(null);
    setJobStatus(null);
  };

  useEffect(() => {
    return () => {
      if (previewUrl) {
        URL.revokeObjectURL(previewUrl);
      }
    };
  }, [previewUrl]);

  const handleMetadataLoaded = (event: SyntheticEvent<HTMLVideoElement>) => {
    const duration = Number(event.currentTarget.duration);
    if (!Number.isFinite(duration) || duration <= 0) {
      setVideoDuration(0);
      setTrimStart(0);
      setTrimEnd(0);
      return;
    }

    const safeDuration = Number(duration.toFixed(2));
    setVideoDuration(safeDuration);
    setTrimStart(0);
    setTrimEnd(safeDuration);
  };

  const handleTrimStartChange = (value: number) => {
    const safeStart = Number.isFinite(value) ? value : 0;
    const nextStart = Math.max(0, Math.min(safeStart, Math.max(0, trimEnd - 0.1)));
    setTrimStart(Number(nextStart.toFixed(2)));
  };

  const handleTrimEndChange = (value: number) => {
    const floor = trimStart + 0.1;
    const safeEnd = Number.isFinite(value) ? value : floor;
    const nextEnd = Math.max(floor, Math.min(safeEnd, videoDuration || safeEnd));
    setTrimEnd(Number(nextEnd.toFixed(2)));
  };

  const handleTrimStartManual = (value: number) => {
    handleTrimStartChange(value);
  };

  const handleTrimEndManual = (value: number) => {
    handleTrimEndChange(value);
  };

  const trimStartPercent = videoDuration > 0 ? (trimStart / videoDuration) * 100 : 0;
  const trimEndPercent = videoDuration > 0 ? (trimEnd / videoDuration) * 100 : 100;

  const pollJobStatus = async (jobId: string, isBatch: boolean) => {
    for (let attempt = 0; attempt < 300; attempt += 1) {
      await new Promise((resolve) => window.setTimeout(resolve, 1000));

      const statusPath = isBatch ? `/batch/jobs/${jobId}` : `/video/jobs/${jobId}`;
      const response = await authFetch(`${apiBaseUrl}${statusPath}`, {
        cache: "no-store",
      });

      const payload = (await response.json()) as VideoJobStatusResponse | { detail?: string };

      if (!response.ok) {
        throw new Error("detail" in payload ? payload.detail ?? "Video job status check failed." : "Video job status check failed.");
      }

      const statusPayload = payload as VideoJobStatusResponse;
      setJobStatus(statusPayload.status);

      if (statusPayload.status === "completed") {
        setResult((previous) =>
          previous
            ? {
                ...previous,
                status: "completed",
                download_url: isBatch ? `/batch/jobs/${jobId}/download` : `/video/jobs/${jobId}/download`,
                output_filename: statusPayload.output_path?.split("/").pop() ?? null,
              }
            : previous,
        );
        return;
      }

      if (statusPayload.status === "failed") {
        throw new Error(statusPayload.error_message ?? "Video conversion failed.");
      }
    }

    throw new Error("Video conversion is taking longer than expected.");
  };

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    const isBatch = selectedFiles.length > 1;

    if (selectedFiles.length === 0) {
      setErrorMessage("Please choose a video file first.");
      return;
    }

    if (!isBatch && trimEnabled && videoDuration > 0 && trimEnd <= trimStart) {
      setErrorMessage("Trim end time must be greater than trim start time.");
      return;
    }

    setIsSubmitting(true);
    setErrorMessage(null);
    setResult(null);
    setJobStatus(null);
    setIsBatchResult(isBatch);
    setUploadProgress(selectedFiles.map((f) => ({ name: f.name, pct: 0 })));

    const formData = new FormData();
    if (isBatch) {
      for (const file of selectedFiles) {
        formData.append("files", file);
      }
    } else {
      formData.append("file", selectedFiles[0]!);
    }

    try {
      const query = new URLSearchParams({
        target_format: targetFormat,
        fps: String(fps),
        resize_enabled: String(resizeEnabled),
      });

      if (resizeEnabled) {
        query.set("width", width);
        query.set("height", height);
      }

      if (!isBatch && trimEnabled && videoDuration > 0) {
        query.set("trim_enabled", "true");
        query.set("trim_start", trimStart.toFixed(2));
        query.set("trim_end", trimEnd.toFixed(2));
      }

      const endpoint = isBatch ? "/batch/video/jobs" : "/video/jobs";
      const response = await xhrPost(
        `${apiBaseUrl}${endpoint}?${query.toString()}`,
        formData,
        (pct) => setUploadProgress(distributeProgress(selectedFiles, pct)),
      );
      setUploadProgress([]);

      const payload = (await response.json()) as VideoConversionResponse | { detail?: string };

      if (!response.ok) {
        throw new Error("detail" in payload ? payload.detail ?? "Video conversion failed." : "Video conversion failed.");
      }

      const conversionResult = payload as VideoConversionResponse;
      setResult(conversionResult);
      setJobStatus(conversionResult.status);
      await pollJobStatus(conversionResult.job_id, isBatch);
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : "Video conversion failed.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <section className="tool-card feature-card">
      <div className="section-heading compact-heading">
        <h2>Video converter</h2>
        <p>Upload video, choose target format, and optionally resize, set FPS, or trim using a minimal slider screen.</p>
      </div>

      <form className="converter-form" onSubmit={handleSubmit}>
        <label className="field-group">
          <span>Video file</span>
          <input className="file-input" type="file" accept=".mp4,.mov,.mkv,.avi,.webm,.gif" multiple onChange={handleFileChange} />
        </label>

        <div className="form-grid">
          <label className="field-group">
            <span>Target format</span>
            <select value={targetFormat} onChange={(event) => setTargetFormat(event.target.value)}>
              {videoFormats.map((format) => (
                <option key={format} value={format}>
                  {format}
                </option>
              ))}
            </select>
          </label>

          <label className="field-group">
            <span>FPS (0 keeps source)</span>
            <input type="number" min="0" value={fps} onChange={(event) => setFps(Number(event.target.value))} />
          </label>
        </div>

        <label className="checkbox-group">
          <input type="checkbox" checked={resizeEnabled} onChange={(event) => setResizeEnabled(event.target.checked)} />
          <span>Enable resize</span>
        </label>

        {resizeEnabled ? (
          <div className="form-grid">
            <label className="field-group">
              <span>Width</span>
              <input type="number" min="1" value={width} onChange={(event) => setWidth(event.target.value)} />
            </label>

            <label className="field-group">
              <span>Height</span>
              <input type="number" min="1" value={height} onChange={(event) => setHeight(event.target.value)} />
            </label>
          </div>
        ) : null}

        {selectedFiles.length === 1 && previewUrl ? (
          <section className="trim-card">
            <div className="trim-header">
              <h3>Trim</h3>
              <label className="checkbox-group">
                <input type="checkbox" checked={trimEnabled} onChange={(event) => setTrimEnabled(event.target.checked)} />
                <span>Enable trim</span>
              </label>
            </div>

            <video className="trim-preview" src={previewUrl} controls preload="metadata" onLoadedMetadata={handleMetadataLoaded} />

            <div className="trim-meta-row">
              <span>Duration: {videoDuration > 0 ? `${videoDuration.toFixed(2)}s` : "loading..."}</span>
              <span>
                Range: {trimStart.toFixed(2)}s → {trimEnd.toFixed(2)}s
              </span>
            </div>

            <div className="field-group">
              <span>Trim range</span>
              <div className="dual-range-wrapper">
                <div className="dual-range-base" />
                <div
                  className="dual-range-selected"
                  style={{
                    left: `${trimStartPercent}%`,
                    width: `${Math.max(0, trimEndPercent - trimStartPercent)}%`,
                  }}
                />

                <input
                  className="dual-range-input dual-range-input-start"
                  type="range"
                  min={0}
                  max={videoDuration > 0 ? videoDuration : 0}
                  step="0.1"
                  value={trimStart}
                  disabled={!trimEnabled || videoDuration <= 0}
                  onChange={(event) => handleTrimStartChange(Number(event.target.value))}
                />

                <input
                  className="dual-range-input dual-range-input-end"
                  type="range"
                  min={0}
                  max={videoDuration > 0 ? videoDuration : 0}
                  step="0.1"
                  value={trimEnd}
                  disabled={!trimEnabled || videoDuration <= 0}
                  onChange={(event) => handleTrimEndChange(Number(event.target.value))}
                />
              </div>

              <div className="trim-value-row">
                <span>Start: {trimStart.toFixed(2)}s</span>
                <span>End: {trimEnd.toFixed(2)}s</span>
              </div>

              <div className="trim-manual-row">
                <label className="field-group trim-manual-field">
                  <span>Start (manual)</span>
                  <input
                    type="number"
                    min={0}
                    max={videoDuration > 0 ? videoDuration : undefined}
                    step="0.1"
                    value={trimStart}
                    disabled={!trimEnabled || videoDuration <= 0}
                    onChange={(event) => handleTrimStartManual(Number(event.target.value))}
                  />
                </label>

                <label className="field-group trim-manual-field">
                  <span>End (manual)</span>
                  <input
                    type="number"
                    min={0}
                    max={videoDuration > 0 ? videoDuration : undefined}
                    step="0.1"
                    value={trimEnd}
                    disabled={!trimEnabled || videoDuration <= 0}
                    onChange={(event) => handleTrimEndManual(Number(event.target.value))}
                  />
                </label>
              </div>
            </div>

          </section>
        ) : null}

        {selectedFiles.length > 1 ? <p className="selection-hint">Trim is available for single file mode.</p> : null}

        <button className="primary-button" type="submit" disabled={isSubmitting}>
          {isSubmitting ? "Converting..." : "Convert video"}
        </button>
      </form>

      <UploadProgressPanel files={uploadProgress} />
      <ConversionLoader isVisible={isSubmitting && uploadProgress.length === 0} jobStatus={jobStatus} />

      {selectedFiles.length > 1 ? (
        <p className="selection-hint">
          Selected files: <strong>{selectedFiles.length}</strong>
        </p>
      ) : null}

      {selectedFiles.length === 1 && selectedFile ? (
        <p className="selection-hint">
          Selected file: <strong>{selectedFile.name}</strong>
        </p>
      ) : null}

      {errorMessage ? <p className="error-text">{errorMessage}</p> : null}

      {result ? (
        <div className="result-card">
          <h3>Video conversion state</h3>
          <p>
            <strong>Job:</strong> {result.job_id}
          </p>
          <p>
            <strong>Source:</strong> {result.original_filename}
          </p>
          <p>
            <strong>Format:</strong> {result.target_format}
          </p>
          <p>
            <strong>FPS:</strong> {result.fps}
          </p>
          <p>
            <strong>Resize:</strong> {result.resize_enabled ? `${result.width}x${result.height}` : "Disabled"}
          </p>
          <p>
            <strong>Status:</strong> {result.status}
          </p>
          {jobStatus ? (
            <p>
              <strong>Live status:</strong> {jobStatus}
            </p>
          ) : null}
          {result.download_url ? (
            <a className="primary-button inline-button" href={`${apiBaseUrl}${result.download_url}`} target="_blank" rel="noreferrer">
              Download {isBatchResult ? "zip bundle" : "converted video"}
            </a>
          ) : null}
        </div>
      ) : null}
    </section>
  );
}
