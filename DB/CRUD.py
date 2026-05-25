from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from passlib.context import CryptContext # pip install passlib[bcrypt]

# ДОБАВЛЕНО: импорт ResumeTemplate
from models import SystemUser, Candidate, StaffRole, CandidateStatus, ResumeTemplate

# Настройка для хеширования паролей
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# =====================================================================
# БЛОК 1: Взаимодействие с персоналом (SystemUser)
# =====================================================================

async def register_user(session: AsyncSession, login: str, raw_password: str, fio: str, role: StaffRole) -> SystemUser:
    """Регистрация нового сотрудника (Директор, HR, Админ)"""
    hashed_password = pwd_context.hash(raw_password)
    
    new_user = SystemUser(
        login=login,
        hashed_password=hashed_password,
        fio=fio,
        role=role
    )
    session.add(new_user)
    await session.commit()
    await session.refresh(new_user)
    return new_user

async def authenticate_user(session: AsyncSession, login: str, raw_password: str) -> SystemUser | None:
    """Проверка логина и пароля (для эндпоинта /login)"""
    stmt = select(SystemUser).where(SystemUser.login == login)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()
    
    if not user:
        return None
        
    # Проверяем, совпадает ли введенный пароль с хешем в БД
    if not pwd_context.verify(raw_password, user.hashed_password):
        return None
        
    return user

async def update_user_data(session: AsyncSession, user_id: int, new_fio: str = None, new_role: StaffRole = None) -> SystemUser | None:
    """Изменение данных сотрудника"""
    stmt = select(SystemUser).where(SystemUser.id == user_id)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()
    
    if not user:
        return None
        
    if new_fio:
        user.fio = new_fio
    if new_role:
        user.role = new_role
        
    await session.commit()
    await session.refresh(user)
    return user


# =====================================================================
# БЛОК 2: Взаимодействие с ресурсами (Кандидаты / Резюме)
# =====================================================================

async def add_candidate(session: AsyncSession, hr_id: int, fio: str, parsed_json: dict) -> Candidate:
    """Добавление нового распарсенного кандидата в систему"""
    new_candidate = Candidate(
        hr_id=hr_id,
        fio=fio,
        current_status=CandidateStatus.NEW,
        parsed_json_profile=parsed_json
    )
    session.add(new_candidate)
    await session.commit()
    await session.refresh(new_candidate)
    return new_candidate

async def get_candidate_json(session: AsyncSession, candidate_id: int) -> dict | None:
    """Получение JSON-профиля конкретного кандидата"""
    stmt = select(Candidate.parsed_json_profile).where(Candidate.id == candidate_id)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()

async def change_candidate_status(session: AsyncSession, candidate_id: int, new_status: CandidateStatus) -> Candidate | None:
    """Изменение статуса кандидата (например, с BENCH на ON_PROJECT)"""
    stmt = update(Candidate).where(Candidate.id == candidate_id).values(current_status=new_status).returning(Candidate)
    
    result = await session.execute(stmt)
    await session.commit()
    return result.scalar_one_or_none()


# =====================================================================
# БЛОК 3: Взаимодействие с шаблонами экспорта (ResumeTemplate)
# =====================================================================

async def add_template(session: AsyncSession, company_name: str, style_config: dict, docx_file_path: str) -> ResumeTemplate:
    """Добавление нового корпоративного шаблона (обычно доступно только Admin)"""
    new_template = ResumeTemplate(
        company_name=company_name,
        style_config=style_config,
        docx_file_path=docx_file_path,
        is_active=True
    )
    session.add(new_template)
    await session.commit()
    await session.refresh(new_template)
    return new_template

async def get_active_templates(session: AsyncSession) -> list[ResumeTemplate]:
    """Получение списка всех активных шаблонов (для выпадающего списка у HR во фронтенде)"""
    stmt = select(ResumeTemplate).where(ResumeTemplate.is_active == True)
    result = await session.execute(stmt)
    return list(result.scalars().all())

async def get_template_by_id(session: AsyncSession, template_id: int) -> ResumeTemplate | None:
    """Получение конкретного шаблона со стилями для генерации Word-файла"""
    stmt = select(ResumeTemplate).where(ResumeTemplate.id == template_id, ResumeTemplate.is_active == True)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()

async def deactivate_template(session: AsyncSession, template_id: int) -> ResumeTemplate | None:
    """'Мягкое' удаление шаблона: он скрывается из интерфейса HR, но остается в БД для истории"""
    stmt = update(ResumeTemplate).where(ResumeTemplate.id == template_id).values(is_active=False).returning(ResumeTemplate)
    result = await session.execute(stmt)
    await session.commit()
    return result.scalar_one_or_none()