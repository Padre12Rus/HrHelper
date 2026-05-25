"""
Модуль форматирования данных для документов Word с использованием docxtpl.

Архитектура:
- DocxRichTextBuilder: класс для построения RichText объектов на основе Style JSON
- Разделение данных (Data JSON) и стилей (Style JSON)
- Гибкая настройка форматирования через конфигурацию
"""

from typing import Any, Dict, List, Optional, Union
from docxtpl import RichText


class StyleConfig:
    """
    Класс для работы с конфигурацией стилей.
    Предоставляет удобный доступ к настройкам шрифтов и форматирования.
    """
    
    def __init__(self, style_dict: Dict[str, Any]):
        """
        Инициализация конфигурации стилей.
        
        Args:
            style_dict: Словарь с настройками стилей
        """
        self._config = style_dict
        self._default = style_dict.get('default', {})
        self._field_styles = style_dict.get('field_styles', {})
    
    def get_font(self, field_type: str = None, style_type: str = 'regular') -> str:
        """Получить название шрифта."""
        if field_type and field_type in self._field_styles:
            return self._field_styles[field_type].get('font', self._default.get('font', 'Calibri Light'))
        
        fonts = self._default.get('fonts', {})
        return fonts.get(style_type, self._default.get('font', 'Calibri Light'))
    
    def get_size(self, field_type: str = None, style_type: str = 'regular') -> int:
        """Получить размер шрифта в полупунктах."""
        if field_type and field_type in self._field_styles:
            return self._field_styles[field_type].get('size', self._default.get('size', 21))
        
        sizes = self._default.get('sizes', {})
        return sizes.get(style_type, self._default.get('size', 21))
    
    def get_bold(self, field_type: str = None, style_type: str = 'regular') -> bool:
        """Получить флаг жирного шрифта."""
        if field_type and field_type in self._field_styles:
            return self._field_styles[field_type].get('bold', False)
        return style_type == 'bold' or style_type == 'header'
    
    def get_italic(self, field_type: str = None) -> bool:
        """Получить флаг курсива."""
        if field_type and field_type in self._field_styles:
            return self._field_styles[field_type].get('italic', False)
        return False
    
    def get_uppercase(self, field_type: str = None) -> bool:
        """Получить флаг преобразования в верхний регистр."""
        if field_type and field_type in self._field_styles:
            return self._field_styles[field_type].get('uppercase', False)
        return False
    
    def get_field_config(self, field_type: str) -> Dict[str, Any]:
        """Получить полную конфигурацию для типа поля."""
        return self._field_styles.get(field_type, {})


class DocxRichTextBuilder:
    """
    Класс для построения RichText объектов на основе конфигурации стилей.
    
    Разделяет логику форматирования данных и их визуального оформления.
    Все настройки шрифтов, размеров и стилей берутся из Style JSON.
    """
    
    def __init__(self, style_config: Union[Dict[str, Any], StyleConfig]):
        """
        Инициализация построителя с конфигурацией стилей.
        
        Args:
            style_config: Словарь с настройками стилей или объект StyleConfig
        """
        if isinstance(style_config, StyleConfig):
            self.style = style_config
        else:
            self.style = StyleConfig(style_config)
    
    # --- Утилиты ---
    
    @staticmethod
    def clean_text(raw_str: Any, uppercase: bool = False) -> str:
        """
        Очистка и нормализация текста.
        
        Args:
            raw_str: Исходная строка
            uppercase: Преобразовать в верхний регистр
            
        Returns:
            Очищенная строка
        """
        if not raw_str:
            return ""
        text = str(raw_str).strip()
        return text.upper() if uppercase else text
    
    def add_segment(
        self, 
        rt: RichText, 
        text: str,
        field_type: str = None,
        style_type: str = 'regular',
        bold: bool = None,
        italic: bool = None,
        font: str = None,
        size: int = None
    ) -> None:
        """
        Добавляет сегмент текста в RichText с настройками из конфига.
        
        Args:
            rt: Объект RichText
            text: Текст для добавления
            field_type: Тип поля для получения стилей из конфига
            style_type: Тип стиля ('regular', 'bold', 'header')
            bold: Переопределение флага bold
            italic: Переопределение флага italic
            font: Переопределение шрифта
            size: Переопределение размера
        """
        if not text:
            return
        
        # Определяем параметры форматирования
        final_font = font or self.style.get_font(field_type, style_type)
        final_size = size or self.style.get_size(field_type, style_type)
        final_bold = bold if bold is not None else self.style.get_bold(field_type, style_type)
        final_italic = italic if italic is not None else self.style.get_italic(field_type)
        
        rt.add(
            str(text),
            bold=final_bold,
            italic=final_italic,
            font=final_font,
            size=final_size
        )
    
    def build_rt(
        self,
        *segments,
        field_type: str = None,
        style_type: str = 'regular'
    ) -> RichText:
        """
        Строит RichText из последовательности сегментов.
        
        Args:
            segments: Строки или кортежи (текст, bold) или словари с параметрами
            field_type: Тип поля для стилей
            style_type: Тип стиля по умолчанию
            
        Returns:
            Объект RichText
        """
        rt = RichText()
        
        for seg in segments:
            if not seg:
                continue
            
            if isinstance(seg, dict):
                # Словарь с полными параметрами
                text = seg.get('text', '')
                self.add_segment(
                    rt,
                    text,
                    field_type=seg.get('field_type', field_type),
                    style_type=seg.get('style_type', style_type),
                    bold=seg.get('bold'),
                    italic=seg.get('italic'),
                    font=seg.get('font'),
                    size=seg.get('size')
                )
            elif isinstance(seg, tuple):
                # Кортеж (текст, bold)
                text, bold = seg
                self.add_segment(rt, text, field_type=field_type, style_type=style_type, bold=bold)
            else:
                # Простая строка
                self.add_segment(rt, seg, field_type=field_type, style_type=style_type)
        
        return rt
    
    # --- Простые поля ---
    
    def format_simple_field(
        self,
        raw_value: Any,
        field_type: str = None,
        uppercase: bool = None,
        bold: bool = None
    ) -> RichText:
        """
        Форматирование простого текстового поля.
        
        Args:
            raw_value: Исходное значение
            field_type: Тип поля для получения стилей
            uppercase: Преобразовать в верхний регистр
            bold: Жирный шрифт
            
        Returns:
            Объект RichText
        """
        if uppercase is None and field_type:
            uppercase = self.style.get_uppercase(field_type)
        
        text = self.clean_text(raw_value, uppercase=uppercase or False)
        
        if bold is None and field_type:
            bold = self.style.get_bold(field_type)
        
        return self.build_rt((text, bold if bold is not None else False), field_type=field_type)
    
    def format_fio(self, value: Any) -> RichText:
        """Форматирование ФИО."""
        return self.format_simple_field(value, field_type='fio')
    
    def format_vacancy(self, value: Any) -> RichText:
        """Форматирование названия вакансии."""
        return self.format_simple_field(value, field_type='vacancy')
    
    def format_total_year_work(self, value: Any) -> RichText:
        """Форматирование общего стажа работы."""
        return self.format_simple_field(value, field_type='total_year_work')
    
    def format_project_background(self, value: Any) -> RichText:
        """Форматирование описания проектов."""
        return self.format_simple_field(value, field_type='project_background')
    
    def format_pitch(self, value: Any) -> RichText:
        """Форматирование краткого описания (pitch)."""
        text = value if value else ""
        return self.build_rt(text, field_type='pitch')
    
    def format_language(self, value: Any) -> RichText:
        """Форматирование языков."""
        return self.build_rt(value if value else "", field_type='language')
    
    def format_employment(self, value: Any) -> RichText:
        """Форматирование типа занятости."""
        return self.build_rt(value if value else "", field_type='employment')
    
    def format_status(self, value: Any) -> RichText:
        """Форматирование статуса."""
        return self.build_rt(value if value else "", field_type='status')
    
    def format_role_in_project(self, value: Any) -> RichText:
        """Форматирование роли в проекте."""
        return self.build_rt(value if value else "", field_type='role_in_project')
    
    def format_skills_tools_in_project(self, value: Any) -> RichText:
        """Форматирование навыков/инструментов в проекте."""
        return self.build_rt(value if value else "", field_type='skills_tools_in_project')
    
    def format_project_name(self, raw_name: Any, raw_period: Any) -> RichText:
        """
        Форматирование названия проекта с периодом.
        
        Args:
            raw_name: Название проекта
            raw_period: Период работы
            
        Returns:
            Объект RichText
        """
        return self.build_rt(raw_name, '\n', raw_period, field_type='project_name')
    
    # --- Сложные блоки ---
    
    def format_skills_tools(self, raw_data: Union[str, List[str]]) -> RichText:
        """
        Обрабатывает список навыков в формате "Категория: Значение".
        
        Args:
            raw_data: Строка с переносами или список строк
            
        Returns:
            Объект RichText с форматированными навыками
        """
        rt = RichText()
        if not raw_data:
            return rt
        
        # Преобразуем в список строк
        items = raw_data if isinstance(raw_data, list) else str(raw_data).split('\n')
        
        field_config = self.style.get_field_config('skills_tools')
        category_bold = field_config.get('category_bold', True)
        
        for i, item in enumerate(items):
            text = str(item).strip()
            if not text:
                continue
            
            if ':' in text:
                # Разделяем категорию и значения
                category, values = text.split(':', 1)
                self.add_segment(rt, category.strip() + ":", field_type='skills_tools', bold=category_bold)
                self.add_segment(rt, " " + values.strip(), field_type='skills_tools', bold=False)
            else:
                self.add_segment(rt, text, field_type='skills_tools')
            
            # Добавляем перенос строки между элементами (кроме последнего)
            if i < len(items) - 1:
                self.add_segment(rt, '\n', field_type='skills_tools')
        
        return rt
    
    def format_education(self, education_data: List[Union[Dict, str]]) -> RichText:
        """
        Формирует блок образования.
        
        Поддерживает два формата:
        - Словарь с ключами: type, institution, year, speciality
        - Строка с разделением через \n
        
        Args:
            education_data: Список записей об образовании
            
        Returns:
            Объект RichText с отформатированным блоком образования
        """
        rt = RichText()
        if not education_data:
            return rt
        
        field_config = self.style.get_field_config('education')
        header_bold = field_config.get('header_bold', True)
        detail_bold = field_config.get('detail_bold', False)
        
        for i, item in enumerate(education_data):
            if isinstance(item, dict):
                # Обработка словаря
                edu_type = item.get('type', '').strip()
                institution = item.get('institution', '').strip()
                year = item.get('year', '').strip()
                speciality = item.get('speciality', '').strip()
                
                # Формируем заголовок (учреждение + год)
                header_parts = [p for p in [institution, year] if p]
                header = ", ".join(header_parts)
                
                # Добавляем тип образования
                if edu_type:
                    self.add_segment(rt, edu_type, field_type='education', bold=header_bold)
                
                # Добавляем заголовок
                if header:
                    if edu_type:
                        self.add_segment(rt, '\n', field_type='education')
                    self.add_segment(rt, header, field_type='education', bold=header_bold)
                
                # Добавляем специальность
                if speciality:
                    if edu_type or header:
                        self.add_segment(rt, '\n', field_type='education')
                    self.add_segment(rt, speciality, field_type='education', bold=detail_bold)
            
            elif isinstance(item, str):
                # Обработка строки: первая строка жирная, остальные - обычные
                parts = item.split('\n', 1)
                self.add_segment(rt, parts[0], field_type='education', bold=header_bold)
                if len(parts) > 1:
                    self.add_segment(rt, '\n' + parts[1], field_type='education', bold=detail_bold)
            
            # Добавляем двойной перенос между записями (кроме последней)
            if i < len(education_data) - 1:
                self.add_segment(rt, '\n\n', field_type='education')
        
        return rt
    
    def format_courses_list(self, raw_courses: List[Union[Dict, str]]) -> List[RichText]:
        """
        Форматирует список курсов.
        
        Формат вывода: "Год, Название курса"
        
        Args:
            raw_courses: Список курсов (словари или строки)
            
        Returns:
            Список объектов RichText (по одному на курс)
        """
        processed_list = []
        
        if not raw_courses:
            return processed_list
        
        for item in raw_courses:
            rt = RichText()
            text_row = ""
            
            if isinstance(item, dict):
                # Обработка словаря
                name = item.get('name', '').strip()
                year = item.get('year', '').strip()
                
                # Формируем строку: Год, Название
                parts = []
                if year:
                    parts.append(year)
                if name:
                    parts.append(name)
                
                text_row = ", ".join(parts)
            
            elif isinstance(item, str):
                # Строка используется как есть
                text_row = item.strip()
            
            if text_row:
                self.add_segment(rt, text_row, field_type='courses')
                processed_list.append(rt)
        
        return processed_list
    
    def format_list_for_word(self, raw_text: Union[str, List[str]]) -> List[RichText]:
        """
        Форматирует данные для маркированного списка Word.
        
        Очищает строки от маркеров (•, -, *, —) и возвращает список RichText объектов.
        
        Args:
            raw_text: Строка с переносами или список строк
            
        Returns:
            Список объектов RichText (по одному на элемент списка)
        """
        processed_list = []
        
        if not raw_text:
            return processed_list
        
        # Преобразуем в список строк
        lines = raw_text if isinstance(raw_text, list) else str(raw_text).split('\n')
        lines = [str(line).strip() for line in lines if str(line).strip()]
        
        for line in lines:
            # Очищаем от маркеров списка в начале строки
            clean_text = line.lstrip('•-*—· ').strip()
            
            if clean_text:
                rt = RichText()
                self.add_segment(rt, clean_text, field_type='list_item')
                processed_list.append(rt)
        
        return processed_list
    
    # --- Главный метод сборки контекста ---
    
    def build(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Собирает полный контекст для render() на основе Data JSON.
        
        Этот метод является точкой входа для преобразования данных в формат,
        готовый для передачи в docxtpl.render().
        
        Структура данных соответствует parser/template/example.json
        
        Args:
            data: Словарь с данными (Data JSON)
            
        Returns:
            Словарь контекста для docxtpl
        """
        context = {}
        
        # Простые поля
        if 'fio' in data:
            context['fio'] = self.format_fio(data['fio'])
        
        if 'vacancy' in data:
            context['vacancy'] = self.format_vacancy(data['vacancy'])
        
        if 'total_year_work' in data:
            context['total_year_work'] = self.format_total_year_work(data['total_year_work'])
        
        # project_backround (с опечаткой в оригинале example.json)
        if 'project_backround' in data:
            context['project_backround'] = self.format_project_background(data['project_backround'])
        
        if 'pitch' in data:
            context['pitch'] = self.format_pitch(data['pitch'])
        
        # languages (множественное число)
        if 'languages' in data:
            context['languages'] = self.format_language(data['languages'])
        
        # citizenship_location (новое поле)
        if 'citizenship_location' in data:
            context['citizenship_location'] = self.format_simple_field(
                data['citizenship_location'],
                field_type='citizenship_location'
            )
        
        if 'employment' in data:
            context['employment'] = self.format_employment(data['employment'])
        
        if 'status' in data:
            context['status'] = self.format_status(data['status'])
        
        # skills_and_tools (вместо skills_tools)
        if 'skills_and_tools' in data:
            context['skills_and_tools'] = self.format_skills_tools(data['skills_and_tools'])
        
        # Образование
        if 'education' in data:
            context['education'] = self.format_education(data['education'])
        
        # advanced_training (вместо courses)
        if 'advanced_training' in data:
            context['advanced_training'] = self.format_courses_list(data['advanced_training'])
        
        # Проекты с новой структурой из example.json
        if 'projects' in data:
            formatted_projects = []
            for project in data['projects']:
                proj_context = {}
                
                # place_time_raw - название компании
                if 'place_time_raw' in project:
                    proj_context['place_time_raw'] = self.format_simple_field(
                        project['place_time_raw'],
                        field_type='place_time_raw'
                    )
                
                # period - период работы
                if 'period' in project:
                    proj_context['period'] = self.format_simple_field(
                        project['period'],
                        field_type='period'
                    )
                
                # Можно объединить place_time_raw и period для совместимости
                if 'place_time_raw' in project and 'period' in project:
                    proj_context['name_and_period'] = self.format_project_name(
                        project['place_time_raw'],
                        project['period']
                    )
                
                # role_in_project
                if 'role_in_project' in project:
                    proj_context['role_in_project'] = self.format_role_in_project(
                        project['role_in_project']
                    )
                
                # task_on_project - список задач
                if 'task_on_project' in project:
                    proj_context['task_on_project'] = self.format_list_for_word(
                        project['task_on_project']
                    )
                
                # achievements_in_project - список достижений
                if 'achievements_in_project' in project:
                    proj_context['achievements_in_project'] = self.format_list_for_word(
                        project['achievements_in_project']
                    )
                
                # skills_tools_in_project
                if 'skills_tools_in_project' in project:
                    proj_context['skills_tools_in_project'] = self.format_skills_tools_in_project(
                        project['skills_tools_in_project']
                    )
                
                formatted_projects.append(proj_context)
            
            context['projects'] = formatted_projects
        
        # Дополнительные поля (списки) для обратной совместимости
        list_fields = ['responsibilities', 'achievements', 'certifications']
        for field in list_fields:
            if field in data:
                context[field] = self.format_list_for_word(data[field])
        
        return context


# --- Вспомогательные функции для загрузки конфигурации ---

def load_style_from_json(filepath: str) -> StyleConfig:
    """
    Загружает конфигурацию стилей из JSON файла.
    
    Args:
        filepath: Путь к файлу style.json
        
    Returns:
        Объект StyleConfig
    """
    import json
    with open(filepath, 'r', encoding='utf-8') as f:
        style_dict = json.load(f)
    return StyleConfig(style_dict)


def load_data_from_json(filepath: str) -> Dict[str, Any]:
    """
    Загружает данные из JSON файла.
    
    Args:
        filepath: Путь к файлу data.json
        
    Returns:
        Словарь с данными
    """
    import json
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)
