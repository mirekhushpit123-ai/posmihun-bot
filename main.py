import asyncio
import random
import logging
import requests
from bs4 import BeautifulSoup
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from apscheduler.schedulers.asyncio import AsyncIOScheduler

BOT_TOKEN = "8934888528:AAHtqHu_QuF-kizOQelQd_S6Ls3gFeHA-RI"
CHAT_ID = -1004391417926

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Функція для отримання мудрості з інтернету
def get_wisdom_from_web():
    try:
        # Беремо випадкову сторінку з сайту з приказками
        url = "https://dovidka.biz.ua/ukrayinski-narodni-prisliv-ya-pro-pratsyu/"
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        quotes = [p.text for p in soup.find_all('p') if len(p.text) > 20]
        return random.choice(quotes)
    except:
        return "🌾 Хто рано встає, тому Бог дає!"

# Клавіатура з двома кнопками
def get_menu_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🧠 Мудрість з інтернету", callback_data="get_wisdom")],
        [InlineKeyboardButton(text="😂 Свіжий анекдот", callback_data="get_joke")]
    ])

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("Привіт! Обирай, що хочеш отримати:", reply_markup=get_menu_kb())

@dp.callback_query(F.data == "get_wisdom")
async def send_wisdom(callback: types.CallbackQuery):
    await callback.message.answer(f"🧠 {get_wisdom_from_web()}")
    await callback.answer()

@dp.callback_query(F.data == "get_joke")
async def send_joke(callback: types.CallbackQuery):
    # Анекдот
    await callback.message.answer("😂 — Чому ти спізнився? — Через табличку 'Обережно, ремонт'! — І що? — Ну, я йшов дуже обережно!")
    await callback.answer()

# Завдання за розкладом
async def job_morning():
    await bot.send_message(chat_id=CHAT_ID, text=f"☀️ Доброго ранку! {get_wisdom_from_web()}")

async def main():
    scheduler = AsyncIOScheduler(timezone="Europe/Kyiv")
    scheduler.add_job(job_morning, "cron", hour=7, minute=0)
    scheduler.start()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
