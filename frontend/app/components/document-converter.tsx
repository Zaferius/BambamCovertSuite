"use client";

import { ChangeEvent, FormEvent, useMemo, useState } from "react";
import { ConversionLoader } from "./conversion-loader";


const documentFormats = ["PDF", "DOCX", "ODT", "TXT"] as const;

type DocumentConversionResponse = {
  job_id: string;
  status: string;
  target_format: string;
  original_filename: string;
  output_filename?: string | null;
  download_url?: string | null;
};

type DocumentJobStatusResponse = {
  id: string;
  status: string;
  output_path?: string | null;
  error_message?: string | null;
};


export function DocumentConverter() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [targetFormat, setTargetFormat] = useState<string>("PDF");
  const [isBatchResult, setIsBatchResult] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [result, setResult] = useState<DocumentConversionResponse | null>(null);
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
    for (let attempt = 0; attempt < 180; attempt += 1) {
      await new Promise((resolve) => window.setTimeout(resolve, 1000));

      const statusPath = isBatch ? `/batch/jobs/${jobId}` : `/document/jobs/${jobId}`;
      const response = await fetch(`${apiBaseUrl}${statusPath}`, { cache: "no-store" });
      const payload = (await response.json()) as DocumentJobStatusResponse | { detail?: string };

      if (!response.ok) {
        throw new Error("detail" in payload ? payload.detail ?? "Document job status check failed." : "Document job status check failed.");
      }

      const statusPayload = payload as DocumentJobStatusResponse;
      setJobStatus(statusPayload.status);

      if (statusPayload.status === "completed") {
        setResult((previous) =>
          previous
            ? {
                ...previous,
                status: "completed",
                download_url: isBatch ? `/batch/jobs/${jobId}/download` : `/document/jobs/${jobId}/download`,
                output_filename: statusPayload.output_path?.split("/").pop() ?? null,
              }
            : previous,
        );
        return;
      }

      if (statusPayload.status === "failed") {
        throw new Error(statusPayload.error_message ?? "Document conversion failed.");
      }
    }

    throw new Error("Document conversion is taking longer than expected.");
  };

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    const isBatch = selectedFiles.length > 1;

    if (selectedFiles.length === 0) {
      setErrorMessage("Please choose a document file first.");
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
      const query = new URLSearchParams({ target_format: targetFormat });

      const endpoint = isBatch ? "/batch/document/jobs" : "/document/jobs";
      const response = await fetch(`${apiBaseUrl}${endpoint}?${query.toString()}`, {
        method: "POST",
        body: formData,
      });

      const payload = (await response.json()) as DocumentConversionResponse | { detail?: string };

      if (!response.ok) {
        throw new Error("detail" in payload ? payload.detail ?? "Document conversion failed." : "Document conversion failed.");
      }

      const conversionResult = payload as DocumentConversionResponse;
      setResult(conversionResult);
      setJobStatus(conversionResult.status);
      await pollJobStatus(conversionResult.job_id, isBatch);
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : "Document conversion failed.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <section className="tool-card feature-card">
      <div className="section-heading compact-heading">
        <h2>Document converter</h2>
        <p>Upload a supported office document and convert it with LibreOffice headless in Docker.</p>
      </div>

      <form className="converter-form" onSubmit={handleSubmit}>
        <label className="field-group">
          <span>Document file</span>
          <input className="file-input" type="file" multiple accept=".pdf,.docx,.doc,.odt,.txt,.rtf" onChange={handleFileChange} />
        </label>

        <label className="field-group">
          <span>Target format</span>
          <select value={targetFormat} onChange={(event) => setTargetFormat(event.target.value)}>
            {documentFormats.map((format) => (
              <option key={format} value={format}>
                {format}
              </option>
            ))}
          </select>
        </label>

        <button className="primary-button" type="submit" disabled={isSubmitting}>
          {isSubmitting ? "Converting..." : "Convert document"}
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
          <h3>Document conversion state</h3>
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
              Download {isBatchResult ? "zip bundle" : "converted document"}
            </a>
          ) : null}
        </div>
      ) : null}
    </section>
  );
}
