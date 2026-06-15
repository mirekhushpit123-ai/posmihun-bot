import asyncio
import logging
import random
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from apscheduler.schedulers.asyncio import AsyncIOScheduler

BOT_TOKEN = "8934888528:AAEK53K2NRsqDBSFwIa9Y3t5DnD534FhJk0"
CHAT_ID = -1004391417926

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
scheduler = AsyncIOScheduler(timezone="Europe/Kyiv")

WISDOMS = [
    "Де козак там і слава. Бджола мала, а й та працює!",
    "Хто рано встає, тому Бог дає! Праця годує, а лінь марнує.",
    "Без охоти нема роботи. Роби до поту, їж у охоту!"
]

def get_main_menu():
    builder = ReplyKeyboardBuilder()
    builder.button(text="🧠 Мудрість дня")
    builder.button(text="☀️ Ранкове привітання")
    builder.button(text="🌙 Побажати добраніч")
    builder.adjust(1, 2)
    return builder.as_markup(resize_keyboard=True)

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    try:
        await message.answer(
            "👋 Бот ПоСмІхУнЧуК успішно запущений на Render! Виберіть команду:",
            reply_markup=get_main_menu()
        )
    except Exception as e:
        logging.error(f"Error in start: {e}")

async def send_morning_message(target_chat=CHAT_ID):
    try:
        await bot.send_message(chat_id=target_chat, text="☀️ Доброго ранку! Продуктивного дня усім! ☕️")
    except Exception as e:
        logging.error(f"Error morning: {e}")

async def send_wisdom_message(target_chat=CHAT_ID):
    wisdom = random.choice(WISDOMS)
    try:
        await bot.send_message(chat_id=target_chat, text=f"🧠 Хвилинка мудрості:\n\n{wisdom}")
    except Exception as e:
        logging.error(f"Error wisdom: {e}")

async def send_night_message(target_chat=CHAT_ID):
    try:
        await bot.send_message(chat_id=target_chat, text="🌙 На добраніч! Мирних снів! 💤")
    except Exception as e:
        logging.error(f"Error night: {e}")

@dp.message(lambda message: message.text == "🧠 Мудрість дня")
async def btn_wisdom(message: types.Message):
    await send_wisdom_message(target_chat=message.chat.id)

@dp.message(lambda message: message.text == "☀️ Ранкове привітання")
async def btn_morning(message: types.Message):
    await send_morning_message(target_chat=message.chat.id)

@dp.message(lambda message: message.text == "🌙 Побажати добраніч")
async def btn_night(message: types.Message):
    await send_night_message(target_chat=message.chat.id)

def setup_scheduler():
    scheduler.add_job(send_morning_message, "cron", hour=8, minute=0)
    scheduler.add_job(send_wisdom_message, "cron", hour=8, minute=1)
    scheduler.add_job(send_night_message, "cron", hour=23, minute=0)
    scheduler.start()

async def main():
    setup_scheduler()
    # Чистимо старі завислі вебхуки від Hugging Face, щоб звільнити лінію
    await bot.delete_webhook(drop_pending_updates=True)
    logging.info("Починаємо Polling...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        pass
