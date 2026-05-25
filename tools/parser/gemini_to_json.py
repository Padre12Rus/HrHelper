from __future__ import annotations

import json
import os
import time
import warnings
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Union
from urllib.parse import urlparse

import google.generativeai as genai
from google.api_core import exceptions as gae
from googleapiclient.errors import HttpError, ResumableUploadError
from docx import Document
from dotenv import load_dotenv

# Загружаем .env сразу, чтобы переменные были доступны как можно раньше
load_dotenv()

# --- Конфигурация и Константы ---
BASE_DIR = Path(__file__).parent
DEFAULT_PROMPT_PATH = BASE_DIR / "template" / "prompt.md"
DEFAULT_TEMPLATE_PATH = BASE_DIR / "template" / "example.json"
DEFAULT_MODEL_NAME = "gemini-2.5-flash"

GENERATION_CONFIG = {
    "temperature": 0.05,
    "response_mime_type": "application/json",
}

# --- Исключения ---
class GeminiError(Exception):
    """Базовая ошибка Gemini."""

class UnsupportedLocationError(GeminiError):
    """Регион запрещен для использования API."""

class UnsupportedMimeTypeError(GeminiError):
    """Тип файла не поддерживается."""

class ProxyConfigurationError(GeminiError):
    """Ошибка настройки прокси."""

# --- Вспомогательные функции ---
def _read_text_file(path: Union[str, Path]) -> str:
    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(f"Файл не найден: {file_path}")
    with file_path.open("r", encoding="utf-8") as f:
        return f.read()

def _extract_docx_text(path: Path) -> str:
    doc = Document(str(path))
    return "\n".join([p.text for p in doc.paragraphs if p.text])

def _current_date_iso() -> str:
    return datetime.now().date().isoformat()

# --- Основной Класс ---
class GeminiClient:
    def __init__(self, api_key: Optional[str] = None, model_name: str = DEFAULT_MODEL_NAME):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise RuntimeError("GEMINI_API_KEY не установлен.")
        
        self.model_name = model_name
        
        # 1. Сначала настраиваем сеть (прокси)
        self._configure_network()
        
        # 2. Затем конфигурируем библиотеку
        genai.configure(api_key=self.api_key)
        
        # 3. Инициализируем модель (ленивая инициализация, соединение пойдет при первом запросе)
        self.model = None 

    def _configure_network(self) -> None:
        """
        Настраивает переменные окружения для прокси ДО инициализации gRPC.
        """
        proxy = os.getenv("GEMINI_PROXY") or os.getenv("HTTPS_PROXY")
        
        if not proxy:
            return

        parsed = urlparse(proxy)
        scheme = parsed.scheme.lower()

        if scheme.startswith("socks"):
            raise ProxyConfigurationError(
                f"SOCKS прокси ({scheme}) не поддерживаются gRPC клиентом Gemini напрямую. "
                "Используйте HTTP/HTTPS прокси."
            )

        # gRPC (на котором работает Gemini Python SDK) требует правильной схемы.
        # Если указан https прокси, библиотека requests/grpc может требовать http:// префикс 
        # для туннелирования, если это не нативный TLS прокси.
        # Для надежности выставляем системные переменные.
        
        # Нормализация
        final_proxy = proxy
        if scheme == "https":
             # Часто gRPC клиенты лучше работают, если прокси задан как http://host:port 
             # даже для https трафика (метод CONNECT)
             warnings.warn("HTTPS прокси может работать нестабильно с gRPC. Попробуйте HTTP.", RuntimeWarning)

        os.environ["http_proxy"] = final_proxy
        os.environ["https_proxy"] = final_proxy
        os.environ["HTTP_PROXY"] = final_proxy
        os.environ["HTTPS_PROXY"] = final_proxy
        
        # Дополнительно для gRPC (на всякий случай)
        os.environ["GRPC_PROXY_EXP"] = final_proxy

    def _get_model(self, system_instruction: str) -> genai.GenerativeModel:
        """Создает или обновляет модель с новой инструкцией."""
        # Создаем экземпляр модели на лету, чтобы привязать system_instruction
        return genai.GenerativeModel(
            model_name=self.model_name,
            generation_config=GENERATION_CONFIG,
            system_instruction=system_instruction,
        )

    def _handle_errors(self, exc: Exception) -> None:
        """Централизованная обработка ошибок API."""
        msg = str(exc)
        if "User location is not supported" in msg:
            raise UnsupportedLocationError(msg) from exc
        if "Unsupported MIME type" in msg:
            raise UnsupportedMimeTypeError(msg) from exc
        raise GeminiError(f"Ошибка API: {msg}") from exc

    def _upload_file(self, path: Path, timeout: int = 300):
        """Загружает файл и ждет завершения процессинга."""
        try:
            print(f"Загрузка файла: {path.name}...")
            upload = genai.upload_file(str(path))
            
            # Ожидание обработки
            start_time = time.time()
            while upload.state.name == "PROCESSING":
                if time.time() - start_time > timeout:
                    raise TimeoutError("Тайм-аут обработки файла на стороне Google.")
                time.sleep(2)
                upload = genai.get_file(upload.name)
            
            if upload.state.name != "ACTIVE":
                raise GeminiError(f"Ошибка обработки файла: статус {upload.state.name}")
            
            return upload
        except (HttpError, ResumableUploadError, gae.GoogleAPICallError) as e:
            self._handle_errors(e)

    def process_request(
        self, 
        input_file: Union[str, Path], 
        instruction_path: Path, 
        template_path: Path
    ) -> str:
        """
        Единая точка входа для обработки запроса.
        """
        input_path = Path(input_file)
        if not input_path.exists():
            raise FileNotFoundError(f"Входной файл не найден: {input_path}")

        # Читаем промпты
        instruction_text = _read_text_file(instruction_path)
        template_text = _read_text_file(template_path)
        
        # Инициализируем модель с инструкцией
        model = self._get_model(instruction_text)

        current_date = _current_date_iso()
        content_parts = [
            f"Текущая дата (YYYY-MM-DD): {current_date}.",
            "Используй текущую дату для расчетов периодов «Наст. время».",
        ]

        # Логика ветвления по типу файла
        if input_path.suffix.lower() == ".docx":
            # Текст вставляем напрямую (1 запрос)
            doc_text = _extract_docx_text(input_path)
            content_parts.extend([
                "Исходный текст резюме:\n",
                doc_text,
            ])
        else:
            # Бинарные файлы загружаем через File API (2 запроса: upload + generate)
            file_ref = self._upload_file(input_path)
            content_parts.append(file_ref)

        # Добавляем шаблон JSON в конец запроса
        content_parts.extend([
            "\nИспользуй JSON шаблон:\n",
            template_text,
            "\nЗаполни и верни корректный JSON."
        ])

        # Генерация
        try:
            print("Генерация ответа...")
            response = model.generate_content(content_parts)
            return response.text
        except gae.GoogleAPICallError as e:
            self._handle_errors(e)
            return "{}" # Недостижимый код из-за raise, но для линтера

# --- Функции-обертки для совместимости с внешним вызовом ---

def generate_json_from_file(
    input_file: Union[str, Path],
    *,
    instruction_path: Union[str, Path] = DEFAULT_PROMPT_PATH,
    template_path: Union[str, Path] = DEFAULT_TEMPLATE_PATH,
    model_name: str = DEFAULT_MODEL_NAME,
) -> str:
    
    client = GeminiClient(model_name=model_name)
    return client.process_request(input_file, instruction_path, template_path)

def generate_json_dict(
    input_file: Union[str, Path],
    *,
    instruction_path: Union[str, Path] = DEFAULT_PROMPT_PATH,
    template_path: Union[str, Path] = DEFAULT_TEMPLATE_PATH,
    model_name: str = DEFAULT_MODEL_NAME,
) -> Dict[str, Any]:
    
    text = generate_json_from_file(
        input_file,
        instruction_path=instruction_path,
        template_path=template_path,
        model_name=model_name,
    )
    cleaned_text = text.strip()
    # Иногда модель возвращает ```json ... ```, чистим это
    if cleaned_text.startswith("```json"):
        cleaned_text = cleaned_text[7:]
    if cleaned_text.endswith("```"):
        cleaned_text = cleaned_text[:-3]
        
    return json.loads(cleaned_text)

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("input_file")
    parser.add_argument("--prompt", default=str(DEFAULT_PROMPT_PATH))
    parser.add_argument("--template", default=str(DEFAULT_TEMPLATE_PATH))
    parser.add_argument("--model", default=DEFAULT_MODEL_NAME)

    args = parser.parse_args()

    try:
        result = generate_json_from_file(
            args.input_file,
            instruction_path=args.prompt,
            template_path=args.template,
            model_name=args.model,
        )
        print(result)
    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
