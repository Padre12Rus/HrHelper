# PDF → JSON (Gemini) → DOCX CV

## Стек
- google-generativeai (Gemini)
- python-dotenv
- docxtpl

## Структура
- `parser/gemini_to_json.py` — просит Gemini разобрать PDF и вернуть JSON по шаблону.
- `parser/json_to_docx.py` — рендерит DOCX по шаблону из JSON.
- `parser/tools/formatters.py` — форматирует поля в RichText для docxtpl.
- `parser/template/example.json` — пример ожидаемой структуры JSON.
- `parser/template/placeholders_cv_docx.docx` — DOCX-шаблон с плейсхолдерами.

## Настройка
1. Создать `.env` с `GEMINI_API_KEY=<ключ>`.
2. Поместить PDF для разбора, указать путь в `parser/gemini_to_json.py` (переменная `source_file`).
3. Проверить пути к `prompt.md` (инструкция модели) и `example.json`.

## Использование
### 1) Получить JSON из PDF
```bash
python parser/gemini_to_json.py
