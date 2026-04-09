import { DEFAULT_API_BASE_URL, JOB_STATUS } from "./app-constants";

export function buildApiUrl(path: string): string {
  return `${DEFAULT_API_BASE_URL}${path}`;
}

export function isCompletedStatus(status: string | null | undefined): boolean {
  return status === JOB_STATUS.completed;
}

export function isFailedStatus(status: string | null | undefined): boolean {
  return status === JOB_STATUS.failed;
}

