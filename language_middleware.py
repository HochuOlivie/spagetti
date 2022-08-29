from aiogram.contrib.middlewares.i18n import I18nMiddleware
from typing import Tuple, Any, Optional
from aiogram import types
from pathlib import Path
import database


I18N_DOMAIN = 'mybot'
BASE_DIR = Path(__file__).parent
LOCALES_DIR = BASE_DIR / 'locales'


async def get_lang(user_id):
    return None


class TMiddleware(I18nMiddleware):
    async def get_user_locale(self, action: str, args: Tuple[Any]) -> Optional[str]:
        user = types.User.get_current()
        return await database.getUserLang(user.id)


def setup_middleware(dp):
    i18n = TMiddleware(I18N_DOMAIN, LOCALES_DIR)
    dp.middleware.setup(i18n)
    return i18n
