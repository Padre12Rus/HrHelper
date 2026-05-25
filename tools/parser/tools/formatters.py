"""
Обёртка над new_formatters: тот же API, что и раньше, для совместимости с ботом.
Стили загружаются из parser/template/style.json.
"""

from pathlib import Path

from .new_tools.new_formatters import DocxRichTextBuilder, load_style_from_json

# Путь к style.json в template (относительно этого файла: tools/formatters.py -> template/style.json)
_STYLE_PATH = Path(__file__).resolve().parent.parent / "template" / "style.json"
_builder = DocxRichTextBuilder(load_style_from_json(str(_STYLE_PATH)))

# --- Утилиты (как в старом API) ---

def clean_upper(raw_str):
    return _builder.clean_text(raw_str, uppercase=True)


def add_segment(rt, text, *, bold=False):
    """Добавляет сегмент текста в RichText."""
    if text:
        _builder.add_segment(rt, str(text), bold=bold)


def build_rt(*segments):
    """Строит RichText из строк или кортежей (текст, bold)."""
    return _builder.build_rt(*segments)


# --- Простые поля ---

def format_simple_field(raw_value, uppercase=False, bold=True):
    return _builder.format_simple_field(raw_value, uppercase=uppercase, bold=bold)


def format_fio(val):
    return _builder.format_fio(val)


def format_vacancy(val):
    return _builder.format_vacancy(val)


def format_total_year_work(val):
    return _builder.format_total_year_work(val)


def format_project_backround(val):
    """Опечатка в названии сохранена для совместимости с json_to_docx и ботом."""
    return _builder.format_project_background(val)


def format_pitch(val):
    return _builder.format_pitch(val)


def format_language(val):
    return _builder.format_language(val)


def format_employment(val):
    return _builder.format_employment(val)


def format_status(val):
    return _builder.format_status(val)


def format_role_in_project(val):
    return _builder.format_role_in_project(val)


def format_skills_tools_in_project(val):
    return _builder.format_skills_tools_in_project(val)


def format_project_name(raw_name, raw_period):
    return _builder.format_project_name(raw_name, raw_period)


# --- Сложные блоки ---

def format_skills_tools(raw_data):
    return _builder.format_skills_tools(raw_data)


def format_education(education_data):
    return _builder.format_education(education_data)


def format_courses_list(raw_courses):
    return _builder.format_courses_list(raw_courses)


def format_list_for_word(raw_text):
    return _builder.format_list_for_word(raw_text)
