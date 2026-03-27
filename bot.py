import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

from models import init_db, User, SessionLocal

# Включаем логирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

API_TOKEN = os.getenv("BOT_TOKEN") or "8612467052:AAHXvs8HLgpcwPOq7yexP0-5f_y3iDH_v0Y"
SITE_URL = os.getenv("SITE_URL") or "https://beton-bot-nf6s.onrender.com"

dp = Dispatcher()


def get_or_create_user(tg_user):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.tg_id == tg_user.id).first()
        if not user:
            user = User(
                tg_id=tg_user.id,
                username=tg_user.username,
                first_name=tg_user.first_name,
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            logger.info(f"Новый пользователь создан: {tg_user.id}")
        else:
            logger.info(f"Пользователь уже есть: {tg_user.id}")
        return user
    except Exception as e:
        logger.error(f"Ошибка БД: {e}")
        db.rollback()
        raise
    finally:
        db.close()


@dp.message(F.text == "/start")
async def start(message: Message):
    logger.info(f"Получен /start от {message.from_user.id}")
    try:
        user = get_or_create_user(message.from_user)
        url = f"{SITE_URL}/schedule?tg_id={user.tg_id}"

        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="Открыть расписание", url=url)]
            ]
        )

        await message.answer(
            "Вы зарегистрированы. Нажмите кнопку, чтобы открыть расписание.",
            reply_markup=kb
        )
        logger.info(f"Ответ отправлен пользователю {message.from_user.id}")
    except Exception as e:
        logger.error(f"Ошибка в /start: {e}")
        await message.answer("Произошла ошибка. Попробуйте позже.")


async def main():
    logger.info("Запуск бота...")
    init_db()
    logger.info("БД инициализирована")
    bot = Bot(token=API_TOKEN)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())