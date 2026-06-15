import asyncio
import random
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# Твої налаштування
BOT_TOKEN = "8934888528:AAHyXNs1zxsYqE6oQNQAuIbZaDpGmMAK9hA"
CHAT_ID = -1004391417926

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Бази даних для контенту
WISDOMS = [
    "🌾 Де козак, там і слава.",
    "☀️ Хто рано встає, тому Бог дає!",
    "🌳 Без охоти нема роботи.",
    "🌻 Не кажи не вмію, а кажи навчуся.",
    "💪 Велике дерево поволі росте."
]

ADVICES = [
    "🌿 Пийте більше води протягом дня.",
    "🍎 З'їжте яблуко для енергії.",
    "📖 Прочитайте сторінку книги.",
    "🧘 Зробіть коротку розминку для спини."
]

JOKES = [
    "— Чому ти спізнився? — Через табличку 'Обережно, йдуть ремонтні роботи'. — І що? — Ну, я йшов дуже обережно!",
    "Приходить кум до кума: — Куме, а що це у вас собака так виє? — А це він у мене співати вчиться! — А чого ж він так фальшиво? — Та бо він ще нотної грамоти не знає!",
    "Українець купує квиток у касі: — Мені до Києва. — Вам 'туди' чи 'назад'? — Звісно, назад! Бо туди я вже їздив!"
]

# Кнопка для користувачів
def get_menu_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🧠 Отримати мудрість дня", callback_data="get_wisdom")]
    ])

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "Привіт! Я бот ПоСмІхУнЧиК. Я допомагаю створювати чудовий настрій у чаті, "
        "надсилаючи привітання, мудрі слова та анекдоти за розкладом! 😊🌾",
        reply_markup=get_menu_kb()
    )

@dp.callback_query(F.data == "get_wisdom")
async def send_random_wisdom(callback: types.CallbackQuery):
    content = random.choice(WISDOMS + ADVICES)
    await callback.message.answer(f"🧠 *Порада/Мудрість:* {content}")
    await callback.answer()

# Завдання за розкладом
async def job_morning():
    photo = f"https://picsum.photos/800/600?random={random.randint(1, 1000)}"
    await bot.send_photo(chat_id=CHAT_ID, photo=photo, caption="☀️ *Доброго ранку, чате!* Бажаю усім неймовірного натхнення, шаленої енергії та продуктивного дня! Нехай задумане легко вдається! ☕️✨")

async def job_info():
    content = random.choice(WISDOMS + ADVICES)
    await bot.send_message(chat_id=CHAT_ID, text=f"🗓 *На сьогодні:* {content}")

async def job_joke():
    await bot.send_message(chat_id=CHAT_ID, text=f"😂 *Анекдот дня:* {random.choice(JOKES)}")

async def job_night():
    await bot.send_message(chat_id=CHAT_ID, text="🌙 *На добраніч, дорогі друзі!*\n\nЧас відпочивати від турбот. Бажаю усім міцного сну та найсолодших, мирних снів! До завтра! 💤🧸")

async def main():
    scheduler = AsyncIOScheduler(timezone="Europe/Kyiv")
    # Розклад
    scheduler.add_job(job_morning, "cron", hour=7, minute=0)
    scheduler.add_job(job_info, "cron", hour=7, minute=1)
    scheduler.add_job(job_joke, "cron", hour=12, minute=30)
    scheduler.add_job(job_night, "cron", hour=23, minute=0)
    scheduler.start()
    
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
