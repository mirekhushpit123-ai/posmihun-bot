import asyncio
from aiogram import Bot, Dispatcher, executor, types

# Твій токен
bot = Bot(token='7308144211:AAEvE6ZzM7h-R_wR9I-B6Z9Z_pQoK7zZ-8g')
dp = Dispatcher(bot)

@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    await message.reply('Бот успішно запустився на Render!')

if __name__ == '__main__':
    executor.start_polling(dp)
