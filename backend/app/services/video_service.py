import os
import subprocess
from pathlib import Path


VIDEO_FORMATS = {"MP4", "MOV", "MKV", "AVI", "WEBM", "GIF"}


def ensure_even_dimension(value: int) -> int:
    if value < 1:
        raise ValueError("Resize dimensions must be greater than 0")
    return value if value % 2 == 0 else value + 1


def normalize_resize_dimensions(width: int | None, height: int | None) -> tuple[int, int]:
    if width is None or height is None:
        raise ValueError("Width and height are required when crop is enabled")
    return ensure_even_dimension(width), ensure_even_dimension(height)


def normalize_crop_offset(value: int) -> int:
    return value if value % 2 == 0 else value - 1


def get_ffmpeg_cmd() -> list[str]:
    exe = "ffmpeg.exe" if os.name == "nt" else "ffmpeg"
    here = os.path.dirname(os.path.abspath(__file__))
    local = os.path.join(here, exe)
    if os.path.exists(local):
        return [local]
    return ["ffmpeg"]


class VideoConversionService:
    def build_command(
        self,
        *,
        source_path: Path,
        output_path: Path,
        target_format: str,
        fps: int = 0,
        resize_enabled: bool = False,
        width: int | None = None,
        height: int | None = None,
        crop_x: int | None = None,
        crop_y: int | None = None,
        trim_enabled: bool = False,
        trim_start: float | None = None,
        trim_end: float | None = None,
    ) -> list[str]:
        normalized_format = target_format.upper()

        if normalized_format not in VIDEO_FORMATS:
            raise ValueError(f"Unsupported target format: {target_format}")

        cmd = get_ffmpeg_cmd() + ["-y"]

        if trim_enabled:
            if trim_start is None or trim_end is None:
                raise ValueError("trim_start and trim_end are required when trim is enabled")
            if trim_end <= trim_start:
                raise ValueError("trim_end must be greater than trim_start")
            cmd += ["-ss", f"{trim_start}", "-to", f"{trim_end}"]

        cmd += ["-i", str(source_path)]

        if resize_enabled:
            normalized_width, normalized_height = normalize_resize_dimensions(width, height)
            nx = normalize_crop_offset(crop_x if crop_x is not None else 0)
            ny = normalize_crop_offset(crop_y if crop_y is not None else 0)
            cmd += [
                "-vf",
                f"crop={normalized_width}:{normalized_height}:{nx}:{ny}",
            ]

        if fps > 0:
            cmd += ["-r", str(fps)]

        ext = normalized_format.lower()
        vcodec = "libx264" if ext in {"mp4", "mov", "mkv", "avi"} else ("libvpx-vp9" if ext == "webm" else "gif")
        acodec = "aac" if ext in {"mp4", "mov", "mkv", "avi"} else ("libopus" if ext == "webm" else None)

        if ext != "gif":
            cmd += ["-c:v", vcodec]
            if acodec is not None:
                cmd += ["-c:a", acodec]

        cmd += [str(output_path)]
        return cmd

    def convert(
        self,
        *,
        source_path: Path,
        output_path: Path,
        target_format: str,
        fps: int = 0,
        resize_enabled: bool = False,
        width: int | None = None,
        height: int | None = None,
        crop_x: int | None = None,
        crop_y: int | None = None,
        trim_enabled: bool = False,
        trim_start: float | None = None,
        trim_end: float | None = None,
    ) -> Path:
        cmd = self.build_command(
            source_path=source_path,
            output_path=output_path,
            target_format=target_format,
            fps=fps,
            resize_enabled=resize_enabled,
            width=width,
            height=height,
            crop_x=crop_x,
            crop_y=crop_y,
            trim_enabled=trim_enabled,
            trim_start=trim_start,
            trim_end=trim_end,
        )

        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if result.returncode != 0:
            raise RuntimeError(result.stderr or "FFmpeg video conversion error")

        return output_path
