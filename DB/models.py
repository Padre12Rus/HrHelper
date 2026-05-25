import enum
import datetime
from sqlalchemy import String, ForeignKey, Enum, Index, Boolean
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.sql import func

# Базовый класс для всех моделей
class Base(DeclarativeBase):
    pass

# ==========================================
# 1. Enums (Типы данных)
# ==========================================
class StaffRole(str, enum.Enum):
    DIRECTOR = "director"
    HUNTER = "hunter"
    ADMIN = "admin"

class CandidateStatus(str, enum.Enum):
    NEW = "new"
    BENCH = "bench"
    ON_PROJECT = "on_project"
    OUTSTAFF = "outstaff"

# ==========================================
# 2. Модель: system_users (Внутренний персонал)
# ==========================================
class SystemUser(Base):
    __tablename__ = "system_users"

    id: Mapped[int] = mapped_column(primary_key=True)
    login: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    fio: Mapped[str] = mapped_column(String(255))
    role: Mapped[StaffRole] = mapped_column(Enum(StaffRole, native_enum=True))
    
    created_at: Mapped[datetime.datetime] = mapped_column(server_default=func.now())

    # Связь с кандидатами (Один-ко-Многим)
    added_candidates: Mapped[list["Candidate"]] = relationship(
        back_populates="hr", 
        # cascade="all, delete-orphan" закомментировано, т.к. в SQL у нас стоит ON DELETE SET NULL
        # это правильнее: если HR уволился, его кандидаты остаются в базе
    )

# ==========================================
# 3. Модель: candidates (Кандидаты / Ресурсы)
# ==========================================
class Candidate(Base):
    __tablename__ = "candidates"

    id: Mapped[int] = mapped_column(primary_key=True)
    
    hr_id: Mapped[int | None] = mapped_column(ForeignKey("system_users.id", ondelete="SET NULL"), nullable=True)
    
    fio: Mapped[str] = mapped_column(String(255))
    current_status: Mapped[CandidateStatus] = mapped_column(
        Enum(CandidateStatus, native_enum=True), 
        default=CandidateStatus.NEW,
        index=True
    )
    
    parsed_json_profile: Mapped[dict] = mapped_column(JSONB, nullable=False)
    
    created_at: Mapped[datetime.datetime] = mapped_column(server_default=func.now())

    # Связь обратно к HR
    hr: Mapped["SystemUser"] = relationship(back_populates="added_candidates")

    __table_args__ = (
        Index(
            "idx_candidates_jsonb_profile", 
            "parsed_json_profile", 
            postgresql_using="gin"
        ),
    )


# ==========================================
# 4. Модель: resume_templates (Шаблоны экспорта)
# ==========================================
class ResumeTemplate(Base):
    __tablename__ = "resume_templates"

    id: Mapped[int] = mapped_column(primary_key=True)
    
    # Название формата (например, "Сбербанк", "Яндекс")
    company_name: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    
    # Сюда мы целиком кладем содержимое style.json
    style_config: Mapped[dict] = mapped_column(JSONB, nullable=False)
    
    # Путь к физическому файлу .docx шаблона на диске или в S3
    docx_file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    
    # Флаг актуальности шаблона
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)

    created_at: Mapped[datetime.datetime] = mapped_column(server_default=func.now())