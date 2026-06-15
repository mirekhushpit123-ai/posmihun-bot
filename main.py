import asyncio
from aiogram import Bot, Dispatcher, executor, types

API_TOKEN = '7308144211:AAEvE6ZzM7h-R_wR9I-B6Z9Z_pQoK7zZ-8g'

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    await message.reply("Привіт! Бот успішно запущений на хостингу Render!")

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
