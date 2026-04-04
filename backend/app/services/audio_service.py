import os
import subprocess
from pathlib import Path


AUDIO_FORMATS = {"MP3", "WAV", "FLAC", "OGG", "M4A", "AAC"}
AUDIO_BITRATES = {"128k", "192k", "256k", "320k"}


def get_ffmpeg_cmd() -> list[str]:
    exe = "ffmpeg.exe" if os.name == "nt" else "ffmpeg"
    here = os.path.dirname(os.path.abspath(__file__))
    local = os.path.join(here, exe)
    if os.path.exists(local):
        return [local]
    return ["ffmpeg"]


class AudioConversionService:
    def convert(self, *, source_path: Path, output_path: Path, target_format: str, bitrate: str) -> Path:
        normalized_format = target_format.upper()

        if normalized_format not in AUDIO_FORMATS:
            raise ValueError(f"Unsupported target format: {target_format}")

        if bitrate not in AUDIO_BITRATES:
            raise ValueError(f"Unsupported bitrate: {bitrate}")

        cmd = get_ffmpeg_cmd() + [
            "-y",
            "-i",
            str(source_path),
            "-b:a",
            bitrate,
            str(output_path),
        ]

        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if result.returncode != 0:
            raise RuntimeError(result.stderr or "FFmpeg audio conversion error")

        return output_path
