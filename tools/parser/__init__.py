from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from .gemini_to_json import (
    DEFAULT_PROMPT_PATH,
    DEFAULT_TEMPLATE_PATH,
    UnsupportedLocationError,
    UnsupportedMimeTypeError,
    generate_json_dict,
)
from .json_to_docx import generate_cv

BASE_DIR = Path(__file__).parent
DOCX_TEMPLATE_PATH = BASE_DIR / "template" / "placeholders_cv_docx.docx"


def _output_name(input_path: Path, original_name: Optional[str]) -> str:
    if original_name:
        base = Path(original_name).stem or input_path.stem
    else:
        base = input_path.stem
    return f"{base}.docx"


def process_document(source_path: Path, original_name: Optional[str] = None) -> Path:
    input_path = Path(source_path)
    if not input_path.exists():
        raise FileNotFoundError(f"Файл не найден: {input_path}")

    json_path = input_path.with_suffix(".json")
    output_path = input_path.with_name(_output_name(input_path, original_name))

    try:
        json_data = generate_json_dict(
            input_file=input_path,
            instruction_path=DEFAULT_PROMPT_PATH,
            template_path=DEFAULT_TEMPLATE_PATH,
        )
    except UnsupportedLocationError as exc:
        raise RuntimeError("Gemini недоступен в этом регионе. Включи VPN или используй другой API ключ.") from exc
    except UnsupportedMimeTypeError as exc:
        raise RuntimeError("Формат файла не поддерживается Gemini. Отправь PDF/TXT или другой формат.") from exc

    json_path.write_text(json.dumps(json_data, ensure_ascii=False, indent=2), encoding="utf-8")
    generate_cv(json_path=json_path, template_path=DOCX_TEMPLATE_PATH, output_path=output_path)
    return output_path
