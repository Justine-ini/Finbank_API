from fastapi import APIRouter
from backend.app.api.routes import home
from backend.app.api.routes.auth import register, activate, login, password_reset, refresh, logout
from backend.app.api.routes.profile import create, update, upload, me, all_profiles
from backend.app.api.routes.next_of_kin import create as create_next_of_kin, all, update as update_next_of_kin, delete

api_router = APIRouter()
api_router.include_router(home.router)
api_router.include_router(register.router)
api_router.include_router(activate.router)
api_router.include_router(login.router)
api_router.include_router(password_reset.router)
api_router.include_router(refresh.router)
api_router.include_router(logout.router)
api_router.include_router(create.router)
api_router.include_router(update.router)
api_router.include_router(upload.router)
api_router.include_router(me.router)
api_router.include_router(all_profiles.router)
api_router.include_router(create_next_of_kin.router)
api_router.include_router(update_next_of_kin.router)
api_router.include_router(delete.router)
api_router.include_router(all.router)
