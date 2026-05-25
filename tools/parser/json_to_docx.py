from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from docxtpl import DocxTemplate

from .tools import formatters as fmt


def _load_data(json_path: Path) -> Dict[str, Any]:
    with json_path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _build_projects(projects: Any) -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []
    if not isinstance(projects, list):
        return items

    for project in projects:
        if not isinstance(project, dict):
            continue

        raw_place = project.get("place_time_raw") or project.get("name") or ""
        raw_period = project.get("period") or ""

        items.append(
            {
                "project_place_and_work_time": fmt.format_project_name(raw_place, raw_period),
                "role_in_project": fmt.format_role_in_project(project.get("role_in_project")),
                "task_on_project": fmt.format_list_for_word(project.get("task_on_project")),
                "achievements_in_project": fmt.format_list_for_word(project.get("achievements_in_project")),
                "skills_tools_in_project": fmt.format_skills_tools_in_project(project.get("skills_tools_in_project")),
            }
        )

    return items


def generate_cv(json_path: Path | str, template_path: Path | str, output_path: Path | str) -> Path:
    json_file = Path(json_path)
    template_file = Path(template_path)
    output_file = Path(output_path)

    if not json_file.exists():
        raise FileNotFoundError(f"JSON не найден: {json_file}")
    if not template_file.exists():
        raise FileNotFoundError(f"Шаблон DOCX не найден: {template_file}")

    data = _load_data(json_file)
    doc = DocxTemplate(str(template_file))

    context: Dict[str, Any] = {
        "fio": fmt.format_fio(data.get("fio")),
        "vacancy": fmt.format_vacancy(data.get("vacancy")),
        "total_year_work": fmt.format_total_year_work(data.get("total_year_work")),
        "project_backround": fmt.format_project_backround(data.get("project_backround")),
        "pitch": fmt.format_pitch(data.get("pitch")),
        "skills_tools": fmt.format_skills_tools(data.get("skills_and_tools")),
        "education": fmt.format_education(data.get("education")),
        "courses": fmt.format_courses_list(data.get("advanced_training")),
        "languages": fmt.format_language(data.get("languages")),
        "citizenship_location": fmt.format_simple_field(data.get("citizenship_location"), bold=False),
        "employment": fmt.format_employment(data.get("employment")),
        "status": fmt.format_status(data.get("status")),
        "projects": _build_projects(data.get("projects")),
    }

    doc.render(context)
    doc.save(str(output_file))
    return output_file


__all__ = ["generate_cv"]
