from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from yt_dlp import YoutubeDL

from app.core.constants import YOUTUBE_AUDIO_FORMATS, YOUTUBE_AUDIO_QUALITY_ORDER, YOUTUBE_DOWNLOAD_MODES, YOUTUBE_VIDEO_QUALITY_ORDER
from app.schemas.youtube import YouTubeAnalysisItem, YouTubeQualityOption


class YouTubeService:
    def normalize_urls(self, raw_urls: list[str]) -> list[str]:
        cleaned: list[str] = []
        seen: set[str] = set()
        for raw in raw_urls:
            value = raw.strip()
            if not value:
                continue
            normalized = self.normalize_url(value)
            if normalized not in seen:
                seen.add(normalized)
                cleaned.append(normalized)
        return cleaned

    def normalize_url(self, url: str) -> str:
        parsed = urlparse(url.strip())
        host = parsed.netloc.lower()
        if "youtu.be" in host:
            return url.strip()
        if "youtube.com" in host:
            query = parse_qs(parsed.query)
            video_id = query.get("v", [None])[0]
            if video_id:
                return f"https://www.youtube.com/watch?v={video_id}"
        return url.strip()

    def validate_mode(self, mode: str) -> str:
        normalized = mode.lower().strip()
        if normalized not in YOUTUBE_DOWNLOAD_MODES:
            raise ValueError("Unsupported download mode")
        return normalized

    def validate_audio_format(self, audio_format: str) -> str:
        normalized = audio_format.lower().strip()
        if normalized not in YOUTUBE_AUDIO_FORMATS:
            raise ValueError("Unsupported audio format")
        return normalized

    def analyze_urls(self, raw_urls: list[str], mode: str) -> list[YouTubeAnalysisItem]:
        normalized_mode = self.validate_mode(mode)
        items: list[YouTubeAnalysisItem] = []
        for url in self.normalize_urls(raw_urls):
            try:
                info = self._extract_info(url)
                items.append(
                    YouTubeAnalysisItem(
                        url=url,
                        normalized_url=info.get("webpage_url") or url,
                        title=info.get("title"),
                        duration_seconds=info.get("duration"),
                        thumbnail_url=info.get("thumbnail"),
                        platform=info.get("extractor_key") or info.get("extractor"),
                        available_qualities=self._build_quality_options(info, normalized_mode),
                        available_audio_formats=list(YOUTUBE_AUDIO_FORMATS),
                        status="ready",
                    )
                )
            except Exception as exc:
                items.append(
                    YouTubeAnalysisItem(
                        url=url,
                        status="failed",
                        error_message=str(exc),
                        available_qualities=[],
                        available_audio_formats=[],
                    )
                )
        return items

    def pick_quality(self, available: list[str], selected: str, mode: str) -> str:
        if selected in available:
            return selected
        order = YOUTUBE_VIDEO_QUALITY_ORDER if mode == "video" else YOUTUBE_AUDIO_QUALITY_ORDER
        if selected not in order:
            return available[-1] if available else selected
        wanted_index = order.index(selected)
        best_match = None
        best_distance = 999
        for value in available:
            if value not in order:
                continue
            distance = abs(order.index(value) - wanted_index)
            if distance < best_distance:
                best_distance = distance
                best_match = value
        return best_match or (available[-1] if available else selected)

    def download_item(self, url: str, output_dir: Path, mode: str, selected_quality: str, audio_format: str) -> tuple[Path, str]:
        info = self._extract_info(url)
        available = [option.value for option in self._build_quality_options(info, mode)]
        resolved_quality = self.pick_quality(available, selected_quality, mode)
        title = self._sanitize_name(info.get("title") or "youtube_download")
        template = str(output_dir / f"{title}.%(ext)s")

        ydl_opts = {
            "quiet": True,
            "noplaylist": True,
            "outtmpl": template,
            "merge_output_format": "mp4",
        }

        if mode == "video":
            max_height = resolved_quality.replace("p", "")
            ydl_opts["format"] = f"bestvideo[height<={max_height}]+bestaudio/best[height<={max_height}]"
        else:
            ydl_opts["format"] = "bestaudio/best"
            ydl_opts["postprocessors"] = [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": audio_format,
                "preferredquality": "0",
            }]

        with YoutubeDL(ydl_opts) as ydl:
            result = ydl.extract_info(url, download=True)
            final_path = Path(ydl.prepare_filename(result))
            if mode == "audio":
                final_path = final_path.with_suffix(f".{audio_format}")
            return final_path, resolved_quality

    def _extract_info(self, url: str) -> dict:
        with YoutubeDL({"quiet": True, "skip_download": True, "noplaylist": True}) as ydl:
            return ydl.extract_info(url, download=False)

    def _build_quality_options(self, info: dict, mode: str) -> list[YouTubeQualityOption]:
        formats = info.get("formats") or []
        if mode == "video":
            heights = sorted({f"{fmt.get('height')}p" for fmt in formats if fmt.get("vcodec") != "none" and fmt.get("height")}, key=self._sort_quality)
            return [YouTubeQualityOption(value=value, label=value) for value in heights]
        abr_values = sorted(
            {value for value in (self._normalize_audio_bitrate(fmt.get("abr")) for fmt in formats if fmt.get("acodec") != "none" and fmt.get("abr")) if value is not None},
            key=self._sort_quality,
        )
        values = [value for value in abr_values if value is not None]
        if values and "best" not in values:
            values.append("best")
        return [YouTubeQualityOption(value=value, label=value.upper()) for value in values]

    def _normalize_audio_bitrate(self, abr: object) -> str | None:
        if abr is None:
            return None
        try:
            numeric = int(round(float(abr)))
        except Exception:
            return None
        return f"{numeric}k"

    def _sort_quality(self, value: str) -> int:
        digits = re.sub(r"\D", "", value)
        return int(digits) if digits else 999999

    def _sanitize_name(self, value: str) -> str:
        cleaned = re.sub(r"[\\/:*?\"<>|]+", "_", value).strip()
        return cleaned[:160] or "youtube_download"
