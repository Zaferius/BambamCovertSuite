"use client";

import { ChangeEvent, FormEvent, useMemo, useState } from "react";
import { authFetch } from "../lib/auth-fetch";

type BatchRenameResponse = {
  job_id: string;
  status: string;
  item_count: number;
  output_filename?: string | null;
  download_url?: string | null;
};

type JobStatusResponse = {
  id: string;
  status: string;
  output_path?: string | null;
  output_filename?: string | null;
  error_message?: string | null;
};

export function BatchRenameConverter() {
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [pattern, setPattern] = useState<string>("{name}_{index}");
  const [startIndex, setStartIndex] = useState<number>(1);
  const [keepExtension, setKeepExtension] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [result, setResult] = useState<BatchRenameResponse | null>(null);
  const [jobStatus, setJobStatus] = useState<string | null>(null);

  const apiBaseUrl = useMemo(
    () => process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000",
    [],
  );

  const handleFileChange = (event: ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(event.target.files ?? []);
    setSelectedFiles(files);
    setErrorMessage(null);
    setResult(null);
    setJobStatus(null);
  };

  const pollJobStatus = async (jobId: string) => {
    for (let attempt = 0; attempt < 120; attempt += 1) {
      await new Promise((resolve) => window.setTimeout(resolve, 1000));

      const response = await authFetch(`${apiBaseUrl}/batch/jobs/${jobId}`, { cache: "no-store" });
      const payload = (await response.json()) as JobStatusResponse | { detail?: string };

      if (!response.ok) {
        throw new Error("detail" in payload ? payload.detail ?? "Rename job status check failed." : "Rename job status check failed.");
      }

      const statusPayload = payload as JobStatusResponse;
      setJobStatus(statusPayload.status);

      if (statusPayload.status === "completed") {
        setResult((previous) =>
          previous
            ? {
                ...previous,
                status: "completed",
                output_filename: statusPayload.output_filename ?? statusPayload.output_path?.split("/").pop() ?? null,
                download_url: `/batch/jobs/${jobId}/download`,
              }
            : previous,
        );
        return;
      }

      if (statusPayload.status === "failed") {
        throw new Error(statusPayload.error_message ?? "Batch rename failed.");
      }
    }

    throw new Error("Batch rename is taking longer than expected.");
  };

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    if (selectedFiles.length === 0) {
      setErrorMessage("Please choose at least one file first.");
      return;
    }

    setIsSubmitting(true);
    setErrorMessage(null);
    setResult(null);
    setJobStatus(null);

    const formData = new FormData();
    for (const file of selectedFiles) {
      formData.append("files", file);
    }

    try {
      const query = new URLSearchParams({
        pattern,
        start_index: String(startIndex),
        keep_extension: String(keepExtension),
      });

      const response = await authFetch(`${apiBaseUrl}/batch/rename/jobs?${query.toString()}`, {
        method: "POST",
        body: formData,
      });

      const payload = (await response.json()) as BatchRenameResponse | { detail?: string };

      if (!response.ok) {
        throw new Error("detail" in payload ? payload.detail ?? "Batch rename failed." : "Batch rename failed.");
      }

      const renameResult = payload as BatchRenameResponse;
      setResult(renameResult);
      setJobStatus(renameResult.status);
      await pollJobStatus(renameResult.job_id);
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : "Batch rename failed.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <section className="tool-card feature-card">
      <div className="section-heading compact-heading">
        <h2>Batch rename</h2>
        <p>Upload multiple files, define a naming pattern, then download the renamed files as a zip bundle.</p>
      </div>

      <form className="converter-form" onSubmit={handleSubmit}>
        <label className="field-group">
          <span>Files</span>
          <input className="file-input" type="file" multiple onChange={handleFileChange} />
        </label>

        <div className="form-grid">
          <label className="field-group">
            <span>Pattern</span>
            <input
              type="text"
              value={pattern}
              onChange={(event) => setPattern(event.target.value)}
              placeholder="{name}_{index}"
            />
          </label>

          <label className="field-group">
            <span>Start index</span>
            <input
              type="number"
              min="0"
              value={startIndex}
              onChange={(event) => setStartIndex(Number(event.target.value))}
            />
          </label>
        </div>

        <label className="checkbox-group">
          <input
            type="checkbox"
            checked={keepExtension}
            onChange={(event) => setKeepExtension(event.target.checked)}
          />
          <span>Keep original extension</span>
        </label>

        <button className="primary-button" type="submit" disabled={isSubmitting}>
          {isSubmitting ? "Renaming..." : "Start batch rename"}
        </button>
      </form>

      {selectedFiles.length > 0 ? (
        <p className="selection-hint">
          Selected files: <strong>{selectedFiles.length}</strong>
        </p>
      ) : null}

      {errorMessage ? <p className="error-text">{errorMessage}</p> : null}

      {result ? (
        <div className="result-card">
          <h3>Batch rename state</h3>
          <p>
            <strong>Job:</strong> {result.job_id}
          </p>
          <p>
            <strong>Item count:</strong> {result.item_count}
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
              Download zip bundle
            </a>
          ) : null}
        </div>
      ) : null}
    </section>
  );
}

