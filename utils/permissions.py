from typing import Optional
from database.models import User, UserRole, Task
from config import settings

def is_admin(user: Optional[User], telegram_id: int) -> bool:
    if telegram_id in settings.ADMIN_IDS:
        return True
    return bool(user and user.role == UserRole.ADMIN)

def can_create_task(user: Optional[User], telegram_id: int) -> bool:
    if is_admin(user, telegram_id):
        return True
    return bool(user and user.role in (UserRole.ADMIN, UserRole.MANAGER))

def can_manage_task(user: Optional[User], telegram_id: int, task: Task) -> bool:
    """
    Tugmani bosa oladimi:
    - Vazifa ijrochisi (assignee_id == telegram_id)
    - Vazifa yaratuvchisi (creator_id == telegram_id)
    - Admin yoki Menejer
    """
    if is_admin(user, telegram_id):
        return True
    if user and user.role == UserRole.MANAGER:
        return True
    if task.assignee_id == telegram_id or task.creator_id == telegram_id:
        return True
    return False

def can_approve_task(user: Optional[User], telegram_id: int, task: Task) -> bool:
    """
    Tekshiruvdagi vazifani kim tasdiqlay oladi:
    - Vazifa yaratuvchisi (creator_id == telegram_id)
    - Admin yoki Menejer
    """
    if is_admin(user, telegram_id):
        return True
    if user and user.role in (UserRole.ADMIN, UserRole.MANAGER):
        return True
    if task.creator_id == telegram_id:
        return True
    return False

