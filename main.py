import asyncio
import random
import logging
import datetime
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from apscheduler.schedulers.asyncio import AsyncIOScheduler

BOT_TOKEN = "8934888528:AAHtqHu_QuF-kizOQelQd_S6Ls3gFeHA-RI"
CHAT_ID = -1004391417926

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Списки контенту (тут 100+ одиниць)
WISDOMS = [f"Мудрість №{i}: [Тут твоя прикмета/мудрість]" for i in range(1, 101)]
JOKES = [f"Анекдот №{i}: [Тут твій жарт]" for i in range(1, 101)]

def get_day_info():
    days = ["Понеділок", "Вівторок", "Середа", "Четвер", "П'ятниця", "Субота", "Неділя"]
    today = datetime.datetime.now().weekday()
    return days[today]

def get_menu_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🧠 Мудрість дня", callback_data="get_wisdom")],
        [InlineKeyboardButton(text="😂 Свіжий анекдот", callback_data="get_joke")]
    ])

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(f"Привіт! Сьогодні {get_day_info()}. Обирай, що хочеш:", reply_markup=get_menu_kb())

@dp.callback_query(F.data == "get_wisdom")
async def send_wisdom(callback: types.CallbackQuery):
    await callback.message.answer(f"🧠 {random.choice(WISDOMS)}")
    await callback.answer()

@dp.callback_query(F.data == "get_joke")
async def send_joke(callback: types.CallbackQuery):
    await callback.message.answer(f"😂 {random.choice(JOKES)}")
    await callback.answer()

async def job_morning():
    photo = f"https://picsum.photos/800/600?random={random.randint(1, 10000)}"
    day = get_day_info()
    text = f"☀️ Доброго ранку! Сьогодні {day}.\n{random.choice(WISDOMS)}"
    await bot.send_photo(chat_id=CHAT_ID, photo=photo, caption=text)

async def main():
    scheduler = AsyncIOScheduler(timezone="Europe/Kyiv")
    scheduler.add_job(job_morning, "cron", hour=7, minute=0)
    scheduler.start()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
