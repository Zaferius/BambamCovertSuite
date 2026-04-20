"use client";

import { ChangeEvent, FormEvent, MouseEvent as ReactMouseEvent, SyntheticEvent, useEffect, useState, useRef, useCallback } from "react";
import { ConversionLoader } from "./conversion-loader";
import { type FileUploadItem, UploadProgressPanel } from "./upload-progress";
import { distributeProgress, xhrPost } from "../lib/xhr-post";
import { authFetch } from "../lib/auth-fetch";
import { useAction } from "../lib/action-context";
import { buildApiUrl, isCompletedStatus, isFailedStatus } from "../lib/api";
import { AUDIO_TIME_FORMAT_PLACEHOLDER, JOB_STATUS, POLL_INTERVAL_MS, VIDEO_ACCEPT_ATTR, VIDEO_FORMATS } from "../lib/app-constants";

function formatTime(s: number): string {
  const m = Math.floor(s / 60);
  const sec = (s % 60).toFixed(1).padStart(4, "0");
  return `${String(m).padStart(2, "0")}:${sec}`;
}

function mmssToSeconds(value: string): number | null {
  const trimmed = value.trim();
  const colonMatch = trimmed.match(/^(\d+):(\d+(?:\.\d+)?)$/);
  if (colonMatch) {
    return Number(colonMatch[1]) * 60 + Number(colonMatch[2]);
  }
  const plain = Number(trimmed);
  return Number.isFinite(plain) ? plain : null;
}

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

type ResizeHandle = "n" | "s" | "e" | "w" | "ne" | "nw" | "se" | "sw";


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

  const [isDragging, setIsDragging] = useState<"start" | "end" | null>(null);
  const waveformAreaRef = useRef<HTMLDivElement>(null);
  const videoRef = useRef<HTMLVideoElement>(null);
  const resizeStageRef = useRef<HTMLDivElement>(null);
  const [sourceWidth, setSourceWidth] = useState<number>(1920);
  const [sourceHeight, setSourceHeight] = useState<number>(1080);
  const [activeResizeHandle, setActiveResizeHandle] = useState<ResizeHandle | null>(null);
  const [isMovingOverlay, setIsMovingOverlay] = useState(false);
  const [overlayRect, setOverlayRect] = useState({ left: 0, top: 0, w: 1, h: 1 });
  const resizeDragStartRef = useRef<{
    startX: number;
    startY: number;
    stageRect: DOMRect;
    snapLeft: number;
    snapTop: number;
    snapW: number;
    snapH: number;
  } | null>(null);

  const { setAction } = useAction();

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
    const media = event.currentTarget;
    const duration = Number(media.duration);
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

    const naturalWidth = Math.max(1, Number(media.videoWidth) || 1);
    const naturalHeight = Math.max(1, Number(media.videoHeight) || 1);
    setSourceWidth(naturalWidth);
    setSourceHeight(naturalHeight);

    setOverlayRect({ left: 0, top: 0, w: 1, h: 1 });
    setWidth(String(naturalWidth));
    setHeight(String(naturalHeight));
  };

  useEffect(() => {
    const video = videoRef.current;
    if (!video) return;
    if (resizeEnabled) video.pause();
  }, [resizeEnabled]);

  useEffect(() => {
    if (!activeResizeHandle) return;

    const onMouseMove = (e: MouseEvent) => {
      const start = resizeDragStartRef.current;
      if (!start) return;

      const dxF = (e.clientX - start.startX) / start.stageRect.width;
      const dyF = (e.clientY - start.startY) / start.stageRect.height;

      let left = start.snapLeft;
      let top = start.snapTop;
      let w = start.snapW;
      let h = start.snapH;

      if (activeResizeHandle.includes("e")) {
        w = Math.max(0.05, Math.min(1 - left, w + dxF));
      }
      if (activeResizeHandle.includes("w")) {
        const newLeft = Math.max(0, Math.min(left + w - 0.05, left + dxF));
        w = left + w - newLeft;
        left = newLeft;
      }
      if (activeResizeHandle.includes("s")) {
        h = Math.max(0.05, Math.min(1 - top, h + dyF));
      }
      if (activeResizeHandle.includes("n")) {
        const newTop = Math.max(0, Math.min(top + h - 0.05, top + dyF));
        h = top + h - newTop;
        top = newTop;
      }

      setOverlayRect({ left, top, w, h });
      setWidth(String(Math.max(2, Math.round(w * sourceWidth))));
      setHeight(String(Math.max(2, Math.round(h * sourceHeight))));
    };

    const onTouchMove = (e: TouchEvent) => {
      e.preventDefault();
      const touch = e.touches[0];
      if (!touch) return;
      const start = resizeDragStartRef.current;
      if (!start) return;

      const dxF = (touch.clientX - start.startX) / start.stageRect.width;
      const dyF = (touch.clientY - start.startY) / start.stageRect.height;

      let left = start.snapLeft;
      let top = start.snapTop;
      let w = start.snapW;
      let h = start.snapH;

      if (activeResizeHandle.includes("e")) {
        w = Math.max(0.05, Math.min(1 - left, w + dxF));
      }
      if (activeResizeHandle.includes("w")) {
        const newLeft = Math.max(0, Math.min(left + w - 0.05, left + dxF));
        w = left + w - newLeft;
        left = newLeft;
      }
      if (activeResizeHandle.includes("s")) {
        h = Math.max(0.05, Math.min(1 - top, h + dyF));
      }
      if (activeResizeHandle.includes("n")) {
        const newTop = Math.max(0, Math.min(top + h - 0.05, top + dyF));
        h = top + h - newTop;
        top = newTop;
      }

      setOverlayRect({ left, top, w, h });
      setWidth(String(Math.max(2, Math.round(w * sourceWidth))));
      setHeight(String(Math.max(2, Math.round(h * sourceHeight))));
    };

    const onMouseUp = () => {
      setActiveResizeHandle(null);
      resizeDragStartRef.current = null;
    };

    document.addEventListener("mousemove", onMouseMove);
    document.addEventListener("touchmove", onTouchMove, { passive: false });
    document.addEventListener("mouseup", onMouseUp);
    document.addEventListener("touchend", onMouseUp);
    return () => {
      document.removeEventListener("mousemove", onMouseMove);
      document.removeEventListener("touchmove", onTouchMove);
      document.removeEventListener("mouseup", onMouseUp);
      document.removeEventListener("touchend", onMouseUp);
    };
  }, [activeResizeHandle, sourceWidth, sourceHeight]);

  const startResizeDrag = (handle: ResizeHandle) => (e: ReactMouseEvent<HTMLButtonElement>) => {
    e.preventDefault();
    e.stopPropagation();
    const stage = resizeStageRef.current;
    if (!stage) return;
    resizeDragStartRef.current = {
      startX: e.clientX,
      startY: e.clientY,
      stageRect: stage.getBoundingClientRect(),
      snapLeft: overlayRect.left,
      snapTop: overlayRect.top,
      snapW: overlayRect.w,
      snapH: overlayRect.h,
    };
    setActiveResizeHandle(handle);
  };

  // Move overlay drag
  useEffect(() => {
    if (!isMovingOverlay) return;

    const onMove = (clientX: number, clientY: number) => {
      const start = resizeDragStartRef.current;
      if (!start) return;
      const dxF = (clientX - start.startX) / start.stageRect.width;
      const dyF = (clientY - start.startY) / start.stageRect.height;
      const left = Math.max(0, Math.min(1 - start.snapW, start.snapLeft + dxF));
      const top = Math.max(0, Math.min(1 - start.snapH, start.snapTop + dyF));
      setOverlayRect({ left, top, w: start.snapW, h: start.snapH });
    };

    const onMouseMove = (e: MouseEvent) => onMove(e.clientX, e.clientY);
    const onTouchMove = (e: TouchEvent) => {
      e.preventDefault();
      const t = e.touches[0];
      if (t) onMove(t.clientX, t.clientY);
    };
    const onUp = () => {
      setIsMovingOverlay(false);
      resizeDragStartRef.current = null;
    };

    document.addEventListener("mousemove", onMouseMove);
    document.addEventListener("touchmove", onTouchMove, { passive: false });
    document.addEventListener("mouseup", onUp);
    document.addEventListener("touchend", onUp);
    return () => {
      document.removeEventListener("mousemove", onMouseMove);
      document.removeEventListener("touchmove", onTouchMove);
      document.removeEventListener("mouseup", onUp);
      document.removeEventListener("touchend", onUp);
    };
  }, [isMovingOverlay]);

  const startOverlayMove = (e: ReactMouseEvent<HTMLDivElement>) => {
    e.preventDefault();
    const stage = resizeStageRef.current;
    if (!stage) return;
    resizeDragStartRef.current = {
      startX: e.clientX,
      startY: e.clientY,
      stageRect: stage.getBoundingClientRect(),
      snapLeft: overlayRect.left,
      snapTop: overlayRect.top,
      snapW: overlayRect.w,
      snapH: overlayRect.h,
    };
    setIsMovingOverlay(true);
  };

  const startOverlayMoveTouch = (e: React.TouchEvent<HTMLDivElement>) => {
    e.preventDefault();
    const stage = resizeStageRef.current;
    if (!stage) return;
    const touch = e.touches[0];
    if (!touch) return;
    resizeDragStartRef.current = {
      startX: touch.clientX,
      startY: touch.clientY,
      stageRect: stage.getBoundingClientRect(),
      snapLeft: overlayRect.left,
      snapTop: overlayRect.top,
      snapW: overlayRect.w,
      snapH: overlayRect.h,
    };
    setIsMovingOverlay(true);
  };


  const xToTime = useCallback(
    (clientX: number): number => {
      const area = waveformAreaRef.current;
      if (!area || videoDuration <= 0) return 0;
      const rect = area.getBoundingClientRect();
      const ratio = Math.max(0, Math.min((clientX - rect.left) / rect.width, 1));
      return Number((ratio * videoDuration).toFixed(2));
    },
    [videoDuration],
  );

  useEffect(() => {
    if (!isDragging) return;

    const onMouseMove = (e: MouseEvent) => {
      const t = xToTime(e.clientX);
      if (isDragging === "start") {
        const newStart = Math.min(t, trimEnd - 0.1);
        setTrimStart(newStart);
        if (videoRef.current) videoRef.current.currentTime = newStart;
      } else {
        const newEnd = Math.max(t, trimStart + 0.1);
        setTrimEnd(newEnd);
        if (videoRef.current) videoRef.current.currentTime = newEnd;
      }
    };

    const onTouchMove = (e: TouchEvent) => {
      e.preventDefault();
      const touch = e.touches[0];
      if (!touch) return;
      const t = xToTime(touch.clientX);
      if (isDragging === "start") {
        const newStart = Math.min(t, trimEnd - 0.1);
        setTrimStart(newStart);
        if (videoRef.current) videoRef.current.currentTime = newStart;
      } else {
        const newEnd = Math.max(t, trimStart + 0.1);
        setTrimEnd(newEnd);
        if (videoRef.current) videoRef.current.currentTime = newEnd;
      }
    };

    const onMouseUp = () => setIsDragging(null);

    document.addEventListener("mousemove", onMouseMove);
    document.addEventListener("touchmove", onTouchMove, { passive: false });
    document.addEventListener("mouseup", onMouseUp);
    document.addEventListener("touchend", onMouseUp);
    return () => {
      document.removeEventListener("mousemove", onMouseMove);
      document.removeEventListener("touchmove", onTouchMove);
      document.removeEventListener("mouseup", onMouseUp);
      document.removeEventListener("touchend", onMouseUp);
    };
  }, [isDragging, xToTime, trimStart, trimEnd]);

  useEffect(() => {
    const video = videoRef.current;
    if (!video || !trimEnabled) return;

    const onTimeUpdate = () => {
      if (video.currentTime >= trimEnd) {
        video.pause();
        video.currentTime = trimStart;
      } else if (video.currentTime < trimStart) {
        video.currentTime = trimStart;
      }
    };

    video.addEventListener("timeupdate", onTimeUpdate);
    return () => video.removeEventListener("timeupdate", onTimeUpdate);
  }, [trimStart, trimEnd, trimEnabled]);

  const trimStartPercent = videoDuration > 0 ? (trimStart / videoDuration) * 100 : 0;
  const trimEndPercent = videoDuration > 0 ? (trimEnd / videoDuration) * 100 : 100;

  const pollJobStatus = async (jobId: string, isBatch: boolean) => {
    for (let attempt = 0; attempt < 300; attempt += 1) {
      await new Promise((resolve) => window.setTimeout(resolve, POLL_INTERVAL_MS));

      const statusPath = isBatch ? `/batch/jobs/${jobId}` : `/video/jobs/${jobId}`;
      const response = await authFetch(buildApiUrl(statusPath), {
        cache: "no-store",
      });

      const payload = (await response.json()) as VideoJobStatusResponse | { detail?: string };

      if (!response.ok) {
        throw new Error("detail" in payload ? payload.detail ?? "Video job status check failed." : "Video job status check failed.");
      }

      const statusPayload = payload as VideoJobStatusResponse;
      setJobStatus(statusPayload.status);

      if (isCompletedStatus(statusPayload.status)) {
        setResult((previous) =>
          previous
            ? {
              ...previous,
              status: JOB_STATUS.completed,
              download_url: isBatch ? `/batch/jobs/${jobId}/download` : `/video/jobs/${jobId}/download`,
              output_filename: statusPayload.output_path?.split("/").pop() ?? null,
            }
            : previous,
        );
        return;
      }

      if (isFailedStatus(statusPayload.status)) {
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
      setAction("Converting Video(s)");
      const query = new URLSearchParams({
        target_format: targetFormat,
        fps: String(fps),
        resize_enabled: String(resizeEnabled),
      });

      if (resizeEnabled) {
        query.set("width", width);
        query.set("height", height);
        query.set("crop_x", String(Math.round(overlayRect.left * sourceWidth)));
        query.set("crop_y", String(Math.round(overlayRect.top * sourceHeight)));
      }

      if (!isBatch && trimEnabled && videoDuration > 0) {
        query.set("trim_enabled", "true");
        query.set("trim_start", trimStart.toFixed(2));
        query.set("trim_end", trimEnd.toFixed(2));
      }

      const endpoint = isBatch ? "/batch/video/jobs" : "/video/jobs";
      const response = await xhrPost(
        buildApiUrl(`${endpoint}?${query.toString()}`),
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
      setAction("idle");
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
          <input className="file-input" type="file" accept={VIDEO_ACCEPT_ATTR} multiple onChange={handleFileChange} />
        </label>

        <div className="form-grid">
          <label className="field-group">
            <span>Target format</span>
            <select value={targetFormat} onChange={(event) => setTargetFormat(event.target.value)}>
              {VIDEO_FORMATS.map((format) => (
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
          <span>Enable crop</span>
        </label>

        {selectedFiles.length === 1 && previewUrl ? (
          <section className="trim-card">
            <div className="trim-header">
              <h3>Trim</h3>
              <label className="checkbox-group">
                <input type="checkbox" checked={trimEnabled} onChange={(event) => setTrimEnabled(event.target.checked)} />
                <span>Enable trim</span>
              </label>
            </div>

            <div ref={resizeStageRef} className="video-resize-stage">
              <video ref={videoRef} className="trim-preview" src={previewUrl} controls={!resizeEnabled} preload="metadata" onLoadedMetadata={handleMetadataLoaded} />
              {resizeEnabled ? (
                <div
                  className="video-resize-overlay"
                  style={{ left: `${overlayRect.left * 100}%`, top: `${overlayRect.top * 100}%`, width: `${overlayRect.w * 100}%`, height: `${overlayRect.h * 100}%`, cursor: isMovingOverlay ? "grabbing" : "grab", pointerEvents: "auto" }}
                  onMouseDown={startOverlayMove}
                  onTouchStart={startOverlayMoveTouch}
                >
                  <span className="resize-overlay-label">
                    {width} × {height}px
                    {(overlayRect.left > 0 || overlayRect.top > 0) && (
                      <> @ {Math.round(overlayRect.left * sourceWidth)},{Math.round(overlayRect.top * sourceHeight)}</>
                    )}
                  </span>
                  {(["n", "s", "e", "w", "ne", "nw", "se", "sw"] as ResizeHandle[]).map((handle) => (
                    <button
                      key={handle}
                      type="button"
                      className={`resize-handle resize-handle-${handle}`}
                      onMouseDown={startResizeDrag(handle)}
                      onTouchStart={(e) => {
                        e.preventDefault();
                        e.stopPropagation();
                        const stage = resizeStageRef.current;
                        if (!stage) return;
                        const touch = e.touches[0];
                        if (!touch) return;
                        resizeDragStartRef.current = {
                          startX: touch.clientX,
                          startY: touch.clientY,
                          stageRect: stage.getBoundingClientRect(),
                          snapLeft: overlayRect.left,
                          snapTop: overlayRect.top,
                          snapW: overlayRect.w,
                          snapH: overlayRect.h,
                        };
                        setActiveResizeHandle(handle);
                      }}
                      aria-label={`Resize ${handle}`}
                    />
                  ))}
                </div>
              ) : null}
            </div>

            <div
              ref={waveformAreaRef}
              className="waveform-area"
              style={{ userSelect: "none", height: "60px", marginTop: "12px", borderRadius: "8px" }}
            >
              <div style={{ width: "100%", height: "100%", background: "repeating-linear-gradient(90deg, rgba(255,255,255,0.05) 0px, rgba(255,255,255,0.05) 2px, transparent 2px, transparent 10px)", opacity: 0.5 }} />

              <div className="waveform-mask" style={{ left: 0, width: `${trimStartPercent}%` }} />
              <div className="waveform-mask" style={{ right: 0, width: `${100 - trimEndPercent}%` }} />

              <div
                className="waveform-handle"
                style={{ left: `${trimStartPercent}%`, opacity: trimEnabled ? 1 : 0.4 }}
                onMouseDown={(e) => {
                  if (!trimEnabled) return;
                  e.preventDefault();
                  setIsDragging("start");
                }}
                onTouchStart={(e) => {
                  if (!trimEnabled) return;
                  e.preventDefault();
                  setIsDragging("start");
                }}
              >
                <div className="waveform-handle-grip" />
              </div>

              <div
                className="waveform-handle"
                style={{ left: `${trimEndPercent}%`, opacity: trimEnabled ? 1 : 0.4 }}
                onMouseDown={(e) => {
                  if (!trimEnabled) return;
                  e.preventDefault();
                  setIsDragging("end");
                }}
                onTouchStart={(e) => {
                  if (!trimEnabled) return;
                  e.preventDefault();
                  setIsDragging("end");
                }}
              >
                <div className="waveform-handle-grip" />
              </div>
            </div>

            <div className="waveform-timestamps" style={{ marginBottom: "12px" }}>
              <span>{formatTime(trimStart)}</span>
              <span className="waveform-time-center">{formatTime(videoDuration)}</span>
              <span>{formatTime(trimEnd)}</span>
            </div>

            <div className="trim-meta-row">
              <span>Duration: {videoDuration > 0 ? `${videoDuration.toFixed(2)}s` : "loading..."}</span>
              <span>
                Range: {trimStart.toFixed(2)}s → {trimEnd.toFixed(2)}s
              </span>
            </div>

            <div className="field-group">
              <span>Trim range</span>
              <div className="trim-manual-row">
                <label className="field-group trim-manual-field">
                  <span>Start (MM:SS.s)</span>
                  <input
                    key={trimStart}
                    type="text"
                    defaultValue={formatTime(trimStart)}
                    disabled={!trimEnabled || videoDuration <= 0}
                    placeholder={AUDIO_TIME_FORMAT_PLACEHOLDER}
                    onBlur={(e) => {
                      const s = mmssToSeconds(e.target.value);
                      if (s !== null) {
                        const newStart = Number(Math.min(Math.max(s, 0), trimEnd - 0.1).toFixed(2));
                        setTrimStart(newStart);
                        if (videoRef.current) videoRef.current.currentTime = newStart;
                      }
                    }}
                  />
                </label>

                <label className="field-group trim-manual-field">
                  <span>End (MM:SS.s)</span>
                  <input
                    key={trimEnd}
                    type="text"
                    defaultValue={formatTime(trimEnd)}
                    disabled={!trimEnabled || videoDuration <= 0}
                    placeholder={AUDIO_TIME_FORMAT_PLACEHOLDER}
                    onBlur={(e) => {
                      const s = mmssToSeconds(e.target.value);
                      if (s !== null) {
                        const newEnd = Number(Math.max(Math.min(s, videoDuration), trimStart + 0.1).toFixed(2));
                        setTrimEnd(newEnd);
                        if (videoRef.current) videoRef.current.currentTime = newEnd;
                      }
                    }}
                  />
                </label>
              </div>
            </div>
          </section>
        ) : null}

        {selectedFiles.length > 1 ? <p className="selection-hint">Trim is available for single file mode.</p> : null}

        <button className="primary-button" type="submit" disabled={isSubmitting}>
          {uploadProgress.length > 0 ? "Uploading..." : isSubmitting ? "Converting..." : "Convert video"}
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
            <strong>Crop:</strong> {result.resize_enabled ? `${result.width}x${result.height}` : "Disabled"}
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
            <a className="primary-button inline-button" href={buildApiUrl(result.download_url)} target="_blank" rel="noreferrer">
              Download {isBatchResult ? "zip bundle" : "converted video"}
            </a>
          ) : null}
        </div>
      ) : null}
    </section>
  );
}
