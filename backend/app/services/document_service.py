import shutil
import subprocess
import uuid
from pathlib import Path


DOCUMENT_TARGET_FORMATS = {"PDF", "DOCX", "ODT", "TXT"}

UNSUPPORTED_CONVERSIONS: dict[str, set[str]] = {
    ".pdf": {"DOCX", "PDF"},
}

LIBREOFFICE_FILTER_MAP = {
    "DOCX": 'docx:"MS Word 2007 XML"',
    "PDF": 'pdf:"writer_pdf_Export"',
    "ODT": "odt",
    "TXT": 'txt:"Text (encoded)"',
}


class DocumentConversionService:
    def convert(self, *, source_path: Path, output_dir: Path, target_format: str) -> Path:
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

        safe_name = f"bambam_doc_{uuid.uuid4().hex}{source_path.suffix}"
        safe_source = Path("/tmp") / safe_name
        shutil.copy2(source_path, safe_source)

        convert_to_arg = LIBREOFFICE_FILTER_MAP.get(normalized_format, normalized_format.lower())

        tmp_out_dir = Path("/tmp") / f"bambam_out_{uuid.uuid4().hex}"
        tmp_out_dir.mkdir(parents=True, exist_ok=True)

        try:
            cmd = [
                "libreoffice",
                "--headless",
                "-env:UserInstallation=file:///tmp/libreoffice_profile",
                "--convert-to",
                convert_to_arg,
                "--outdir",
                str(tmp_out_dir),
                str(safe_source),
            ]

            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if (
                result.returncode != 0
                or "source file could not be loaded" in result.stderr
                or "source file could not be loaded" in result.stdout
                or "no export filter" in result.stderr
                or "no export filter" in result.stdout
                or "Please verify input parameters" in result.stderr
            ):
                raise RuntimeError(
                    f"LibreOffice conversion failed.\n"
                    f"RETURN CODE: {result.returncode}\n"
                    f"STDOUT: {result.stdout}\n"
                    f"STDERR: {result.stderr}"
                )

            converted_tmp = tmp_out_dir / f"{safe_source.stem}.{normalized_format.lower()}"
            final_output = output_dir / f"{source_path.stem}.{normalized_format.lower()}"

            if not converted_tmp.exists():
                error_msg = f"Converted document file was not produced.\nSTDOUT: {result.stdout}\nSTDERR: {result.stderr}"
                raise RuntimeError(error_msg)

            shutil.move(str(converted_tmp), str(final_output))
        finally:
            safe_source.unlink(missing_ok=True)
            shutil.rmtree(tmp_out_dir, ignore_errors=True)

        return final_output
