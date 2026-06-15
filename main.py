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

# Універсальна функція для отримання контенту
def get_content_from_web(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        content_div = soup.find('div', class_='entry-content') or soup.find('body')
        items = [p.text.strip() for p in content_div.find_all('p') if len(p.text.strip()) > 30 and '.' in p.text]
        return random.choice(items) if items else "Цікава думка загубилася в мережі..."
    except:
        return "Не вдалося отримати контент, спробуйте пізніше."

def get_menu_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🧠 Мудрість дня", callback_data="get_wisdom")],
        [InlineKeyboardButton(text="😂 Свіжий анекдот", callback_data="get_joke")]
    ])

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("Привіт! Я ПоСміХунЧиК. Обирай, що хочеш отримати:", reply_markup=get_menu_kb())

@dp.callback_query(F.data == "get_wisdom")
async def send_wisdom(callback: types.CallbackQuery):
    url = "https://dovidka.biz.ua/ukrayinski-narodni-prisliv-ya-pro-pratsyu/"
    await callback.message.answer(f"🧠 {get_content_from_web(url)}")
    await callback.answer()

@dp.callback_query(F.data == "get_joke")
async def send_joke(callback: types.CallbackQuery):
    url = "https://dovidka.biz.ua/ukrayinski-anekdoti-pro-kuma/"
    await callback.message.answer(f"😂 {get_content_from_web(url)}")
    await callback.answer()

# --- РОЗКЛАД ЗАВДАНЬ ---
async def job_morning():
    url = "https://dovidka.biz.ua/ukrayinski-narodni-prisliv-ya-pro-pratsyu/"
    photo = f"https://picsum.photos/800/600?random={random.randint(1, 1000)}"
    await bot.send_photo(chat_id=CHAT_ID, photo=photo, caption=f"☀️ Доброго ранку! {get_content_from_web(url)}")

async def job_info():
    url = "https://dovidka.biz.ua/ukrayinski-narodni-prisliv-ya-pro-pratsyu/"
    await bot.send_message(chat_id=CHAT_ID, text=f"🗓 Порада на сьогодні: {get_content_from_web(url)}")

async def job_joke():
    url = "https://dovidka.biz.ua/ukrayinski-anekdoti-pro-kuma/"
    await bot.send_message(chat_id=CHAT_ID, text=f"😂 Анекдот дня: {get_content_from_web(url)}")

async def job_night():
    await bot.send_message(chat_id=CHAT_ID, text="🌙 На добраніч! Солодких снів! 💤")

async def main():
    scheduler = AsyncIOScheduler(timezone="Europe/Kyiv")
    # Розклад: ранок (7:00), інформація (7:01), анекдот (12:30), ніч (23:00)
    scheduler.add_job(job_morning, "cron", hour=7, minute=0)
    scheduler.add_job(job_info, "cron", hour=7, minute=1)
    scheduler.add_job(job_joke, "cron", hour=12, minute=30)
    scheduler.add_job(job_night, "cron", hour=23, minute=0)
    scheduler.start()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
