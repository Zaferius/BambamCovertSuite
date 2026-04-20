"use client";

/// <reference types="react" />
/// <reference types="react-dom" />
/// <reference types="node" />

import type { ChangeEvent, FormEvent } from "react";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { ConversionLoader } from "./conversion-loader";
import { type FileUploadItem, UploadProgressPanel } from "./upload-progress";
import { distributeProgress, xhrPost } from "../lib/xhr-post";
import { authFetch } from "../lib/auth-fetch";
import { buildApiUrl, isCompletedStatus, isFailedStatus } from "../lib/api";
import {
  AUDIO_ACCEPT_ATTR,
  AUDIO_BITRATES,
  AUDIO_FORMATS,
  AUDIO_TIME_FORMAT_PLACEHOLDER,
  JOB_STATUS,
  POLL_INTERVAL_MS,
} from "../lib/app-constants";


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

/** Parse "MM:SS.s" or plain seconds string → seconds, returns null on failure */
function mmssToSeconds(value: string): number | null {
  const trimmed = value.trim();
  const colonMatch = trimmed.match(/^(\d+):(\d+(?:\.\d+)?)$/);
  if (colonMatch) {
    return Number(colonMatch[1]) * 60 + Number(colonMatch[2]);
  }
  const plain = Number(trimmed);
  return Number.isFinite(plain) ? plain : null;
}


export function AudioConverter() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [targetFormat, setTargetFormat] = useState<string>("MP3");
  const [bitrate, setBitrate] = useState<string>("192k");
  const [isBatchResult, setIsBatchResult] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [uploadProgress, setUploadProgress] = useState<FileUploadItem[]>([]);
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
  const audioBufferRef = useRef<AudioBuffer | null>(null);
  const audioPlayerRef = useRef<HTMLAudioElement | null>(null);
  const audioObjectUrlRef = useRef<string | null>(null);
  const rafIdRef = useRef<number | null>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [playhead, setPlayhead] = useState(0);
  const [volume, setVolume] = useState(1.0);

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

  // Decode audio data — store buffer in ref, then flip waveformReady to mount the canvas
  useEffect(() => {
    if (!selectedFile || selectedFiles.length !== 1) return;

    let cancelled = false;
    setWaveformReady(false);
    setAudioDuration(0);
    audioBufferRef.current = null;
    setIsPlaying(false);
    setPlayhead(0);

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
        audioBufferRef.current = audioBuffer;
        setWaveformReady(true);
        await audioCtx.close();
      } catch {
        // decode failed — waveform won't show
      }
    };
    reader.readAsArrayBuffer(selectedFile);

    return () => {
      cancelled = true;
      audioPlayerRef.current?.pause();
      audioPlayerRef.current = null;
      if (audioObjectUrlRef.current) {
        URL.revokeObjectURL(audioObjectUrlRef.current);
        audioObjectUrlRef.current = null;
      }
      if (rafIdRef.current !== null) {
        window.cancelAnimationFrame(rafIdRef.current);
        rafIdRef.current = null;
      }
    };
  }, [selectedFile, selectedFiles.length]);

  // Draw waveform AFTER canvas is mounted (waveformReady=true triggers re-render → canvas appears)
  useEffect(() => {
    if (!waveformReady || !audioBufferRef.current) return;
    const buf = audioBufferRef.current;
    const raf = window.requestAnimationFrame(() => drawWaveform(buf));
    return () => window.cancelAnimationFrame(raf);
  }, [waveformReady, drawWaveform, trimEnabled]);

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

  // ─── Play preview ─────────────────────────────────────────────────────────

  const handlePlayPreview = useCallback(() => {
    if (isPlaying) {
      if (rafIdRef.current !== null) {
        window.cancelAnimationFrame(rafIdRef.current);
        rafIdRef.current = null;
      }
      audioPlayerRef.current?.pause();
      setIsPlaying(false);
      return;
    }

    if (!selectedFile || audioDuration <= 0) return;

    if (audioObjectUrlRef.current) {
      URL.revokeObjectURL(audioObjectUrlRef.current);
    }

    const url = URL.createObjectURL(selectedFile);
    audioObjectUrlRef.current = url;

    const audio = new Audio(url);
    audio.volume = volume;
    audio.currentTime = trimStart;
    audioPlayerRef.current = audio;

    const capturedEnd = trimEnd;
    const capturedStart = trimStart;

    const tick = () => {
      if (!audioPlayerRef.current) return;
      const t = audioPlayerRef.current.currentTime;
      setPlayhead(t);
      if (t >= capturedEnd) {
        audioPlayerRef.current.pause();
        setIsPlaying(false);
        setPlayhead(capturedStart);
        rafIdRef.current = null;
        return;
      }
      rafIdRef.current = window.requestAnimationFrame(tick);
    };

    const onEnded = () => {
      if (rafIdRef.current !== null) {
        window.cancelAnimationFrame(rafIdRef.current);
        rafIdRef.current = null;
      }
      setIsPlaying(false);
      setPlayhead(capturedStart);
    };

    audio.addEventListener("ended", onEnded);

    audio.play().then(() => {
      setIsPlaying(true);
      setPlayhead(capturedStart);
      rafIdRef.current = window.requestAnimationFrame(tick);
    }).catch(() => setIsPlaying(false));
  }, [isPlaying, selectedFile, audioDuration, trimStart, trimEnd, volume]);

  useEffect(() => {
    if (audioPlayerRef.current) {
      audioPlayerRef.current.volume = volume;
    }
  }, [volume]);

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
    if (rafIdRef.current !== null) {
      window.cancelAnimationFrame(rafIdRef.current);
      rafIdRef.current = null;
    }
    audioPlayerRef.current?.pause();
    audioPlayerRef.current = null;
    setIsPlaying(false);
    setPlayhead(0);
  };

  // ─── Polling ──────────────────────────────────────────────────────────────

  const pollJobStatus = async (jobId: string, isBatch: boolean) => {
    for (let attempt = 0; attempt < 120; attempt += 1) {
      await new Promise((resolve) => window.setTimeout(resolve, POLL_INTERVAL_MS));

      const statusPath = isBatch ? `/batch/jobs/${jobId}` : `/audio/jobs/${jobId}`;
      const response = await authFetch(buildApiUrl(statusPath), { cache: "no-store" });
      const payload = (await response.json()) as AudioJobStatusResponse | ApiErrorResponse;

      if (!response.ok) {
        throw new Error("detail" in payload ? payload.detail ?? "Audio job status check failed." : "Audio job status check failed.");
      }

      const statusPayload = payload as AudioJobStatusResponse;
      setJobStatus(statusPayload.status);

      if (isCompletedStatus(statusPayload.status)) {
        setResult((previous: PollingResultUpdater) =>
          previous
            ? {
              ...previous,
              status: JOB_STATUS.completed,
              download_url: isBatch ? `/batch/jobs/${jobId}/download` : `/audio/jobs/${jobId}/download`,
              output_filename: statusPayload.output_path?.split("/").pop() ?? null,
            }
            : previous,
        );
        return;
      }

      if (isFailedStatus(statusPayload.status)) {
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
    setUploadProgress(selectedFiles.map((f) => ({ name: f.name, pct: 0 })));

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
      const response = await xhrPost(
        buildApiUrl(`${endpoint}?${query.toString()}`),
        formData,
        (pct) => setUploadProgress(distributeProgress(selectedFiles, pct)),
      );
      setUploadProgress([]);

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
          <input className="file-input" type="file" accept={AUDIO_ACCEPT_ATTR} multiple onChange={handleFileChange} />
        </label>

        {selectedFiles.length > 0 && (
          <div className="converter-settings-reveal">
            <div className="form-grid">
              <label className="field-group">
                <span>Target format</span>
                <select value={targetFormat} onChange={(e: ChangeEvent<HTMLSelectElement>) => setTargetFormat(e.target.value)}>
                  {AUDIO_FORMATS.map((f) => (
                    <option key={f} value={f}>{f}</option>
                  ))}
                </select>
              </label>

              <label className="field-group">
                <span>Bitrate</span>
                <select value={bitrate} onChange={(e: ChangeEvent<HTMLSelectElement>) => setBitrate(e.target.value)}>
                  {AUDIO_BITRATES.map((v) => (
                    <option key={v} value={v}>{v}</option>
                  ))}
                </select>
              </label>
            </div>

            {selectedFiles.length === 1 && (
              <div className="feature-toggles-row">
                <button
                  type="button"
                  className={`feature-toggle-btn${trimEnabled ? " active" : ""}`}
                  onClick={() => setTrimEnabled((v) => !v)}
                >
                  <span className="feature-toggle-dot" />
                  Trim
                </button>
              </div>
            )}

            {selectedFiles.length === 1 && trimEnabled && !waveformReady && (
              <p className="waveform-decoding">Decoding waveform…</p>
            )}

            {selectedFiles.length === 1 && trimEnabled && waveformReady ? (
              <section className="trim-card">
                <div className="trim-header">
                  <h3>Trim</h3>
                </div>

                <div
                  ref={waveformAreaRef}
                  className="waveform-area"
                  style={{ userSelect: "none" }}
                >
                  <span className="waveform-filename">{selectedFile?.name}</span>

                  <canvas ref={canvasRef} className="waveform-canvas" />

                  <div className="waveform-mask" style={{ left: 0, width: `${startPct}%` }} />
                  <div className="waveform-mask" style={{ right: 0, width: `${100 - endPct}%` }} />

                  <div
                    className="waveform-handle"
                    style={{ left: `${startPct}%` }}
                    onMouseDown={(e) => { e.preventDefault(); setIsDragging("start"); }}
                  >
                    <div className="waveform-handle-grip" />
                  </div>

                  <div
                    className="waveform-handle"
                    style={{ left: `${endPct}%` }}
                    onMouseDown={(e) => { e.preventDefault(); setIsDragging("end"); }}
                  >
                    <div className="waveform-handle-grip" />
                  </div>

                  {audioDuration > 0 && (
                    <div
                      className="waveform-playhead"
                      style={{ left: `${(playhead / audioDuration) * 100}%` }}
                    />
                  )}
                </div>

                <div className="waveform-timestamps">
                  <span>{formatTime(trimStart)}</span>
                  <span className="waveform-time-center">{formatTime(audioDuration)}</span>
                  <span>{formatTime(trimEnd)}</span>
                </div>

                <div className="waveform-controls-row">
                  <button
                    type="button"
                    className="trim-play-btn"
                    onClick={handlePlayPreview}
                    title={isPlaying ? "Pause preview" : "Play preview (trimmed range)"}
                  >
                    {isPlaying ? (
                      <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
                        <path d="M5.5 3.5A1.5 1.5 0 0 1 7 5v6a1.5 1.5 0 0 1-3 0V5a1.5 1.5 0 0 1 1.5-1.5zm5 0A1.5 1.5 0 0 1 12 5v6a1.5 1.5 0 0 1-3 0V5a1.5 1.5 0 0 1 1.5-1.5z" />
                      </svg>
                    ) : (
                      <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
                        <path d="m11.596 8.697-6.363 3.692c-.54.313-1.233-.066-1.233-.697V4.308c0-.63.692-1.01 1.233-.696l6.363 3.692a.802.802 0 0 1 0 1.393z" />
                      </svg>
                    )}
                  </button>
                  <span className="trim-playhead-time">{formatTime(isPlaying ? playhead : trimStart)}</span>
                  <div className="trim-volume-group">
                    <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" fill="currentColor" viewBox="0 0 16 16" className="trim-volume-icon">
                      <path d="M11.536 14.01A8.473 8.473 0 0 0 14.026 8a8.473 8.473 0 0 0-2.49-6.01l-.708.707A7.476 7.476 0 0 1 13.025 8c0 2.071-.84 3.946-2.197 5.303l.708.707z" />
                      <path d="M10.121 12.596A6.48 6.48 0 0 0 12.025 8a6.48 6.48 0 0 0-1.904-4.596l-.707.707A5.483 5.483 0 0 1 11.025 8a5.483 5.483 0 0 1-1.61 3.89l.706.706z" />
                      <path d="M8.707 11.182A4.486 4.486 0 0 0 10.025 8a4.486 4.486 0 0 0-1.318-3.182L8 5.525A3.489 3.489 0 0 1 9.025 8 3.49 3.49 0 0 1 8 10.475l.707.707zM6.717 3.55A.5.5 0 0 1 7 4v8a.5.5 0 0 1-.812.39L3.825 10.5H1.5A.5.5 0 0 1 1 10V6a.5.5 0 0 1 .5-.5h2.325l2.363-1.89a.5.5 0 0 1 .529-.06z" />
                    </svg>
                    <input
                      type="range"
                      min={0}
                      max={1}
                      step={0.01}
                      value={volume}
                      onChange={(e) => setVolume(Number(e.target.value))}
                      className="trim-volume-slider"
                    />
                    <span className="trim-volume-pct">{Math.round(volume * 100)}%</span>
                  </div>
                </div>

                <div className="trim-meta-row">
                  <span>Duration: {audioDuration > 0 ? `${audioDuration.toFixed(2)}s` : "loading…"}</span>
                  <span>Range: {trimStart.toFixed(2)}s → {trimEnd.toFixed(2)}s</span>
                </div>

                <div className="trim-manual-row">
                  <label className="field-group trim-manual-field">
                    <span>Start (MM:SS.s)</span>
                    <input
                      key={trimStart}
                      type="text"
                      defaultValue={formatTime(trimStart)}
                      placeholder={AUDIO_TIME_FORMAT_PLACEHOLDER}
                      onBlur={(e) => {
                        const s = mmssToSeconds(e.target.value);
                        if (s !== null) setTrimStart(Number(Math.min(Math.max(s, 0), trimEnd - 0.1).toFixed(2)));
                      }}
                    />
                  </label>
                  <label className="field-group trim-manual-field">
                    <span>End (MM:SS.s)</span>
                    <input
                      key={trimEnd}
                      type="text"
                      defaultValue={formatTime(trimEnd)}
                      placeholder={AUDIO_TIME_FORMAT_PLACEHOLDER}
                      onBlur={(e) => {
                        const s = mmssToSeconds(e.target.value);
                        if (s !== null) setTrimEnd(Number(Math.max(Math.min(s, audioDuration), trimStart + 0.1).toFixed(2)));
                      }}
                    />
                  </label>
                </div>
              </section>
            ) : null}

            {selectedFiles.length > 1 && (
              <p className="selection-hint">Trim is available for single file mode only.</p>
            )}

            <button className="primary-button" type="submit" disabled={isSubmitting}>
              {uploadProgress.length > 0 ? "Uploading..." : isSubmitting ? "Converting..." : "Convert audio"}
            </button>
          </div>
        )}
      </form>

      <UploadProgressPanel files={uploadProgress} />
      <ConversionLoader isVisible={isSubmitting && uploadProgress.length === 0} jobStatus={jobStatus} />

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
            <a className="primary-button inline-button" href={buildApiUrl(result.download_url)} target="_blank" rel="noreferrer">
              Download {isBatchResult ? "zip bundle" : "converted audio"}
            </a>
          ) : null}
        </div>
      ) : null}
    </section>
  );
}
