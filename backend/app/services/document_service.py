import shutil
import subprocess
import uuid
from pathlib import Path


DOCUMENT_TARGET_FORMATS = {"PDF", "DOCX", "ODT", "TXT"}


class DocumentConversionService:
    def convert(self, *, source_path: Path, output_dir: Path, target_format: str) -> Path:
        normalized_format = target_format.upper()

        if normalized_format not in DOCUMENT_TARGET_FORMATS:
            raise ValueError(f"Unsupported document target format: {target_format}")

        output_dir.mkdir(parents=True, exist_ok=True)

        safe_name = f"bambam_doc_{uuid.uuid4().hex}{source_path.suffix}"
        safe_source = Path("/tmp") / safe_name
        shutil.copy2(source_path, safe_source)

        try:
            cmd = [
                "libreoffice",
                "--headless",
                "-env:UserInstallation=file:///tmp/libreoffice_profile",
                "--convert-to",
                normalized_format.lower(),
                "--outdir",
                str(output_dir),
                str(safe_source),
            ]

            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if result.returncode != 0 or "source file could not be loaded" in result.stderr or "source file could not be loaded" in result.stdout:
                raise RuntimeError(
                    f"LibreOffice conversion failed.\n"
                    f"RETURN CODE: {result.returncode}\n"
                    f"STDOUT: {result.stdout}\n"
                    f"STDERR: {result.stderr}"
                )

            converted_temp = output_dir / f"{safe_source.stem}.{normalized_format.lower()}"
            final_output = output_dir / f"{source_path.stem}.{normalized_format.lower()}"

            if not converted_temp.exists():
                error_msg = f"Converted document file was not produced.\nSTDOUT: {result.stdout}\nSTDERR: {result.stderr}"
                raise RuntimeError(error_msg)

            converted_temp.rename(final_output)
        finally:
            safe_source.unlink(missing_ok=True)

        return final_output
