export const DEFAULT_API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export const AUTH_TOKEN_STORAGE_KEY = "bambam_token";
export const AUTH_USER_STORAGE_KEY = "bambam_user";

export const JOB_STATUS = {
  queued: "queued",
  processing: "processing",
  completed: "completed",
  failed: "failed",
} as const;

export const POLL_INTERVAL_MS = 1000;
export const USER_ACTIVITY_PING_INTERVAL_MS = 10000;

export const IMAGE_FORMATS = ["PNG", "JPG", "JPEG", "WEBP", "TIFF", "BMP", "GIF", "ICO"] as const;
export const IMAGE_QUALITY_FORMATS = ["JPG", "JPEG", "WEBP"] as const;
export const IMAGE_ACCEPT_ATTR = ".png,.jpg,.jpeg,.webp,.tiff,.bmp,.gif,.ico";

export const AUDIO_FORMATS = ["MP3", "WAV", "FLAC", "OGG", "M4A", "AAC", "WMA", "OPUS", "AIFF"] as const;
export const AUDIO_BITRATES = ["128k", "192k", "256k", "320k"] as const;
export const AUDIO_ACCEPT_ATTR = ".mp3,.wav,.flac,.ogg,.m4a,.aac,.wma,.opus,.aiff,.aif";
export const AUDIO_TIME_FORMAT_PLACEHOLDER = "00:00.0";

export const VIDEO_FORMATS = ["MP4", "AVI", "MKV", "MOV", "WMV", "FLV", "WEBM", "GIF"] as const;
export const VIDEO_ACCEPT_ATTR = ".mp4,.mov,.mkv,.avi,.webm,.gif,.wmv,.flv";

export const DOCUMENT_FORMATS = ["PDF", "DOCX", "ODT", "TXT"] as const;
export const DOCUMENT_ACCEPT_ATTR = ".pdf,.docx,.doc,.odt,.txt,.rtf,.xls,.xlsx,.ppt,.pptx";

export const ONLINE_USERS_POLL_INTERVAL_MS = 3000;
export const WORKERS_POLL_INTERVAL_MS = 5000;
export const MIN_WORKER_COUNT = 1;
export const STORAGE_SOURCES = {
  outputs: "outputs",
  uploads: "uploads",
} as const;

