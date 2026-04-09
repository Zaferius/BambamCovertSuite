import shutil
import subprocess
import uuid
import tempfile
from pathlib import Path

from app.core.config import get_settings
from app.core.constants import (
    LIBREOFFICE_BINARY,
    LIBREOFFICE_LOAD_ERROR_MARKERS,
    LIBREOFFICE_PROFILE_DIR_NAME,
    LIBREOFFICE_TEMP_OUTPUT_PREFIX,
    LIBREOFFICE_TEMP_SOURCE_PREFIX,
)


DOCUMENT_TARGET_FORMATS = {"PDF", "DOCX", "ODT", "TXT"}

UNSUPPORTED_CONVERSIONS: dict[str, set[str]] = {
    ".pdf": {"DOCX", "PDF"},
}

LIBREOFFICE_FILTER_MAP = {
    "DOCX": "docx:MS Word 2007 XML",
    "PDF": "pdf:writer_pdf_Export",
    "ODT": "odt",
    "TXT": "txt:Text (encoded)",
}


class DocumentConversionService:
    def convert(self, *, source_path: Path, output_dir: Path, target_format: str) -> Path:
        settings = get_settings()
        normalized_format = target_format.upper()

        if normalized_format not in DOCUMENT_TARGET_FORMATS:
            raise ValueError(f"Unsupported document target format: {target_format}")

        source_ext = source_path.suffix.lower()
        blocked = UNSUPPORTED_CONVERSIONS.get(source_ext, set())
        if normalized_format in blocked:
            raise ValueError(
                f"Converting {source_ext.upper()} to {normalized_format} is not supported. "
                f"PDF files can be converted to: ODT, TXT."
            )
        
        output_dir.mkdir(parents=True, exist_ok=True)

        temp_root = settings.temp_dir.resolve()
        temp_root.mkdir(parents=True, exist_ok=True)
        safe_name = f"{LIBREOFFICE_TEMP_SOURCE_PREFIX}{uuid.uuid4().hex}{source_path.suffix}"
        safe_source = temp_root / safe_name
        shutil.copy2(source_path, safe_source)

        convert_to_arg = LIBREOFFICE_FILTER_MAP.get(normalized_format, normalized_format.lower())

        tmp_out_dir = Path(
            tempfile.mkdtemp(prefix=LIBREOFFICE_TEMP_OUTPUT_PREFIX, dir=str(temp_root))
        )
        office_profile_dir = temp_root / LIBREOFFICE_PROFILE_DIR_NAME
        office_profile_dir.mkdir(parents=True, exist_ok=True)

        try:
            cmd = [
                LIBREOFFICE_BINARY,
                "--headless",
                f"-env:UserInstallation=file:///{office_profile_dir.as_posix()}",
                "--convert-to",
                convert_to_arg,
                "--outdir",
                str(tmp_out_dir),
                str(safe_source),
            ]

            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            stdout = result.stdout or ""
            stderr = result.stderr or ""
            combined_output = "\n".join([stdout, stderr])
            if result.returncode != 0 or any(marker in combined_output for marker in LIBREOFFICE_LOAD_ERROR_MARKERS):
                raise RuntimeError(
                    f"LibreOffice conversion failed.\n"
                    f"RETURN CODE: {result.returncode}\n"
                    f"STDOUT: {stdout}\n"
                    f"STDERR: {stderr}"
                )

            converted_tmp = tmp_out_dir / f"{safe_source.stem}.{normalized_format.lower()}"
            final_output = output_dir / f"{source_path.stem}.{normalized_format.lower()}"

            if not converted_tmp.exists():
                error_msg = f"Converted document file was not produced.\nSTDOUT: {stdout}\nSTDERR: {stderr}"
                raise RuntimeError(error_msg)

            shutil.move(str(converted_tmp), str(final_output))
        finally:
            safe_source.unlink(missing_ok=True)
            shutil.rmtree(tmp_out_dir, ignore_errors=True)

        return final_output
