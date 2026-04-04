"use client";

/// <reference types="react" />
/// <reference types="react-dom" />
/// <reference types="node" />

import type { ChangeEvent, FormEvent } from "react";
import { useMemo, useState } from "react";


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
    for (let attempt = 0; attempt < 120; attempt += 1) {
      await new Promise((resolve) => window.setTimeout(resolve, 1000));

      const statusPath = isBatch ? `/batch/jobs/${jobId}` : `/audio/jobs/${jobId}`;
      const response = await fetch(`${apiBaseUrl}${statusPath}`, {
        cache: "no-store",
      });

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

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    const isBatch = selectedFiles.length > 1;

    if (selectedFiles.length === 0) {
      setErrorMessage("Please choose an audio file first.");
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
        bitrate,
      });

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
            <select value={targetFormat} onChange={(event: ChangeEvent<HTMLSelectElement>) => setTargetFormat(event.target.value)}>
              {audioFormats.map((format) => (
                <option key={format} value={format}>
                  {format}
                </option>
              ))}
            </select>
          </label>

          <label className="field-group">
            <span>Bitrate</span>
            <select value={bitrate} onChange={(event: ChangeEvent<HTMLSelectElement>) => setBitrate(event.target.value)}>
              {audioBitrates.map((value) => (
                <option key={value} value={value}>
                  {value}
                </option>
              ))}
            </select>
          </label>
        </div>

        <button className="primary-button" type="submit" disabled={isSubmitting}>
          {isSubmitting ? "Converting..." : "Convert audio"}
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
          <h3>Audio conversion state</h3>
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
            <strong>Bitrate:</strong> {result.bitrate}
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
              Download {isBatchResult ? "zip bundle" : "converted audio"}
            </a>
          ) : null}
        </div>
      ) : null}
    </section>
  );
}
