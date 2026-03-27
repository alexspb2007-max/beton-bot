import asyncio
import os
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

from models import init_db, User, SessionLocal

API_TOKEN = os.getenv("BOT_TOKEN") or "8612467052:AAHXvs8HLgpcwPOq7yexP0-5f_y3iDH_v0Y"
SITE_URL = os.getenv("SITE_URL") or "http://localhost:8000"

dp = Dispatcher()


def get_or_create_user(tg_user):
    db = SessionLocal()
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
    db.close()
    return user


@dp.message(F.text == "/start")
async def start(message: Message):
    init_db()
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


async def main():
    init_db()
    bot = Bot(token=API_TOKEN)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
