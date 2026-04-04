"use client";

import { ChangeEvent, FormEvent, useMemo, useState } from "react";


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
    setSelectedFile(file);
    setSelectedFiles(files);
    setErrorMessage(null);
    setResult(null);
    setJobStatus(null);
  };

  const pollJobStatus = async (jobId: string, isBatch: boolean) => {
    for (let attempt = 0; attempt < 300; attempt += 1) {
      await new Promise((resolve) => window.setTimeout(resolve, 1000));

      const statusPath = isBatch ? `/batch/jobs/${jobId}` : `/video/jobs/${jobId}`;
      const response = await fetch(`${apiBaseUrl}${statusPath}`, {
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

    setIsSubmitting(true);
    setErrorMessage(null);
    setResult(null);
    setJobStatus(null);
    setIsBatchResult(isBatch);

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

      const endpoint = isBatch ? "/batch/video/jobs" : "/video/jobs";
      const response = await fetch(`${apiBaseUrl}${endpoint}?${query.toString()}`, {
        method: "POST",
        body: formData,
      });

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
        <p>Upload a single video, choose target format, optional FPS, and optional resize settings.</p>
      </div>

      <form className="converter-form" onSubmit={handleSubmit}>
        <label className="field-group">
          <span>Video file</span>
          <input className="file-input" type="file" accept="video/*" multiple onChange={handleFileChange} />
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

        <button className="primary-button" type="submit" disabled={isSubmitting}>
          {isSubmitting ? "Converting..." : "Convert video"}
        </button>
      </form>

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
