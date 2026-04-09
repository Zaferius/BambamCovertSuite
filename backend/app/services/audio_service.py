import os
import subprocess
from pathlib import Path


AUDIO_FORMATS = {"MP3", "WAV", "FLAC", "OGG", "M4A", "AAC", "WMA", "OPUS", "AIFF"}
AUDIO_BITRATES = {"128k", "192k", "256k", "320k"}


def get_ffmpeg_cmd() -> list[str]:
    exe = "ffmpeg.exe" if os.name == "nt" else "ffmpeg"
    here = os.path.dirname(os.path.abspath(__file__))
    local = os.path.join(here, exe)
    if os.path.exists(local):
        return [local]
    return ["ffmpeg"]


class AudioConversionService:
    def convert(
        self,
        *,
        source_path: Path,
        output_path: Path,
        target_format: str,
        bitrate: str,
        trim_enabled: bool = False,
        trim_start: float | None = None,
        trim_end: float | None = None,
    ) -> Path:
        normalized_format = target_format.upper()

        if normalized_format not in AUDIO_FORMATS:
            raise ValueError(f"Unsupported target format: {target_format}")

        if bitrate not in AUDIO_BITRATES:
            raise ValueError(f"Unsupported bitrate: {bitrate}")

        if trim_enabled:
            if trim_start is None or trim_end is None:
                raise ValueError("trim_start and trim_end are required when trim is enabled")
            if trim_end <= trim_start:
                raise ValueError("trim_end must be greater than trim_start")

        cmd = get_ffmpeg_cmd() + ["-y"]

        if trim_enabled and trim_start is not None:
            cmd += ["-ss", f"{trim_start}"]

        cmd += ["-i", str(source_path)]

        if trim_enabled and trim_end is not None and trim_start is not None:
            cmd += ["-to", f"{trim_end - trim_start}"]

        ext = normalized_format.lower()
        cmd += ["-b:a", bitrate]

        if ext == "wma":
            cmd += ["-c:a", "wmav2"]
        elif ext == "opus":
            cmd += ["-c:a", "libopus"]
        elif ext == "aiff":
            cmd += ["-c:a", "pcm_s16be"]

        cmd += [str(output_path)]

        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if result.returncode != 0:
            raise RuntimeError(result.stderr or "FFmpeg audio conversion error")

        return output_path
