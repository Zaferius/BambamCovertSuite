"use client";

import { ChangeEvent, FormEvent, useMemo, useState } from "react";
import { ConversionLoader } from "./conversion-loader";
import { type FileUploadItem, UploadProgressPanel } from "./upload-progress";
import { distributeProgress, xhrPost } from "../lib/xhr-post";
import { authFetch } from "../lib/auth-fetch";
import { buildApiUrl, isCompletedStatus, isFailedStatus } from "../lib/api";
import { DOCUMENT_ACCEPT_ATTR, DOCUMENT_FORMATS, JOB_STATUS, POLL_INTERVAL_MS } from "../lib/app-constants";


const formatsBySource: Record<string, string[]> = {
  pdf: ["ODT", "TXT"],
  docx: [...DOCUMENT_FORMATS],
  doc: [...DOCUMENT_FORMATS],
  odt: ["PDF", "DOCX", "TXT"],
  rtf: [...DOCUMENT_FORMATS],
  txt: ["PDF", "DOCX", "ODT"],
  xls: ["PDF"],
  xlsx: ["PDF"],
  ppt: ["PDF"],
  pptx: ["PDF"],
};

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
  const [uploadProgress, setUploadProgress] = useState<FileUploadItem[]>([]);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [result, setResult] = useState<DocumentConversionResponse | null>(null);
  const [jobStatus, setJobStatus] = useState<string | null>(null);

  const availableFormats = useMemo(() => {
    const ext = (selectedFile?.name.split(".").pop() ?? "").toLowerCase();
    return formatsBySource[ext] ?? [...DOCUMENT_FORMATS];
  }, [selectedFile]);

  const handleFileChange = (event: ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(event.target.files ?? []);
    const file = files[0] ?? null;
    setSelectedFile(file);
    setSelectedFiles(files);
    setErrorMessage(null);
    setResult(null);
    setJobStatus(null);
    const ext = (file?.name.split(".").pop() ?? "").toLowerCase();
    const allowed = formatsBySource[ext] ?? [...DOCUMENT_FORMATS];
    if (!allowed.includes(targetFormat)) {
      setTargetFormat(allowed[0] ?? "PDF");
    }
  };

  const pollJobStatus = async (jobId: string, isBatch: boolean) => {
    for (let attempt = 0; attempt < 180; attempt += 1) {
      await new Promise((resolve) => window.setTimeout(resolve, POLL_INTERVAL_MS));

      const statusPath = isBatch ? `/batch/jobs/${jobId}` : `/document/jobs/${jobId}`;
      const response = await authFetch(buildApiUrl(statusPath), { cache: "no-store" });
      const payload = (await response.json()) as DocumentJobStatusResponse | { detail?: string };

      if (!response.ok) {
        throw new Error("detail" in payload ? payload.detail ?? "Document job status check failed." : "Document job status check failed.");
      }

      const statusPayload = payload as DocumentJobStatusResponse;
      setJobStatus(statusPayload.status);

      if (isCompletedStatus(statusPayload.status)) {
        setResult((previous) =>
          previous
            ? {
              ...previous,
              status: JOB_STATUS.completed,
              download_url: isBatch ? `/batch/jobs/${jobId}/download` : `/document/jobs/${jobId}/download`,
              output_filename: statusPayload.output_path?.split("/").pop() ?? null,
            }
            : previous,
        );
        return;
      }

      if (isFailedStatus(statusPayload.status)) {
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
      const query = new URLSearchParams({ target_format: targetFormat });

      const endpoint = isBatch ? "/batch/document/jobs" : "/document/jobs";
      const response = await xhrPost(
        buildApiUrl(`${endpoint}?${query.toString()}`),
        formData,
        (pct) => setUploadProgress(distributeProgress(selectedFiles, pct)),
      );
      setUploadProgress([]);

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
          <input className="file-input" type="file" multiple accept={DOCUMENT_ACCEPT_ATTR} onChange={handleFileChange} />
        </label>

        <label className="field-group">
          <span>Target format</span>
          <select value={targetFormat} onChange={(event) => setTargetFormat(event.target.value)}>
            {availableFormats.map((format) => (
              <option key={format} value={format}>
                {format}
              </option>
            ))}
          </select>
        </label>

        <button className="primary-button" type="submit" disabled={isSubmitting}>
          {uploadProgress.length > 0 ? "Uploading..." : isSubmitting ? "Converting..." : "Convert document"}
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
            <a className="primary-button inline-button" href={buildApiUrl(result.download_url)} target="_blank" rel="noreferrer">
              Download {isBatchResult ? "zip bundle" : "converted document"}
            </a>
          ) : null}
        </div>
      ) : null}
    </section>
  );
}
