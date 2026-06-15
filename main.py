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

# Список жартів для рандому
JOKES = [
    "— Чому ти спізнився? — Через табличку 'Обережно, ремонт'! — І що? — Ну, я йшов дуже обережно!",
    "Кум до кума: — Куме, а чому ви не купите корову? — А навіщо? — Ну, молоко, сметана, сир... — Ой, куме, а з ким же я тоді горілку буду пити?",
    "Зустрічаються двоє: — Як справи? — Та нормально. Купив собі собаку. — Яку? — Ну, таку, що гавкає. — А яку ще? — Ну, як — яку? Таку, що гавкає, коли хтось приходить!"
]

def get_wisdom_from_web():
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        url = "https://dovidka.biz.ua/ukrayinski-narodni-prisliv-ya-pro-pratsyu/"
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Шукаємо всі елементи, що містять текст мудрості
        items = soup.find_all('li')
        quotes = [item.text for item in items if len(item.text) > 15]
        
        return random.choice(quotes) if quotes else "🌾 Де козак, там і слава."
    except Exception as e:
        logging.error(f"Error fetching wisdom: {e}")
        return "🌾 Хто рано встає, тому Бог дає!"

def get_menu_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🧠 Мудрість дня", callback_data="get_wisdom")],
        [InlineKeyboardButton(text="😂 Свіжий анекдот", callback_data="get_joke")]
    ])

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("Привіт! Я твій бот-помічник. Обирай, що хочеш:", reply_markup=get_menu_kb())

@dp.callback_query(F.data == "get_wisdom")
async def send_wisdom(callback: types.CallbackQuery):
    await callback.message.answer(f"🧠 {get_wisdom_from_web()}")
    await callback.answer()

@dp.callback_query(F.data == "get_joke")
async def send_joke(callback: types.CallbackQuery):
    await callback.message.answer(f"😂 {random.choice(JOKES)}")
    await callback.answer()

async def job_morning():
    await bot.send_message(chat_id=CHAT_ID, text=f"☀️ Доброго ранку! {get_wisdom_from_web()}")

async def main():
    scheduler = AsyncIOScheduler(timezone="Europe/Kyiv")
    scheduler.add_job(job_morning, "cron", hour=7, minute=0)
    scheduler.start()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
