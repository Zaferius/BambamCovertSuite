import subprocess
from pathlib import Path


DOCUMENT_TARGET_FORMATS = {"PDF", "DOCX", "ODT", "TXT"}


class DocumentConversionService:
    def convert(self, *, source_path: Path, output_dir: Path, target_format: str) -> Path:
        normalized_format = target_format.upper()

        if normalized_format not in DOCUMENT_TARGET_FORMATS:
            raise ValueError(f"Unsupported document target format: {target_format}")

        output_dir.mkdir(parents=True, exist_ok=True)

        cmd = [
            "soffice",
            "--headless",
            "--convert-to",
            normalized_format.lower(),
            "--outdir",
            str(output_dir),
            str(source_path),
        ]

        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if result.returncode != 0:
            raise RuntimeError(result.stderr or "LibreOffice document conversion error")

        output_path = output_dir / f"{source_path.stem}.{normalized_format.lower()}"
        if not output_path.exists():
            raise RuntimeError("Converted document file was not produced")

        return output_path
