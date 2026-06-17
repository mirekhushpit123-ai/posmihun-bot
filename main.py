import asyncio
import random
import logging
import datetime
import json
import os
from zoneinfo import ZoneInfo

import aiohttp
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.exceptions import TelegramConflictError
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# .env підхоплюється для локального запуску; на Railway не потрібен
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

# ============================================================
#  НАЛАШТУВАННЯ (читаються зі змінних середовища / .env)
# ============================================================
# BOT_TOKEN          — токен від @BotFather (ОБОВ'ЯЗКОВО)
# OPENROUTER_API_KEY — безкоштовний ключ з openrouter.ai (для AI-функцій)
# AI_MODEL           — модель OpenRouter (за замовч. безкоштовна Gemma 4 31B)
# DATA_DIR           — папка для groups.json (на Railway — Volume, напр. /data)
# ------------------------------------------------------------
BOT_TOKEN = os.getenv("BOT_TOKEN")  # перевіряємо вже під час запуску (див. main())

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
AI_MODEL = os.getenv("AI_MODEL", "google/gemma-4-31b-it:free")
# Якщо безкоштовна модель зайнята (429) — пробуємо наступні по черзі (різні
# провайдери + авто-роутер). Можна перевизначити через AI_MODELS (через кому).
_env_models = os.getenv("AI_MODELS", "")
AI_MODELS = [m.strip() for m in _env_models.split(",") if m.strip()] or [
    AI_MODEL,
    "meta-llama/llama-3.3-70b-instruct:free",
    "qwen/qwen3-next-80b-a3b-instruct:free",
    "openrouter/free",
]
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

DATA_DIR = os.getenv("DATA_DIR", ".")
os.makedirs(DATA_DIR, exist_ok=True)
GROUPS_FILE = os.path.join(DATA_DIR, "groups.json")
JOKES_FILE = os.path.join(DATA_DIR, "jokes_index.json")

# Вмикач AI-брифу в ранковому привітанні (False — завжди простий текст)
MORNING_AI_BRIEF = True

# ============================================================
#  ДВА БРАТИ: розумний (AI) і тупуватий (резерв зі шпаргалки)
#  Імена можна змінити — все підхопиться автоматично.
# ============================================================
SHOW_BROTHER_LABELS = True          # False — прибрати підписи братів
SMART_NAME = "Розумник"             # розумний брат — відповідає через AI
DUMB_NAME = "Тугодум"               # тупуватий брат — читає наперед записане
SMART_EMOJI = "🧠"
DUMB_EMOJI = "🥴"
# Що каже тупий брат, коли розумний "спить" (API не відповів):
SLEEPING_LINES = [
    "{smart} зара дрихне, тож тримай від мене:",
    "{smart} спить як убитий — ну, що в зошиті маю, те й кажу:",
    "Будити {smart}? Та ну його. Ось зі шпаргалки:",
    "{smart} знову заснув над книжками. Слухай тоді мене:",
    "Тссс… {smart} хропе. Я по-простому, як умію:",
]


def smart_msg(text: str) -> str:
    """Відповідь розумного брата (AI спрацював)."""
    if SHOW_BROTHER_LABELS:
        return f"{SMART_EMOJI} {SMART_NAME}:\n{text}"
    return text


def dumb_msg(content: str) -> str:
    """Відповідь тупого брата: каже, що розумний спить, і дає резерв."""
    if not SHOW_BROTHER_LABELS:
        return content
    sleep = random.choice(SLEEPING_LINES).format(smart=SMART_NAME)
    return f"{DUMB_EMOJI} {DUMB_NAME}: {sleep}\n\n{content}"


def dumb_ask_fallback() -> str:
    """Окремий резерв для /ask — тупий брат не вміє відповідати на складне."""
    line = (f"{DUMB_EMOJI} {DUMB_NAME}: {SMART_NAME} зара спить 😴, а я в розумних "
            f"питаннях не сильний. Спитай ще раз, як він прокинеться.")
    if SHOW_BROTHER_LABELS:
        return f"{line}\n\nА поки тримай мудрість: {random.choice(WISDOMS)}"
    return "😔 AI зараз недоступний. Спробуй пізніше."


KYIV = ZoneInfo("Europe/Kyiv")
MONTHS_GEN = [
    "січня", "лютого", "березня", "квітня", "травня", "червня",
    "липня", "серпня", "вересня", "жовтня", "листопада", "грудня",
]
WEEKDAYS = [
    "понеділок", "вівторок", "середа", "четвер",
    "п'ятниця", "субота", "неділя",
]

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN) if BOT_TOKEN else None  # None у консольному тесті
dp = Dispatcher()


def date_human_ua() -> str:
    now = datetime.datetime.now(KYIV)
    return f"{now.day} {MONTHS_GEN[now.month - 1]} {now.year} року, {WEEKDAYS[now.weekday()]}"


# ============================================================
#  ШПАРГАЛКА ТУПОГО БРАТА (резерв, коли AI недоступний)
# ============================================================
WISDOMS = [
    "Без труда нема плода.", "Хто рано встає, тому Бог дає.", "Зробив діло — гуляй сміло.",
    "Праця чоловіка годує, а лінь марнує.", "Хто не працює, той не їсть.", "Де руки й охота, там скора робота.",
    "Людина пізнається в праці.", "Не кажи «гоп», поки не перескочиш.", "Очі страшаться, а руки роблять.",
    "Добре роби — добре й буде.", "Хто сіє вчасно, той буде рясно.", "Не відкладай на завтра те, що можна зробити сьогодні.",
    "Коваль кує, поки залізо гаряче.", "Праця — основа щастя.", "Хто рано встав, той збагатів.",
    "Ледачому й піч холодна.", "Лінь перш за тебе народилась.", "Де лінь, там і злидні.",
    "Ледачий двічі робить.", "Хто спить до обіду, той не знає привіду.", "Лежачого хліба не боїться.",
    "Без охоти нема роботи.", "Ледар і голодний, і холодний.", "Дурний лежить, а розумний біжить.",
    "Лінивому завжди свято.", "Скажи мені, хто твій друг, і я скажу, хто ти.", "Друзі пізнаються в біді.",
    "Один за всіх і всі за одного.", "Не май сто рублів, а май сто друзів.", "Друг — то другий я.",
    "Справжній друг — то великий скарб.", "Без друга на світі туго.", "Дружнє слово — що весняний дощ.",
    "Шануй батька і матір — буде тобі добро на землі.", "Які батьки, такі й діти.", "Яблуко від яблуні недалеко падає.",
    "Без сім'ї людина — що дерево без коріння.", "Батьківська хата — найтепліше місце.", "Вчися змолоду — пригодиться на старість.",
    "Розум — найбільший скарб.", "Книга — джерело мудрості.", "Учись, поки є час.", "Мудрість приходить з роками.",
]

JOKES = [
    "Один хлопчик не вмів вимовляти слово шість. Прийшов в магазин і каже: — Дайте мені сім пачок масла, одну не треба.",
    "Коханий, що ти читаєш? – Свідоцтво про шлюб.. – Навіщо??? - Термін придатності шукаю…",
    "Боїшся стрибати з парашутом? – Так. – Стрибай без нього.",
    "Уночі поліція зупиняє п'яненьку дамочку: – Куди поспішаємо? – На лекцію.",
    "Трамвай поїхав — шафа склалася. Сусід: – Давай знову зберемо, я залізу всередину, подивлюся, що там не так…",
    "Лікарю, ви пам'ятаєте, що порекомендували мені від депресії? – Так, завести коханця!",
    "Не розумію… Чому штани, в яких найкраще лежати на дивані, називаються спортивними?",
    "Операційна. Медсестра кричить: – У нього з'явився пульс, він повертається! Лікар: – Повертатися — погана прикмета.",
    "Докторе, я зламав ногу в двох місцях! — Ви запам'ятали ці місця? — Так. — Тоді більше туди не ходіть.",
    "На м'ясокомбінаті одна корова запитує іншу: – Ти тут вперше? – Ні, блін, удруге!",
    "Гугл – це напевно жінка: ніколи не дасть тобі закінчити фразу і запропонує свій варіант продовження…",
    "Якщо тобі щось тяжко нести, уяви що ти це стирив!",
    "Маленький Абрамчик запитує маму: – Мам, а Дід Мороз під кожну ялинку ставить подарунки? – Звичайно. – То чого ми тільки 1 ялинку поставили?",
    "Якщо раптом ви виявили в себе симптоми грипу — 200 грам з перцем і все як рукою зніме. Якщо не виявили — все одно випийте, глибоко сидить зараза…",
]

MORNING_GREETINGS = [
    "☀️ Доброго ранку! Нехай цей день принесе натхнення, нові досягнення та море позитивних емоцій. Починай його з посмішки!",
    "☕️ Ранок — це чудовий час для нових починань! Бажаю продуктивного дня, легких рішень і гарного настрою.",
    "🌅 Новий день — новий шанс! Нехай сьогоднішній ранок подарує тобі енергію для підкорення всіх поставлених цілей.",
    "✨ Прокидайся та сяй! Бажаю, щоб цей день був наповнений успіхами, приємними сюрпризами та чудовими людьми навколо.",
]

ZODIAC = [
    "Овен", "Телець", "Близнюки", "Рак", "Лев", "Діва",
    "Терези", "Скорпіон", "Стрілець", "Козеріг", "Водолій", "Риби",
]


# ============================================================
#  РОЗУМНИЙ БРАТ — AI (OpenRouter). None = "він заснув".
# ============================================================
async def ai_chat(prompt: str, max_tokens: int = 450, temperature: float = 0.9):
    """Питаємо розумного брата (OpenRouter). Пробуємо кілька безкоштовних моделей
    по черзі; якщо всі зайняті/недоступні — повертаємо None (відповість тупий брат)."""
    if not OPENROUTER_API_KEY:
        return None
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://t.me/",
        "X-Title": "PosmihunchykBot",
    }
    timeout = aiohttp.ClientTimeout(total=40)
    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            for model in AI_MODELS:
                payload = {
                    "model": model,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                }
                try:
                    async with session.post(OPENROUTER_URL, headers=headers, json=payload) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            content = (data["choices"][0]["message"]["content"] or "").strip()
                            if "</think>" in content:  # прибрати «роздуми» reasoning-моделей
                                content = content.split("</think>")[-1].strip()
                            if content:
                                return content
                            logging.warning("Порожня відповідь від %s, пробую наступну…", model)
                        elif resp.status == 429:
                            logging.warning("Модель %s зайнята (429), пробую наступну…", model)
                        else:
                            logging.error("OpenRouter %s (%s): %s", resp.status, model, await resp.text())
                except Exception as e:
                    logging.error("AI error (%s): %s", model, e)
    except Exception as e:
        logging.error("AI session error: %s", e)
    return None


async def ai_today_brief():
    prompt = (
        f"Сьогодні {date_human_ua()}. Напиши коротке тепле повідомлення українською "
        f"для дружнього чату. Включи по пунктах з емодзі:\n"
        f"1) 📅 яке сьогодні число і день тижня;\n"
        f"2) 🎉 1–2 цікаві свята або міжнародні дні, що припадають саме на сьогодні "
        f"(якщо не впевнений — пропусти, НЕ вигадуй);\n"
        f"3) 😇 чиї сьогодні іменини / день ангела за церковним календарем "
        f"(1–3 імені; якщо не впевнений — пропусти);\n"
        f"4) ✨ один короткий цікавий факт або думку дня.\n"
        f"Пиши живо, 4–7 рядків. Без слів «Доброго ранку» на початку. Не вигадуй фактів."
    )
    return await ai_chat(prompt, max_tokens=500, temperature=0.7)


async def ai_joke():
    topics = [
        "життя", "роботу", "тварин", "кота", "сім'ю", "школу", "відпустку",
        "технології", "їжу", "спорт", "лікарів", "сусідів", "погоду", "гроші",
    ]
    prompt = (
        f"Розкажи один короткий смішний український анекдот (2–5 речень) на тему: "
        f"{random.choice(topics)}. Виведи ТІЛЬКИ сам анекдот, без вступу і пояснень. "
        f"Гумор добрий, без образ."
    )
    return await ai_chat(prompt, max_tokens=300, temperature=1.1)


async def ai_fact():
    cats = [
        "космос", "історію України", "тварин", "науку", "українську мову",
        "географію", "техніку", "море", "гори", "їжу", "людське тіло", "музику",
    ]
    prompt = (
        f"Напиши один короткий цікавий і ПРАВДИВИЙ факт українською на тему: "
        f"{random.choice(cats)}. 1–2 речення, почни з «🤓 А ви знали, що…». Без вигадок."
    )
    return await ai_chat(prompt, max_tokens=200, temperature=0.8)


async def ai_horoscope(sign: str):
    prompt = (
        f"Напиши короткий жартівливий гороскоп на сьогодні для знаку «{sign}» "
        f"українською: 2–3 речення, з гумором, дрібкою оптимізму та емодзі."
    )
    return await ai_chat(prompt, max_tokens=220, temperature=1.0)


async def ai_ask(question: str):
    prompt = (
        f"Ти — дружній і корисний помічник у Telegram-чаті. Відповідай українською, "
        f"стисло і по суті. Питання користувача: {question}"
    )
    return await ai_chat(prompt, max_tokens=700, temperature=0.6)


# ============================================================
#  ГОТОВІ ВІДПОВІДІ (об'єднують обох братів)
# ============================================================
async def joke_text():
    ai = await ai_joke()
    return smart_msg(f"😂 {ai}") if ai else dumb_msg(f"😂 {next_static_joke()}")


async def fact_text():
    ai = await ai_fact()
    return smart_msg(ai) if ai else dumb_msg(f"🤓 А ви знали, що… {random.choice(WISDOMS)}")


async def day_text():
    ai = await ai_today_brief()
    return smart_msg(ai) if ai else dumb_msg(f"📅 Сьогодні: {date_human_ua()}\n📜 {random.choice(WISDOMS)}")


async def horoscope_text(sign: str):
    ai = await ai_horoscope(sign)
    return smart_msg(ai) if ai else dumb_msg(
        f"🔮 {sign}: зорі сьогодні мовчать, але я скажу — усміхнись і випий кави ☕️")


# ============================================================
#  ЗБЕРЕЖЕННЯ ГРУП / ІНДЕКСУ
# ============================================================
def load_groups():
    if not os.path.exists(GROUPS_FILE):
        return set()
    with open(GROUPS_FILE, "r", encoding="utf-8") as f:
        try:
            return set(json.load(f))
        except Exception:
            return set()


def save_group(chat_id):
    groups = load_groups()
    if chat_id not in groups:
        groups.add(chat_id)
        with open(GROUPS_FILE, "w", encoding="utf-8") as f:
            json.dump(list(groups), f)


def get_joke_index():
    if not os.path.exists(JOKES_FILE):
        return 0
    try:
        with open(JOKES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return 0


def save_joke_index(index):
    with open(JOKES_FILE, "w", encoding="utf-8") as f:
        json.dump(index, f)


def next_static_joke():
    idx = get_joke_index()
    joke = JOKES[idx % len(JOKES)]
    save_joke_index((idx + 1) % len(JOKES))
    return joke


# ============================================================
#  КНОПКИ
# ============================================================
def get_menu_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📜 Мудрість дня", callback_data="get_wisdom"),
         InlineKeyboardButton(text="😂 Анекдот", callback_data="get_joke")],
        [InlineKeyboardButton(text="📅 Що сьогодні", callback_data="get_today"),
         InlineKeyboardButton(text="🤓 Факт", callback_data="get_fact")],
        [InlineKeyboardButton(text="🔮 Гороскоп", callback_data="get_horo_menu")],
    ])


def get_horo_kb():
    rows, row = [], []
    for i, sign in enumerate(ZODIAC, 1):
        row.append(InlineKeyboardButton(text=sign, callback_data=f"horo:{sign}"))
        if i % 3 == 0:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    return InlineKeyboardMarkup(inline_keyboard=rows)


async def typing(chat_id):
    try:
        await bot.send_chat_action(chat_id, "typing")
    except Exception:
        pass


# ============================================================
#  КОМАНДИ
# ============================================================
HELP_TEXT = (
    "🤖 <b>Нас тут двоє братів:</b>\n"
    f"{SMART_EMOJI} <b>{SMART_NAME}</b> — розумний, відповідає через інтернет (AI).\n"
    f"{DUMB_EMOJI} <b>{DUMB_NAME}</b> — простак, відповідає зі шпаргалки, "
    f"коли {SMART_NAME} спить.\n\n"
    "<b>Команди:</b>\n"
    "/joke — свіжий анекдот 😂\n"
    "/wisdom — мудрість дня 📜\n"
    "/day — що сьогодні за день: свята, іменини, опис 📅\n"
    "/fact — цікавий факт 🤓\n"
    "/horoscope — гороскоп на сьогодні 🔮\n"
    "/ask <i>питання</i> — спитай розумного брата про будь-що 💬\n"
    "/menu — показати кнопки\n"
    "/help — ця довідка\n\n"
    "А ще щоранку о 7:00 ми вітаємо чат і розповідаємо, що цікавого сьогодні. ☀️"
)


@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    save_group(message.chat.id)
    await message.answer(
        "Привіт! Я бот <b>ПоСмІхУнЧиК</b> 😊\n"
        f"Нас двоє братів: {SMART_EMOJI} <b>{SMART_NAME}</b> (розумний, з інтернету) "
        f"і {DUMB_EMOJI} <b>{DUMB_NAME}</b> (простак зі шпаргалки). "
        f"Як {SMART_NAME} спить — {DUMB_NAME} підстрахує.\n\n"
        "Тисни кнопки нижче або глянь /help 🌾",
        reply_markup=get_menu_kb(),
        parse_mode="HTML",
    )


@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    save_group(message.chat.id)
    await message.answer(HELP_TEXT, parse_mode="HTML")


@dp.message(Command("menu"))
async def cmd_menu(message: types.Message):
    save_group(message.chat.id)
    await message.answer("Обери, що показати 👇", reply_markup=get_menu_kb())


@dp.message(Command("wisdom"))
async def cmd_wisdom(message: types.Message):
    save_group(message.chat.id)
    await message.answer(f"📜 {random.choice(WISDOMS)}")


@dp.message(Command("joke"))
async def cmd_joke(message: types.Message):
    save_group(message.chat.id)
    await typing(message.chat.id)
    await message.answer(await joke_text())


@dp.message(Command("day", "today"))
async def cmd_day(message: types.Message):
    save_group(message.chat.id)
    await typing(message.chat.id)
    await message.answer(await day_text())


@dp.message(Command("fact"))
async def cmd_fact(message: types.Message):
    save_group(message.chat.id)
    await typing(message.chat.id)
    await message.answer(await fact_text())


@dp.message(Command("horoscope", "horo"))
async def cmd_horoscope(message: types.Message):
    save_group(message.chat.id)
    parts = (message.text or "").split(maxsplit=1)
    if len(parts) > 1:
        sign = parts[1].strip().capitalize()
        await typing(message.chat.id)
        await message.answer(await horoscope_text(sign))
    else:
        await message.answer("🔮 Обери свій знак зодіаку:", reply_markup=get_horo_kb())


@dp.message(Command("ask"))
async def cmd_ask(message: types.Message):
    save_group(message.chat.id)
    parts = (message.text or "").split(maxsplit=1)
    if len(parts) < 2:
        await message.answer(
            "💬 Напиши питання після команди, напр.:\n<code>/ask хто написав «Кобзар»?</code>",
            parse_mode="HTML")
        return
    await typing(message.chat.id)
    answer = await ai_ask(parts[1].strip())
    await message.answer(smart_msg(answer) if answer else dumb_ask_fallback())


# ============================================================
#  CALLBACK-КНОПКИ
# ============================================================
@dp.callback_query(F.data == "get_wisdom")
async def cb_wisdom(callback: types.CallbackQuery):
    await callback.message.answer(f"📜 {random.choice(WISDOMS)}")
    await callback.answer()


@dp.callback_query(F.data == "get_joke")
async def cb_joke(callback: types.CallbackQuery):
    await callback.answer()
    await typing(callback.message.chat.id)
    await callback.message.answer(await joke_text())


@dp.callback_query(F.data == "get_today")
async def cb_today(callback: types.CallbackQuery):
    await callback.answer()
    await typing(callback.message.chat.id)
    await callback.message.answer(await day_text())


@dp.callback_query(F.data == "get_fact")
async def cb_fact(callback: types.CallbackQuery):
    await callback.answer()
    await typing(callback.message.chat.id)
    await callback.message.answer(await fact_text())


@dp.callback_query(F.data == "get_horo_menu")
async def cb_horo_menu(callback: types.CallbackQuery):
    await callback.message.answer("🔮 Обери свій знак зодіаку:", reply_markup=get_horo_kb())
    await callback.answer()


@dp.callback_query(F.data.startswith("horo:"))
async def cb_horo_sign(callback: types.CallbackQuery):
    await callback.answer()
    sign = callback.data.split(":", 1)[1]
    await typing(callback.message.chat.id)
    await callback.message.answer(await horoscope_text(sign))


# ============================================================
#  РОЗСИЛКА ЗА РОЗКЛАДОМ
# ============================================================
async def broadcast(text):
    for chat_id in load_groups():
        try:
            await bot.send_message(chat_id=chat_id, text=text)
        except Exception as e:
            logging.error("Помилка в %s: %s", chat_id, e)


async def build_morning_text():
    """Збирає текст ранкового привітання (без розсилки) — зручно й для тесту."""
    greeting = random.choice(MORNING_GREETINGS)
    brief = await ai_today_brief() if MORNING_AI_BRIEF else None
    joke = await ai_joke()

    if brief or joke:
        # Розумний брат бадьорий — вітає сам
        body = [brief] if brief else [f"📅 Сьогодні: {date_human_ua()}"]
        if joke:
            body.append(f"😂 Анекдот дня:\n{joke}")
        return f"{greeting}\n\n{smart_msg(chr(10).join(s for s in body if s))}"
    # Розумний спить — тупий бере все на себе
    canned = (f"📅 Сьогодні: {date_human_ua()}\n"
              f"📜 Мудрість дня: {random.choice(WISDOMS)}\n\n"
              f"😂 {next_static_joke()}")
    return f"{greeting}\n\n{dumb_msg(canned)}"


async def job_morning():
    await broadcast(await build_morning_text())


async def job_joke():
    await broadcast(await joke_text())


async def job_night():
    await broadcast("🌙 На добраніч! Солодких снів, відпочивай та набирайся сил на завтра! 💤")


# ============================================================
#  ЗАПУСК
# ============================================================
async def main():
    if not BOT_TOKEN:
        raise SystemExit(
            "❌ Не задано BOT_TOKEN.\n"
            "   • Щоб запустити СПРАВЖНЬОГО бота — створи свого в @BotFather (/newbot),\n"
            "     встав токен у файл .env і запусти знову.\n"
            "   • Щоб просто потестити функції БЕЗ Telegram — запусти local_test.py"
        )
    scheduler = AsyncIOScheduler(timezone="Europe/Kyiv")
    scheduler.add_job(job_morning, "cron", hour=7, minute=0)
    scheduler.add_job(job_joke, "cron", hour=12, minute=30)
    scheduler.add_job(job_night, "cron", hour=23, minute=0)
    scheduler.start()
    logging.info("Бот запущено. Розумний брат (AI): %s",
                 "на зв'язку" if OPENROUTER_API_KEY else "СПИТЬ (нема ключа, працює лише Тугодум)")
    try:
        await dp.start_polling(bot)
    except TelegramConflictError:
        raise SystemExit(
            "❌ Конфлікт: цей бот уже працює в іншому місці (напр. на Railway).\n"
            "   Telegram не дозволяє слухати одного бота з двох місць одночасно.\n"
            "   Для локального тесту створи СВОГО бота в @BotFather і встав його токен у .env."
        )


if __name__ == "__main__":
    asyncio.run(main())
