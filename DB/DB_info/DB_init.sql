-- ==============================================================================
-- Скрипт инициализации базы данных для ATS / Outstaff системы
-- СУБД: PostgreSQL
-- ==============================================================================

-- 1. Создание пользовательских типов данных (Enum)
CREATE TYPE staff_role AS ENUM ('director', 'hunter', 'admin');
CREATE TYPE candidate_status AS ENUM ('new', 'bench', 'on_project', 'outstaff');

-- ==============================================================================
-- 2. Таблица: system_users (Персонал компании)
-- Описание: Хранит данные директоров, HR (хантеров) и системных администраторов.
-- ==============================================================================
CREATE TABLE system_users (
    id SERIAL PRIMARY KEY,
    login VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    fio VARCHAR(255) NOT NULL,
    role staff_role NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Индекс для быстрого поиска при авторизации
CREATE INDEX idx_system_users_login ON system_users(login);


-- ==============================================================================
-- 3. Таблица: candidates (База соискателей / разработчиков)
-- Описание: Хранит метаданные кандидатов и их полный профиль в формате JSONB,
-- который генерируется Нейромодулем на основе резюме.
-- ==============================================================================
CREATE TABLE candidates (
    id SERIAL PRIMARY KEY,
    hr_id INTEGER REFERENCES system_users(id) ON DELETE SET NULL,
    fio VARCHAR(255) NOT NULL,
    current_status candidate_status DEFAULT 'new' NOT NULL,
    parsed_json_profile JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Индексы для фильтрации во фронтенде (список кандидатов)
CREATE INDEX idx_candidates_status ON candidates(current_status);
CREATE INDEX idx_candidates_hr_id ON candidates(hr_id);

-- GIN Индекс: КРИТИЧЕСКИ ВАЖЕН для быстрого поиска внутри структуры JSONB!
CREATE INDEX idx_candidates_jsonb_profile ON candidates USING GIN (parsed_json_profile);


-- ==============================================================================
-- 4. Таблица: resume_templates (Шаблоны и стили экспорта резюме)
-- Описание: Хранит конфигурации стилей (style.json) и пути к базовым файлам .docx
-- для генерации корпоративных резюме под разных клиентов (Сбер, Яндекс и т.д.).
-- ==============================================================================
CREATE TABLE resume_templates (
    id SERIAL PRIMARY KEY,
    company_name VARCHAR(255) UNIQUE NOT NULL,    -- Название формата (например, "Сбербанк")
    style_config JSONB NOT NULL,                  -- Тот самый JSON с настройками шрифтов
    docx_file_path VARCHAR(500) NOT NULL,         -- Путь к файлу шаблона на сервере
    is_active BOOLEAN DEFAULT TRUE NOT NULL,      -- Флаг актуальности шаблона
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Индексы для быстрого отображения списка доступных шаблонов в интерфейсе
CREATE INDEX idx_resume_templates_company_name ON resume_templates(company_name);
CREATE INDEX idx_resume_templates_is_active ON resume_templates(is_active);