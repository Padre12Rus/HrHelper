import os
import asyncio
from markitdown import MarkItDown

md = MarkItDown()

def _sync_convert_to_md(file_path: str) -> str:
    """Синхронная функция, которая делает всю грязную работу"""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Файл не найден: {file_path}")
    
    result = md.convert(file_path)
    return result.text_content

async def extract_markdown_async(file_path: str) -> str:
    """Асинхронная обертка для конвертации в Markdown"""
    return await asyncio.to_thread(_sync_convert_to_md, file_path)