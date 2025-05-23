import logging
import asyncio
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command
from dotenv import load_dotenv
import sqlite3
import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime, timedelta
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# Загрузка переменных окружения
load_dotenv(".env")
TOKEN = os.getenv("BOT_TOKEN")

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Инициализация бота и диспетчера
bot = Bot(token=TOKEN)
dp = Dispatcher()

# Обновляем главное меню
main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📚 Факультеты и направления")],
        [KeyboardButton(text="🗓 Расписание"), KeyboardButton(text="📢 Новости")],
        [KeyboardButton(text="🍽 Меню столовой"), KeyboardButton(text="🔔 Напоминания")],
        [KeyboardButton(text="🔗 Полезные ссылки")]  # Добавляем новую кнопку
    ],
    resize_keyboard=True
)

# Словарь для хранения расписаний
user_schedules = {}

# Меню столовой по дням недели
menu = {
    "Понедельник": {
        "Напитки": ["Чай черный - 30₽", "Чай зеленый - 30₽", "Кофе американо - 50₽", "Компот - 35₽", "Морс - 40₽"],
        "Блюда": [
            "Суп гороховый - 120₽", "Пюре с котлетой - 150₽", 
            "Гречка с грибами - 130₽", "Салат овощной - 80₽",
            "Макароны по-флотски - 140₽", "Курица запеченная - 160₽",
            "Рыба на пару - 170₽", "Плов - 150₽",
            "Омлет с овощами - 110₽", "Борщ - 130₽"
        ],
        "Выпечка": ["Булочка с маком - 50₽", "Пирожок с капустой - 45₽", "Круассан - 60₽", "Пирожное картошка - 55₽", "Пончик - 40₽"]
    },
    "Вторник": {
        "Напитки": ["Какао - 45₽", "Чай с лимоном - 35₽", "Кофе латте - 70₽", "Сок апельсиновый - 60₽", "Лимонад - 50₽"],
        "Блюда": [
            "Щи - 120₽", "Гречка с курицей - 150₽", 
            "Картофель жареный - 130₽", "Салат Цезарь - 110₽",
            "Спагетти болоньезе - 160₽", "Гуляш с гарниром - 170₽",
            "Котлета по-киевски - 180₽", "Рагу овощное - 120₽",
            "Сырники - 100₽", "Солянка - 140₽"
        ],
        "Выпечка": ["Пирожок с яблоком - 45₽", "Кекс - 55₽", "Эклер - 65₽", "Пирожное наполеон - 70₽", "Багет - 40₽"]
    },
    "Среда": {
        "Напитки": ["Чай фруктовый - 40₽", "Кофе капучино - 65₽", "Молочный коктейль - 80₽", "Компот ягодный - 45₽", "Горячий шоколад - 60₽"],
        "Блюда": [
            "Суп куриный - 125₽", "Рис с овощами - 140₽", 
            "Котлета рыбная - 150₽", "Салат греческий - 120₽",
            "Лазанья - 170₽", "Голубцы - 160₽",
            "Картофель запеченный - 130₽", "Фаршированный перец - 150₽",
            "Оладьи - 90₽", "Уха - 140₽"
        ],
        "Выпечка": ["Пирожок с вишней - 50₽", "Круассан с шоколадом - 70₽", "Печенье овсяное - 40₽", "Пирожное медовик - 75₽", "Булочка с корицей - 55₽"]
    },
    "Четверг": {
        "Напитки": ["Чай с мятой - 35₽", "Кофе мокко - 75₽", "Сок яблочный - 55₽", "Морс клюквенный - 45₽", "Эспрессо - 50₽"],
        "Блюда": [
            "Борщ украинский - 140₽", "Пельмени - 150₽", 
            "Гречка с грибами - 130₽", "Салат оливье - 110₽",
            "Курица гриль - 170₽", "Картофельное пюре - 120₽",
            "Рыба жареная - 160₽", "Овощи гриль - 130₽",
            "Сырный суп - 135₽", "Блины с мясом - 140₽"
        ],
        "Выпечка": ["Пирожок с картошкой - 45₽", "Круассан с миндалем - 75₽", "Пончик с глазурью - 50₽", "Пирожное птичье молоко - 80₽", "Булочка с изюмом - 50₽"]
    },
    "Пятница": {
        "Напитки": ["Чай с жасмином - 40₽", "Кофе раф - 80₽", "Сок томатный - 50₽", "Компот из сухофруктов - 40₽", "Латте макиато - 85₽"],
        "Блюда": [
            "Суп-пюре грибной - 145₽", "Плов с бараниной - 180₽", 
            "Макароны с сыром - 130₽", "Салат с тунцом - 125₽",
            "Стейк из семги - 220₽", "Картофель по-деревенски - 140₽",
            "Куриные наггетсы - 150₽", "Овощная запеканка - 135₽",
            "Суп харчо - 150₽", "Блинчики с творогом - 120₽"
        ],
        "Выпечка": ["Пирожок с мясом - 55₽", "Круассан с кремом - 80₽", "Печенье шоколадное - 45₽", "Пирожное тирамису - 90₽", "Булочка с кунжутом - 50₽"]
    },
    "Суббота": {
        "Напитки": ["Чай с бергамотом - 45₽", "Кофе по-венски - 90₽", "Сок мультифрукт - 60₽", "Молочный коктейль с бананом - 85₽", "Капучино с сиропом - 95₽"],
        "Блюда": [
            "Суп том ям - 180₽", "Паста карбонара - 190₽", 
            "Стейк из говядины - 250₽", "Салат с креветками - 200₽",
            "Ризотто - 170₽", "Лосось на гриле - 230₽",
            "Фондю - 210₽", "Рататуй - 160₽",
            "Суп фо бо - 175₽", "Тортилья - 150₽"
        ],
        "Выпечка": ["Круассан с ветчиной - 90₽", "Чизкейк - 120₽", "Маффин шоколадный - 70₽", "Эклер с заварным кремом - 80₽", "Тарталетка с фруктами - 100₽"]
    },
    "Воскресенье": {
        "Напитки": ["Чай травяной - 40₽", "Кофе глясе - 100₽", "Сок гранатовый - 70₽", "Мохито безалкогольный - 90₽", "Какао с зефиром - 85₽"],
        "Блюда": ["Столовая закрыта - приходите в будние дни!"],
        "Выпечка": ["Столовая закрыта - приходите в будние дни!"]
    }
}

# Инициализация базы данных
def init_db():
    conn = sqlite3.connect("reminders.db")
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS reminders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        date TEXT NOT NULL,
        text TEXT NOT NULL,
        notified INTEGER DEFAULT 0
    )
    """)
    conn.commit()
    conn.close()

init_db()

# Функция для проверки и отправки напоминаний
async def check_reminders():
    while True:
        conn = sqlite3.connect("reminders.db")
        cursor = conn.cursor()
        
        # Находим напоминания, которые должны быть сегодня+1 день и еще не были отправлены
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        cursor.execute("SELECT * FROM reminders WHERE date = ? AND notified = 0", (tomorrow,))
        reminders = cursor.fetchall()
        
        for reminder in reminders:
            user_id = reminder[1]
            date = reminder[2]
            text = reminder[3]
            
            try:
                await bot.send_message(
                    user_id,
                    f"🔔 Напоминание за 1 день!\nДата: {date}\nСобытие: {text}"
                )
                # Помечаем как отправленное
                cursor.execute("UPDATE reminders SET notified = 1 WHERE id = ?", (reminder[0],))
                conn.commit()
            except Exception as e:
                logger.error(f"Ошибка при отправке напоминания: {e}")
        
        conn.close()
        await asyncio.sleep(3600)  # Проверяем каждые 1 час

# Обработчики команд
@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer("Привет! Я бот-помощник УдГУ. Чем могу помочь?", reply_markup=main_menu)

@dp.message(F.text == "📚 Факультеты и направления")
async def faculties_menu(message: types.Message):
    categories_markup = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="💻 IT и программирование")],
            [KeyboardButton(text="🧮 Математика и физика")],
            [KeyboardButton(text="🎨 Искусство и дизайн")],
            [KeyboardButton(text="📊 Бизнес и экономика")],
            [KeyboardButton(text="🌍 Гуманитарные науки")],
            [KeyboardButton(text="🔬 Естественные науки")],
            [KeyboardButton(text="⚖️ Юриспруденция")],
            [KeyboardButton(text="🏥 Медицина")],
            [KeyboardButton(text="🏛️ Назад")]
        ],
        resize_keyboard=True
    )
    await message.answer("Выберите категорию направлений:", reply_markup=categories_markup)

@dp.message(F.text == "🏛️ Назад")
async def back_to_main_from_faculties(message: types.Message):
    await message.answer("Главное меню:", reply_markup=main_menu)

@dp.message(F.text == "💻 IT и программирование")
async def it_faculties(message: types.Message):
    text = """
💻 *IT и программирование - направления подготовки:*

🔹 *Программная инженерия*
▫️ Профиль: Разработка программного обеспечения
▫️ Бюджетных мест: 25
▫️ Проходной балл: 240+
▫️ Стоимость: 120 000₽/год
▫️ Изучаемые технологии: Python, Java, C++, алгоритмы, базы данных

🔹 *Прикладная информатика*
▫️ Профиль: Информационные системы в бизнесе
▫️ Бюджетных мест: 20
▫️ Проходной балл: 230+
▫️ Стоимость: 110 000₽/год
▫️ Изучаемые технологии: SQL, 1С, ERP-системы

🔹 *Кибербезопасность*
▫️ Профиль: Защита информации
▫️ Бюджетных мест: 15
▫️ Проходной балл: 250+
▫️ Стоимость: 130 000₽/год
▫️ Изучаемые технологии: Ethical hacking, криптография

🔹 *Искусственный интеллект*
▫️ Профиль: Машинное обучение
▫️ Бюджетных мест: 10
▫️ Проходной балл: 260+
▫️ Стоимость: 140 000₽/год
▫️ Изучаемые технологии: TensorFlow, нейросети

🎓 *Карьерные перспективы:* 
- Разработчик (Junior → Senior)
- Data Scientist
- Аналитик данных
- Специалист по кибербезопасности
- Продуктовый менеджер

📚 *Основные дисциплины:*
- Алгоритмы и структуры данных
- Операционные системы
- Компьютерные сети
- Машинное обучение
- Веб-разработка
"""
    await message.answer(text, parse_mode="Markdown")

@dp.message(F.text == "🧮 Математика и физика")
async def math_faculties(message: types.Message):
    text = """
🧮 *Математика и физика - направления подготовки:*

🔹 *Фундаментальная математика*
▫️ Профиль: Алгебра и геометрия
▫️ Бюджетных мест: 30
▫️ Проходной балл: 220+
▫️ Стоимость: 90 000₽/год
▫️ Изучаемые дисциплины: Топология, теория чисел

🔹 *Прикладная математика*
▫️ Профиль: Математическое моделирование
▫️ Бюджетных мест: 25
▫️ Проходной балл: 230+
▫️ Стоимость: 100 000₽/год
▫️ Изучаемые дисциплины: Дифференциальные уравнения

🔹 *Физика*
▫️ Профиль: Теоретическая физика
▫️ Бюджетных мест: 20
▫️ Проходной балл: 210+
▫️ Стоимость: 95 000₽/год
▫️ Изучаемые дисциплины: Квантовая механика

🔹 *Астрономия*
▫️ Профиль: Астрофизика
▫️ Бюджетных мест: 10
▫️ Проходной балл: 200+
▫️ Стоимость: 85 000₽/год

🎓 *Карьерные перспективы:*
- Научный сотрудник
- Преподаватель
- Аналитик данных
- Инженер-исследователь
"""
    await message.answer(text, parse_mode="Markdown")

@dp.message(F.text == "🎨 Искусство и дизайн")
async def art_faculties(message: types.Message):
    text = """
🎨 *Искусство и дизайн - направления подготовки:*

🔹 *Графический дизайн*
▫️ Профиль: Визуальные коммуникации
▫️ Бюджетных мест: 15
▫️ Проходной балл: творческий конкурс
▫️ Стоимость: 110 000₽/год
▫️ Изучаемые программы: Photoshop, Illustrator

🔹 *Дизайн среды*
▫️ Профиль: Проектирование пространств
▫️ Бюджетных мест: 12
▫️ Проходной балл: творческий конкурс
▫️ Стоимость: 115 000₽/год
▫️ Изучаемые программы: 3ds Max, AutoCAD

🔹 *Изящные искусства*
▫️ Профиль: Живопись
▫️ Бюджетных мест: 10
▫️ Проходной балл: творческий конкурс
▫️ Стоимость: 100 000₽/год

🎓 *Карьерные перспективы:*
- Графический дизайнер
- UX/UI дизайнер
- Художник
- Архитектор
"""
    await message.answer(text, parse_mode="Markdown")

@dp.message(F.text == "📊 Бизнес и экономика")
async def business_faculties(message: types.Message):
    text = """
📊 *Бизнес и экономика - направления подготовки:*

🔹 *Экономика*
▫️ Профиль: Финансы и кредит
▫️ Бюджетных мест: 40
▫️ Проходной балл: 240+
▫️ Стоимость: 120 000₽/год
▫️ Изучаемые дисциплины: Эконометрика, бухучет

🔹 *Менеджмент*
▫️ Профиль: Управление бизнесом
▫️ Бюджетных мест: 35
▫️ Проходной балл: 230+
▫️ Стоимость: 115 000₽/год
▫️ Изучаемые дисциплины: Маркетинг, стратегический менеджмент

🔹 *Бизнес-информатика*
▫️ Профиль: IT-менеджмент
▫️ Бюджетных мест: 20
▫️ Проходной балл: 235+
▫️ Стоимость: 125 000₽/год

🎓 *Карьерные перспективы:*
- Финансовый аналитик
- Бизнес-консультант
- Предприниматель
- Менеджер проектов
"""
    await message.answer(text, parse_mode="Markdown")

@dp.message(F.text == "🌍 Гуманитарные науки")
async def humanities_faculties(message: types.Message):
    text = """
🌍 *Гуманитарные науки - направления подготовки:*

🔹 *История*
▫️ Профиль: Отечественная история
▫️ Бюджетных мест: 25
▫️ Проходной балл: 210+
▫️ Стоимость: 85 000₽/год

🔹 *Философия*
▫️ Профиль: Социальная философия
▫️ Бюджетных мест: 20
▫️ Проходной балл: 200+
▫️ Стоимость: 80 000₽/год

🔹 *Лингвистика*
▫️ Профиль: Теория языка
▫️ Бюджетных мест: 30
▫️ Проходной балл: 220+
▫️ Стоимость: 95 000₽/год

🎓 *Карьерные перспективы:*
- Преподаватель
- Переводчик
- Научный сотрудник
- Журналист
"""
    await message.answer(text, parse_mode="Markdown")

@dp.message(F.text == "🔬 Естественные науки")
async def science_faculties(message: types.Message):
    text = """
🔬 *Естественные науки - направления подготовки:*

🔹 *Биология*
▫️ Профиль: Генетика
▫️ Бюджетных мест: 25
▫️ Проходной балл: 220+
▫️ Стоимость: 90 000₽/год

🔹 *Химия*
▫️ Профиль: Органическая химия
▫️ Бюджетных мест: 20
▫️ Проходной балл: 215+
▫️ Стоимость: 95 000₽/год

🔹 *Экология*
▫️ Профиль: Природопользование
▫️ Бюджетных мест: 15
▫️ Проходной балл: 210+
▫️ Стоимость: 85 000₽/год

🎓 *Карьерные перспективы:*
- Лаборант
- Эколог
- Научный сотрудник
- Преподаватель
"""
    await message.answer(text, parse_mode="Markdown")

@dp.message(F.text == "⚖️ Юриспруденция")
async def law_faculties(message: types.Message):
    text = """
⚖️ *Юриспруденция - направления подготовки:*

🔹 *Гражданское право*
▫️ Профиль: Корпоративное право
▫️ Бюджетных мест: 30
▫️ Проходной балл: 250+
▫️ Стоимость: 130 000₽/год

🔹 *Уголовное право*
▫️ Профиль: Криминалистика
▫️ Бюджетных мест: 25
▫️ Проходной балл: 245+
▫️ Стоимость: 125 000₽/год

🔹 *Международное право*
▫️ Профиль: Дипломатия
▫️ Бюджетных мест: 20
▫️ Проходной балл: 255+
▫️ Стоимость: 140 000₽/год

🎓 *Карьерные перспективы:*
- Юрист
- Прокурор
- Судья
- Нотариус
"""
    await message.answer(text, parse_mode="Markdown")

@dp.message(F.text == "🏥 Медицина")
async def medicine_faculties(message: types.Message):
    text = """
🏥 *Медицина - направления подготовки:*

🔹 *Лечебное дело*
▫️ Профиль: Терапия
▫️ Бюджетных мест: 50
▫️ Проходной балл: 260+
▫️ Стоимость: 150 000₽/год

🔹 *Стоматология*
▫️ Профиль: Хирургическая стоматология
▫️ Бюджетных мест: 30
▫️ Проходной балл: 255+
▫️ Стоимость: 160 000₽/год

🔹 *Фармация*
▫️ Профиль: Фармацевтическая химия
▫️ Бюджетных мест: 25
▫️ Проходной балл: 240+
▫️ Стоимость: 140 000₽/год

🎓 *Карьерные перспективы:*
- Врач
- Фармацевт
- Медицинский исследователь
"""
    await message.answer(text, parse_mode="Markdown")

@dp.message(F.text.startswith("/ege "))
async def ege_calculator(message: types.Message):
    try:
        scores = list(map(int, message.text.split()[1:]))  
        total = sum(scores)
        await message.answer(f"📊 Ваши баллы: {total}\n\nСравните с проходными баллами выше ⬆️")
    except ValueError:
        await message.answer("❌ Ошибка! Введите баллы через пробел, например:\n`/ege 80 75 90`", parse_mode="Markdown")
# Добавляем обработчик для полезных ссылок
@dp.message(F.text == "🔗 Полезные ссылки")
async def useful_links(message: types.Message):
    links_text = """
🔗 *Полезные ссылки УдГУ:*

📌 [Поступление в УдГУ](https://udsu.ru/admissions) - вся информация для абитуриентов

🎓 [Обучение](https://udsu.ru/students) - ресурсы для студентов

🔬 [Наука](https://udsu.ru/news/science) - научные достижения и исследования

🌐 [Официальный сайт](https://udsu.ru) - главный портал университета

📚 [Электронная библиотека](https://library.udsu.ru) - учебные материалы

🏢 [Расписание](https://rasp.udsu.ru) - актуальное расписание занятий
"""
    await message.answer(links_text, parse_mode="Markdown", disable_web_page_preview=True)
# Расписание
@dp.message(F.text == "🗓 Расписание")
async def schedule_info(message: types.Message):
    user_id = message.from_user.id
    if user_id in user_schedules:
        file_id = user_schedules[user_id]
        await message.answer_photo(file_id, caption="📅 Ваше сохраненное расписание:")
    else:
        await message.answer("📅 Отправьте фото, PDF или ссылку на расписание.")

@dp.message(F.photo | F.document)
async def save_schedule(message: types.Message):
    user_id = message.from_user.id
    if message.photo:
        file_id = message.photo[-1].file_id
        user_schedules[user_id] = file_id
        await message.answer("✅ Фото расписания сохранено! Теперь вы можете просмотреть его, нажав кнопку '🗓 Расписание'.")
    elif message.document:
        file_id = message.document.file_id
        user_schedules[user_id] = file_id
        await message.answer("✅ PDF расписания сохранен! Теперь вы можете просмотреть его, нажав кнопку '🗓 Расписание'.")
    else:
        await message.answer("❌ Ошибка! Отправьте фото или PDF.")
        # Добавляем в функцию init_db создание таблицы для расписаний
def init_db():
    conn = sqlite3.connect("reminders.db")
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS reminders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        date TEXT NOT NULL,
        text TEXT NOT NULL,
        notified INTEGER DEFAULT 0
    )
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS schedules (
        user_id INTEGER PRIMARY KEY,
        file_id TEXT NOT NULL,
        file_type TEXT NOT NULL
    )
    """)
    conn.commit()
    conn.close()

# Обновляем обработчик расписания
@dp.message(F.text == "🗓 Расписание")
async def schedule_info(message: types.Message):
    conn = sqlite3.connect("reminders.db")
    cursor = conn.cursor()
    cursor.execute("SELECT file_id, file_type FROM schedules WHERE user_id = ?", (message.from_user.id,))
    schedule = cursor.fetchone()
    conn.close()
    
    if schedule:
        file_id, file_type = schedule
        if file_type == "photo":
            await message.answer_photo(file_id, caption="📅 Ваше сохраненное расписание:")
        elif file_type == "document":
            await message.answer_document(file_id, caption="📅 Ваше сохраненное расписание:")
    else:
        await message.answer("📅 Отправьте фото, PDF или ссылку на расписание.")

# Обновляем обработчик сохранения расписания
@dp.message(F.photo | F.document)
async def save_schedule(message: types.Message):
    user_id = message.from_user.id
    conn = sqlite3.connect("reminders.db")
    cursor = conn.cursor()
    
    if message.photo:
        file_id = message.photo[-1].file_id
        file_type = "photo"
        cursor.execute(
            "INSERT OR REPLACE INTO schedules (user_id, file_id, file_type) VALUES (?, ?, ?)",
            (user_id, file_id, file_type)
        )
    elif message.document:
        file_id = message.document.file_id
        file_type = "document"
        cursor.execute(
            "INSERT OR REPLACE INTO schedules (user_id, file_id, file_type) VALUES (?, ?, ?)",
            (user_id, file_id, file_type)
        )
    else:
        await message.answer("❌ Ошибка! Отправьте фото или PDF.")
        conn.close()
        return
    
    conn.commit()
    conn.close()
    await message.answer("✅ Расписание сохранено! Теперь вы можете просмотреть его, нажав кнопку '🗓 Расписание'.")

# Новости с сайта УдГУ
@dp.message(F.text == "📢 Новости")
async def get_news(message: types.Message):
    try:
        url = "https://udsu.ru/news"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        
        # Получаем HTML-страницу
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Проверяем на ошибки HTTP
        
        # Парсим HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Находим все новостные блоки - уточненный селектор
        news_items = soup.select('.news-list .news-item')[:5]  # Берем 5 последних новостей
        
        if not news_items:
            await message.answer("❌ На сайте не найдено новостей. Попробуйте позже.")
            return
        
        news_text = "📰 *Последние новости УдГУ:*\n\n"
        
        for item in news_items:
            # Извлекаем заголовок
            title_element = item.select_one('.news-item__title a')
            if not title_element:
                continue
                
            title = title_element.get_text(strip=True)
            link = title_element['href']
            
            # Извлекаем дату
            date_element = item.select_one('.news-item__date')
            date = date_element.get_text(strip=True) if date_element else "Дата не указана"
            
            # Формируем полную ссылку
            full_link = f"https://udsu.ru{link}" if link.startswith('/') else link
            
            news_text += f"📅 *{date}*\n🔹 [{title}]({full_link})\n\n"
        
        await message.answer(news_text, 
                           parse_mode="Markdown", 
                           disable_web_page_preview=True)
        
    except requests.RequestException as e:
        logger.error(f"Ошибка при запросе новостей: {e}")
        await message.answer("❌ Не удалось получить новости с сайта. Попробуйте позже.")
    except Exception as e:
        logger.error(f"Неожиданная ошибка при парсинге новостей: {e}")
        await message.answer("❌ Произошла ошибка при обработке новостей. Попробуйте позже.")

# Меню столовой
@dp.message(F.text == "🍽 Меню столовой")
async def get_menu(message: types.Message):
    day = datetime.now().strftime("%A")
    if day == "Sunday":
        day = "Воскресенье"
    
    day_translation = {
        "Monday": "Понедельник",
        "Tuesday": "Вторник",
        "Wednesday": "Среда",
        "Thursday": "Четверг",
        "Friday": "Пятница",
        "Saturday": "Суббота",
        "Sunday": "Воскресенье"
    }
    
    current_day = day_translation.get(day, day)
    day_menu = menu.get(current_day, {})
    
    if not day_menu:
        await message.answer("❌ Меню на сегодня не найдено.")
        return
    
    text = f"🍽 *Меню столовой на {current_day}:*\n\n"
    
    text += "🥤 *Напитки:*\n"
    for item in day_menu.get("Напитки", []):
        text += f"• {item}\n"
    
    text += "\n🍲 *Основные блюда:*\n"
    for item in day_menu.get("Блюда", []):
        text += f"• {item}\n"
    
    text += "\n🥐 *Выпечка:*\n"
    for item in day_menu.get("Выпечка", []):
        text += f"• {item}\n"
    
    await message.answer(text, parse_mode="Markdown")

# Напоминания
@dp.message(F.text == "🔔 Напоминания")
async def reminders_menu(message: types.Message):
    markup = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Добавить напоминание")],
            [KeyboardButton(text="Мои напоминания")],
            [KeyboardButton(text="Назад")]
        ],
        resize_keyboard=True
    )
    await message.answer("Выберите действие:", reply_markup=markup)

@dp.message(F.text == "Добавить напоминание")
async def add_reminder_prompt(message: types.Message):
    await message.answer("📅 Введите дату и текст напоминания в формате:\n`ГГГГ-ММ-ДД Текст напоминания`\n\nПример:\n`2025-05-20 Сдать курсовую работу`", parse_mode="Markdown")

@dp.message(F.text == "Мои напоминания")
async def show_reminders(message: types.Message):
    conn = sqlite3.connect("reminders.db")
    cursor = conn.cursor()
    cursor.execute("SELECT date, text FROM reminders WHERE user_id = ? ORDER BY date", (message.from_user.id,))
    reminders = cursor.fetchall()
    conn.close()
    
    if not reminders:
        await message.answer("У вас нет активных напоминаний.")
        return
    
    text = "📅 *Ваши напоминания:*\n\n"
    for i, (date, reminder_text) in enumerate(reminders, 1):
        text += f"{i}. *{date}* - {reminder_text}\n"
    
    await message.answer(text, parse_mode="Markdown")

@dp.message(F.text == "Назад")
async def back_to_main(message: types.Message):
    await message.answer("Главное меню:", reply_markup=main_menu)

@dp.message(lambda message: len(message.text.split()) >= 2 and "-" in message.text)
async def add_reminder(message: types.Message):
    try:
        parts = message.text.split(" ", 1)
        date_str = parts[0]
        reminder_text = parts[1]
        
        # Проверка формата даты
        datetime.strptime(date_str, "%Y-%m-%d")
        
        conn = sqlite3.connect("reminders.db")
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO reminders (user_id, date, text) VALUES (?, ?, ?)",
            (message.from_user.id, date_str, reminder_text)
        )
        conn.commit()
        conn.close()
        
        await message.answer(f"✅ Напоминание добавлено:\nДата: {date_str}\nТекст: {reminder_text}")
    except ValueError as e:
        await message.answer(f"❌ Ошибка! Неверный формат даты. Используйте:\n`ГГГГ-ММ-ДД Текст напоминания`\n\nПример:\n`2025-05-20 Сдать курсовую`", parse_mode="Markdown")
    except Exception as e:
        logger.error(f"Ошибка при добавлении напоминания: {e}")
        await message.answer("❌ Произошла ошибка при добавлении напоминания.")

# Запуск бота
async def main():
    logger.info("Бот запущен 🚀")
    # Запускаем проверку напоминаний в фоне
    asyncio.create_task(check_reminders())
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())