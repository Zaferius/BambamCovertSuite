"use client";

/// <reference types="react" />
/// <reference types="react-dom" />
/// <reference types="node" />

import type { ChangeEvent, FormEvent } from "react";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { ConversionLoader } from "./conversion-loader";


const audioFormats = ["MP3", "WAV", "FLAC", "OGG", "M4A", "AAC"] as const;
const audioBitrates = ["128k", "192k", "256k", "320k"] as const;

type AudioConversionResponse = {
  job_id: string;
  status: string;
  target_format: string;
  bitrate: string;
  original_filename: string;
  output_filename?: string | null;
  download_url?: string | null;
};

type AudioJobStatusResponse = {
  id: string;
  status: string;
  output_path?: string | null;
  error_message?: string | null;
};

type ApiErrorResponse = {
  detail?: string;
};

type AudioCreateResponse = AudioConversionResponse & {
  item_count?: number;
};

type PollingResultUpdater = AudioConversionResponse | null;


function formatTime(s: number): string {
  const m = Math.floor(s / 60);
  const sec = (s % 60).toFixed(1).padStart(4, "0");
  return `${String(m).padStart(2, "0")}:${sec}`;
}


export function AudioConverter() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [targetFormat, setTargetFormat] = useState<string>("MP3");
  const [bitrate, setBitrate] = useState<string>("192k");
  const [isBatchResult, setIsBatchResult] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [result, setResult] = useState<AudioConversionResponse | null>(null);
  const [jobStatus, setJobStatus] = useState<string | null>(null);

  // Trim / waveform state
  const [trimEnabled, setTrimEnabled] = useState(false);
  const [trimStart, setTrimStart] = useState(0);
  const [trimEnd, setTrimEnd] = useState(0);
  const [audioDuration, setAudioDuration] = useState(0);
  const [waveformReady, setWaveformReady] = useState(false);
  const [isDragging, setIsDragging] = useState<"start" | "end" | null>(null);

  const canvasRef = useRef<HTMLCanvasElement>(null);
  const waveformAreaRef = useRef<HTMLDivElement>(null);

  const apiBaseUrl = useMemo(
    () => process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000",
    [],
  );

  // ─── Waveform drawing ─────────────────────────────────────────────────────

  const drawWaveform = useCallback((audioBuffer: AudioBuffer) => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const dpr = window.devicePixelRatio || 1;
    const cssWidth = canvas.offsetWidth || 800;
    const cssHeight = canvas.offsetHeight || 130;

    canvas.width = cssWidth * dpr;
    canvas.height = cssHeight * dpr;
    ctx.scale(dpr, dpr);

    const width = cssWidth;
    const height = cssHeight;

    ctx.fillStyle = "#0a1628";
    ctx.fillRect(0, 0, width, height);

    const channelData = audioBuffer.getChannelData(0);
    const step = Math.max(1, Math.floor(channelData.length / width));

    ctx.strokeStyle = "#00e87a";
    ctx.lineWidth = 1;
    ctx.beginPath();

    for (let i = 0; i < width; i++) {
      const offset = i * step;
      let min = 1.0;
      let max = -1.0;
      for (let j = 0; j < step; j++) {
        const v = channelData[offset + j] ?? 0;
        if (v < min) min = v;
        if (v > max) max = v;
      }
      const y1 = ((1 - max) / 2) * height;
      const y2 = ((1 - min) / 2) * height;
      ctx.moveTo(i + 0.5, y1);
      ctx.lineTo(i + 0.5, Math.max(y1 + 1, y2));
    }
    ctx.stroke();
  }, []);

  // Decode + draw when a single file is selected
  useEffect(() => {
    if (!selectedFile || selectedFiles.length !== 1) return;

    let cancelled = false;
    setWaveformReady(false);
    setAudioDuration(0);

    const reader = new FileReader();
    reader.onload = async (e) => {
      if (cancelled) return;
      const arrayBuffer = e.target?.result as ArrayBuffer;
      try {
        const audioCtx = new AudioContext();
        const audioBuffer = await audioCtx.decodeAudioData(arrayBuffer.slice(0));
        if (cancelled) { await audioCtx.close(); return; }
        const duration = Number(audioBuffer.duration.toFixed(2));
        setAudioDuration(duration);
        setTrimStart(0);
        setTrimEnd(duration);
        window.requestAnimationFrame(() => {
          if (!cancelled) drawWaveform(audioBuffer);
        });
        setWaveformReady(true);
        await audioCtx.close();
      } catch {
        // decode failed — waveform won't show
      }
    };
    reader.readAsArrayBuffer(selectedFile);

    return () => { cancelled = true; };
  }, [selectedFile, selectedFiles.length, drawWaveform]);

  // ─── Drag handling ────────────────────────────────────────────────────────

  const xToTime = useCallback(
    (clientX: number): number => {
      const area = waveformAreaRef.current;
      if (!area || audioDuration <= 0) return 0;
      const rect = area.getBoundingClientRect();
      const ratio = Math.max(0, Math.min((clientX - rect.left) / rect.width, 1));
      return Number((ratio * audioDuration).toFixed(2));
    },
    [audioDuration],
  );

  useEffect(() => {
    if (!isDragging) return;

    const onMouseMove = (e: MouseEvent) => {
      const t = xToTime(e.clientX);
      if (isDragging === "start") {
        setTrimStart(Math.min(t, trimEnd - 0.1));
      } else {
        setTrimEnd(Math.max(t, trimStart + 0.1));
      }
    };
    const onMouseUp = () => setIsDragging(null);

    document.addEventListener("mousemove", onMouseMove);
    document.addEventListener("mouseup", onMouseUp);
    return () => {
      document.removeEventListener("mousemove", onMouseMove);
      document.removeEventListener("mouseup", onMouseUp);
    };
  }, [isDragging, xToTime, trimStart, trimEnd]);

  const startPct = audioDuration > 0 ? (trimStart / audioDuration) * 100 : 0;
  const endPct = audioDuration > 0 ? (trimEnd / audioDuration) * 100 : 100;

  // ─── File change ──────────────────────────────────────────────────────────

  const handleFileChange = (event: ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(event.target.files ?? []);
    const file = files[0] ?? null;
    setSelectedFile(file);
    setSelectedFiles(files);
    setErrorMessage(null);
    setResult(null);
    setJobStatus(null);
    setWaveformReady(false);
    setAudioDuration(0);
    setTrimEnabled(false);
    setTrimStart(0);
    setTrimEnd(0);
  };

  // ─── Polling ──────────────────────────────────────────────────────────────

  const pollJobStatus = async (jobId: string, isBatch: boolean) => {
    for (let attempt = 0; attempt < 120; attempt += 1) {
      await new Promise((resolve) => window.setTimeout(resolve, 1000));

      const statusPath = isBatch ? `/batch/jobs/${jobId}` : `/audio/jobs/${jobId}`;
      const response = await fetch(`${apiBaseUrl}${statusPath}`, { cache: "no-store" });
      const payload = (await response.json()) as AudioJobStatusResponse | ApiErrorResponse;

      if (!response.ok) {
        throw new Error("detail" in payload ? payload.detail ?? "Audio job status check failed." : "Audio job status check failed.");
      }

      const statusPayload = payload as AudioJobStatusResponse;
      setJobStatus(statusPayload.status);

      if (statusPayload.status === "completed") {
        setResult((previous: PollingResultUpdater) =>
          previous
            ? {
                ...previous,
                status: "completed",
                download_url: isBatch ? `/batch/jobs/${jobId}/download` : `/audio/jobs/${jobId}/download`,
                output_filename: statusPayload.output_path?.split("/").pop() ?? null,
              }
            : previous,
        );
        return;
      }

      if (statusPayload.status === "failed") {
        throw new Error(statusPayload.error_message ?? "Audio conversion failed.");
      }
    }

    throw new Error("Audio conversion is taking longer than expected.");
  };

  // ─── Submit ───────────────────────────────────────────────────────────────

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    const isBatch = selectedFiles.length > 1;

    if (selectedFiles.length === 0) {
      setErrorMessage("Please choose an audio file first.");
      return;
    }

    if (!isBatch && trimEnabled && audioDuration > 0 && trimEnd <= trimStart) {
      setErrorMessage("Trim end time must be greater than trim start time.");
      return;
    }

    setIsSubmitting(true);
    setErrorMessage(null);
    setResult(null);
    setJobStatus(null);
    setIsBatchResult(isBatch);

    const formData = new FormData();
    if (isBatch) {
      for (const file of selectedFiles) formData.append("files", file);
    } else {
      formData.append("file", selectedFiles[0]!);
    }

    try {
      const query = new URLSearchParams({ target_format: targetFormat, bitrate });

      if (!isBatch && trimEnabled && audioDuration > 0) {
        query.set("trim_enabled", "true");
        query.set("trim_start", trimStart.toFixed(2));
        query.set("trim_end", trimEnd.toFixed(2));
      }

      const endpoint = isBatch ? "/batch/audio/jobs" : "/audio/jobs";
      const response = await fetch(`${apiBaseUrl}${endpoint}?${query.toString()}`, {
        method: "POST",
        body: formData,
      });

      const payload = (await response.json()) as AudioCreateResponse | ApiErrorResponse;

      if (!response.ok) {
        throw new Error("detail" in payload ? payload.detail ?? "Audio conversion failed." : "Audio conversion failed.");
      }

      const conversionResult = payload as AudioCreateResponse;
      setResult(conversionResult);
      setJobStatus(conversionResult.status);
      await pollJobStatus(conversionResult.job_id, isBatch);
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : "Audio conversion failed.");
    } finally {
      setIsSubmitting(false);
    }
  };

  // ─── Render ───────────────────────────────────────────────────────────────

  return (
    <section className="tool-card feature-card">
      <div className="section-heading compact-heading">
        <h2>Sound converter</h2>
        <p>Upload a single audio file, choose output format and bitrate, then download the converted result.</p>
      </div>

      <form className="converter-form" onSubmit={handleSubmit}>
        <label className="field-group">
          <span>Audio file</span>
          <input className="file-input" type="file" accept="audio/*" multiple onChange={handleFileChange} />
        </label>

        <div className="form-grid">
          <label className="field-group">
            <span>Target format</span>
            <select value={targetFormat} onChange={(e: ChangeEvent<HTMLSelectElement>) => setTargetFormat(e.target.value)}>
              {audioFormats.map((f) => (
                <option key={f} value={f}>{f}</option>
              ))}
            </select>
          </label>

          <label className="field-group">
            <span>Bitrate</span>
            <select value={bitrate} onChange={(e: ChangeEvent<HTMLSelectElement>) => setBitrate(e.target.value)}>
              {audioBitrates.map((v) => (
                <option key={v} value={v}>{v}</option>
              ))}
            </select>
          </label>
        </div>

        {/* Waveform trim — single file only */}
        {selectedFiles.length === 1 && waveformReady ? (
          <section className="trim-card">
            <div className="trim-header">
              <h3>Trim</h3>
              <label className="checkbox-group">
                <input
                  type="checkbox"
                  checked={trimEnabled}
                  onChange={(e) => setTrimEnabled(e.target.checked)}
                />
                <span>Enable trim</span>
              </label>
            </div>

            {/* Waveform canvas + draggable handles */}
            <div
              ref={waveformAreaRef}
              className="waveform-area"
              style={{ userSelect: "none" }}
            >
              <span className="waveform-filename">{selectedFile?.name}</span>

              <canvas ref={canvasRef} className="waveform-canvas" />

              {/* Dark masks over non-selected regions */}
              <div className="waveform-mask" style={{ left: 0, width: `${startPct}%` }} />
              <div className="waveform-mask" style={{ right: 0, width: `${100 - endPct}%` }} />

              {/* Start handle */}
              <div
                className="waveform-handle"
                style={{ left: `${startPct}%`, opacity: trimEnabled ? 1 : 0.4 }}
                onMouseDown={(e) => {
                  if (!trimEnabled) return;
                  e.preventDefault();
                  setIsDragging("start");
                }}
              >
                <div className="waveform-handle-grip" />
              </div>

              {/* End handle */}
              <div
                className="waveform-handle"
                style={{ left: `${endPct}%`, opacity: trimEnabled ? 1 : 0.4 }}
                onMouseDown={(e) => {
                  if (!trimEnabled) return;
                  e.preventDefault();
                  setIsDragging("end");
                }}
              >
                <div className="waveform-handle-grip" />
              </div>
            </div>

            {/* Timestamps */}
            <div className="waveform-timestamps">
              <span>{formatTime(trimStart)}</span>
              <span className="waveform-time-center">{formatTime(audioDuration)}</span>
              <span>{formatTime(trimEnd)}</span>
            </div>

            <div className="trim-meta-row">
              <span>Duration: {audioDuration > 0 ? `${audioDuration.toFixed(2)}s` : "loading…"}</span>
              <span>Range: {trimStart.toFixed(2)}s → {trimEnd.toFixed(2)}s</span>
            </div>

            {/* Manual inputs */}
            <div className="trim-manual-row">
              <label className="field-group trim-manual-field">
                <span>Start (manual)</span>
                <input
                  type="number"
                  min={0}
                  max={audioDuration}
                  step="0.1"
                  value={trimStart}
                  disabled={!trimEnabled}
                  onChange={(e) => {
                    const v = Number(e.target.value);
                    setTrimStart(Number(Math.min(v, trimEnd - 0.1).toFixed(2)));
                  }}
                />
              </label>
              <label className="field-group trim-manual-field">
                <span>End (manual)</span>
                <input
                  type="number"
                  min={0}
                  max={audioDuration}
                  step="0.1"
                  value={trimEnd}
                  disabled={!trimEnabled}
                  onChange={(e) => {
                    const v = Number(e.target.value);
                    setTrimEnd(Number(Math.max(v, trimStart + 0.1).toFixed(2)));
                  }}
                />
              </label>
            </div>
          </section>
        ) : null}

        {selectedFiles.length > 1 ? (
          <p className="selection-hint">Trim is available for single file mode only.</p>
        ) : null}

        <button className="primary-button" type="submit" disabled={isSubmitting}>
          {isSubmitting ? "Converting..." : "Convert audio"}
        </button>
      </form>

      <ConversionLoader isVisible={isSubmitting} jobStatus={jobStatus} />

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
          <h3>Audio conversion state</h3>
          <p><strong>Job:</strong> {result.job_id}</p>
          <p><strong>Source:</strong> {result.original_filename}</p>
          <p><strong>Format:</strong> {result.target_format}</p>
          <p><strong>Bitrate:</strong> {result.bitrate}</p>
          <p><strong>Status:</strong> {result.status}</p>
          {jobStatus ? <p><strong>Live status:</strong> {jobStatus}</p> : null}
          {result.download_url ? (
            <a className="primary-button inline-button" href={`${apiBaseUrl}${result.download_url}`} target="_blank" rel="noreferrer">
              Download {isBatchResult ? "zip bundle" : "converted audio"}
            </a>
          ) : null}
        </div>
      ) : null}
    </section>
  );
}
