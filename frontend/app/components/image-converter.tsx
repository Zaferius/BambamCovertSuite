"use client";

import { ChangeEvent, FormEvent, useMemo, useState } from "react";
import { ConversionLoader } from "./conversion-loader";
import { type FileUploadItem, UploadProgressPanel } from "./upload-progress";
import { distributeProgress, xhrPost } from "../lib/xhr-post";


const imageFormats = ["PNG", "JPG", "JPEG", "WEBP", "TIFF", "BMP", "GIF"] as const;

type ConversionResponse = {
  job_id: string;
  status: string;
  target_format: string;
  quality: number;
  original_filename: string;
  output_filename?: string | null;
  download_url?: string | null;
};

type JobStatusResponse = {
  id: string;
  status: string;
  output_path?: string | null;
  error_message?: string | null;
};


export function ImageConverter() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [targetFormat, setTargetFormat] = useState<string>("PNG");
  const qualityFormats = new Set(["JPG", "JPEG", "WEBP"]);
  const qualitySupported = qualityFormats.has(targetFormat);
  const [quality, setQuality] = useState<number>(90);
  const [isBatchResult, setIsBatchResult] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [uploadProgress, setUploadProgress] = useState<FileUploadItem[]>([]);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [result, setResult] = useState<ConversionResponse | null>(null);
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
    for (let attempt = 0; attempt < 60; attempt += 1) {
      await new Promise((resolve) => window.setTimeout(resolve, 1000));

      const statusPath = isBatch ? `/batch/jobs/${jobId}` : `/image/jobs/${jobId}`;
      const response = await fetch(`${apiBaseUrl}${statusPath}`, {
        cache: "no-store",
      });

      const payload = (await response.json()) as JobStatusResponse | { detail?: string };

      if (!response.ok) {
        throw new Error("detail" in payload ? payload.detail ?? "Job status check failed." : "Job status check failed.");
      }

      const statusPayload = payload as JobStatusResponse;
      setJobStatus(statusPayload.status);

      if (statusPayload.status === "completed") {
        setResult((previous) =>
          previous
            ? {
                ...previous,
                status: "completed",
                download_url: isBatch ? `/batch/jobs/${jobId}/download` : `/image/jobs/${jobId}/download`,
                output_filename: statusPayload.output_path?.split("/").pop() ?? null,
              }
            : previous,
        );
        return;
      }

      if (statusPayload.status === "failed") {
        throw new Error(statusPayload.error_message ?? "Image conversion failed.");
      }
    }

    throw new Error("Image conversion is taking longer than expected.");
  };

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    const isBatch = selectedFiles.length > 1;

    if (selectedFiles.length === 0) {
      setErrorMessage("Please choose an image file first.");
      return;
    }

    setIsSubmitting(true);
    setErrorMessage(null);
    setResult(null);
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
        quality: String(quality),
      });

      const endpoint = isBatch ? "/batch/image/jobs" : "/image/jobs";
      const response = await xhrPost(
        `${apiBaseUrl}${endpoint}?${query.toString()}`,
        formData,
        (pct) => setUploadProgress(distributeProgress(selectedFiles, pct)),
      );
      setUploadProgress([]);

      const payload = (await response.json()) as ConversionResponse | { detail?: string };

      if (!response.ok) {
        throw new Error("detail" in payload ? payload.detail ?? "Image conversion failed." : "Image conversion failed.");
      }

      const conversionResult = payload as ConversionResponse;
      setResult(conversionResult);
      setJobStatus(conversionResult.status);
      await pollJobStatus(conversionResult.job_id, isBatch);
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : "Image conversion failed.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <section className="tool-card feature-card">
      <div className="section-heading compact-heading">
        <h2>Image converter</h2>
        <p>Upload a single image, choose an output format, and download the converted result.</p>
      </div>

      <form className="converter-form" onSubmit={handleSubmit}>
        <label className="field-group">
          <span>Image file</span>
          <input className="file-input" type="file" accept=".png,.jpg,.jpeg,.webp,.tiff,.bmp,.gif" multiple onChange={handleFileChange} />
        </label>

        <div className="form-grid">
          <label className="field-group">
            <span>Target format</span>
            <select value={targetFormat} onChange={(event) => setTargetFormat(event.target.value)}>
              {imageFormats.map((format) => (
                <option key={format} value={format}>
                  {format}
                </option>
              ))}
            </select>
          </label>

          {qualitySupported ? (
            <label className="field-group">
              <span>Quality: {quality}</span>
              <input
                type="range"
                min="1"
                max="100"
                value={quality}
                onChange={(event) => setQuality(Number(event.target.value))}
              />
            </label>
          ) : null}
        </div>

        <button className="primary-button" type="submit" disabled={isSubmitting}>
          {isSubmitting ? "Converting..." : "Convert image"}
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
          <h3>Conversion complete</h3>
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
            <strong>Status:</strong> {result.status}
          </p>
          {jobStatus ? (
            <p>
              <strong>Live status:</strong> {jobStatus}
            </p>
          ) : null}
          {result.download_url ? (
            <a className="primary-button inline-button" href={`${apiBaseUrl}${result.download_url}`} target="_blank" rel="noreferrer">
              Download {isBatchResult ? "zip bundle" : "converted file"}
            </a>
          ) : null}
        </div>
      ) : null}
    </section>
  );
}
