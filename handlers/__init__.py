from aiogram import Router
from handlers.start import router as start_router
from handlers.task_group import router as task_group_router
from handlers.task_private import router as task_private_router
from handlers.task_actions import router as task_actions_router
from handlers.task_details import router as task_details_router
from handlers.roles_projects import router as roles_projects_router
from handlers.analytics_export import router as analytics_export_router
from handlers.reports import router as reports_router

main_router = Router()
main_router.include_router(start_router)
main_router.include_router(task_group_router)
main_router.include_router(task_private_router)
main_router.include_router(task_actions_router)
main_router.include_router(task_details_router)
main_router.include_router(roles_projects_router)
main_router.include_router(analytics_export_router)
main_router.include_router(reports_router)

__all__ = ["main_router"]

