from pathlib import Path

from PIL import Image


IMAGE_FORMAT_MAP: dict[str, tuple[str, str]] = {
    "PNG": ("PNG", "png"),
    "JPG": ("JPEG", "jpg"),
    "JPEG": ("JPEG", "jpg"),
    "WEBP": ("WEBP", "webp"),
    "TIFF": ("TIFF", "tiff"),
    "BMP": ("BMP", "bmp"),
    "GIF": ("GIF", "gif"),
    "ICO": ("ICO", "ico"),
}


class ImageConversionService:
    def convert(
        self,
        *,
        source_path: Path,
        output_path: Path,
        target_format: str,
        quality: int = 90,
    ) -> Path:
        normalized_format = target_format.upper()

        if normalized_format not in IMAGE_FORMAT_MAP:
            raise ValueError(f"Unsupported target format: {target_format}")

        pillow_format, _ = IMAGE_FORMAT_MAP[normalized_format]

        with Image.open(source_path) as image:
            save_image = image.convert("RGB") if pillow_format == "JPEG" else image
            save_kwargs: dict[str, int] = {}

            if pillow_format in {"JPEG", "WEBP"}:
                save_kwargs["quality"] = quality

            save_image.save(output_path, format=pillow_format, **save_kwargs)

        return output_path
