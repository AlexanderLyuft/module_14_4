                # Домашнее задание по теме "План написания админ панели"


import os
import sqlite3
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.utils import executor
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from dotenv import load_dotenv
from crud_functions import initiate_db, get_all_products, add_product

# Загрузка переменных окружения
load_dotenv()
API_TOKEN = os.getenv('API_TOKEN')

# Инициализация бота и диспетчера
bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# Функция для проверки существования продукта в базе данных
def product_exists(title):
    conn = sqlite3.connect('products.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM Products WHERE title = ?', (title,))
    exists = cursor.fetchone() is not None
    conn.close()
    return exists

# Инициализация базы данных и добавление продуктов
initiate_db()

# Список продуктов для добавления
products_to_add = [
    ('Протеиновый батончик', 'Утоляет голод после тренировки, дает энергию', 100),
    ('ВСАА', 'Способствует восстановлению мышечной ткани', 200),
    ('Протеиновый коктейль', 'Поддерживает иммунитет, создает и восстанавливает клетки и ткани', 300),
    ('Гейнер', 'Помогает увеличить мышечный объем и набрать вес', 400)
]

# Добавляем продукты, если их еще нет в базе данных
for title, description, price in products_to_add:
    if not product_exists(title):
        add_product(title, description, price)

# Определение состояний для расчета калорий
class UserState(StatesGroup):
    age = State()
    growth = State()
    weight = State()

# Создание клавиатуры
keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
button_calculate = KeyboardButton('Рассчитать')
button_info = KeyboardButton('Информация')
button_buy = KeyboardButton('Купить')  # Кнопка "Купить"
keyboard.add(button_calculate, button_info, button_buy)

# Создание Inline-клавиатуры
inline_keyboard = InlineKeyboardMarkup(row_width=2)
button_calories = InlineKeyboardButton('Рассчитать норму калорий', callback_data='calories')
button_formulas = InlineKeyboardButton('Формулы расчёта', callback_data='formulas')
inline_keyboard.add(button_calories, button_formulas)

@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    await message.answer("Привет! Я бот, помогающий твоему здоровью.", reply_markup=keyboard)

@dp.message_handler(text='Рассчитать')
async def main_menu(message: types.Message):
    await message.answer('Выберите опцию:', reply_markup=inline_keyboard)

@dp.message_handler(text='Купить')
async def get_buying_list(message: types.Message):
    products = get_all_products()  # Получаем продукты из базы данных
    inline_buy_keyboard = InlineKeyboardMarkup(row_width=2)  # Создаем клавиатуру для покупки

    for product in products:
        id, title, description, price = product
        await message.answer(f'Название: {title} | Описание: {description} | Цена: {price}')

        # Формируем путь к файлу изображения
        image_path = f'C://Users//alexa//PycharmProjects//Module_14_4/{id}.jpg'

        # Проверяем, существует ли файл перед отправкой
        if os.path.exists(image_path):
            await bot.send_photo(message.chat.id, photo=open(image_path, 'rb'))
        else:
            await message.answer(f'Изображение для {title} отсутствует.')

        # Добавляем кнопку для покупки
        button_buy_product = InlineKeyboardButton(title, callback_data=f'buy_{id}')
        inline_buy_keyboard.add(button_buy_product)

    await message.answer("Выберите продукт для покупки:", reply_markup=inline_buy_keyboard)

@dp.callback_query_handler(lambda c: c.data.startswith('buy_'))
async def process_buy(callback_query: types.CallbackQuery):
    product_id = callback_query.data.split('_')[1]
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(callback_query.from_user.id, "Вы успешно приобрели продукт!")

@dp.callback_query_handler(lambda c: c.data == 'calories')
async def calculate_calories(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(callback_query.from_user.id, "Введите ваш возраст:")
    await UserState.age.set()

@dp.message_handler(state=UserState.age)
async def process_age(message: types.Message, state: FSMContext):
    await state.update_data(age=int(message.text))
    await message.answer("Введите ваш рост (в см):")
    await UserState.growth.set()

@dp.message_handler(state=UserState.growth)
async def process_growth(message: types.Message, state: FSMContext):
    await state.update_data(growth=int(message.text))
    await message.answer("Введите ваш вес (в кг):")
    await UserState.weight.set()

@dp.message_handler(state=UserState.weight)
async def process_weight(message: types.Message, state: FSMContext):
    await state.update_data(weight=int(message.text))
    data = await state.get_data()

    age = data['age']
    growth = data['growth']
    weight = data['weight']

    # Пример расчета калорий по формуле Mifflin-St Jeor
    bmr = 10 * weight + 6.25 * growth - 5 * age + 5  # Формула для мужчин
    await message.answer(f'Ваша норма калорий (BMR) составляет: {bmr} ккал.')

    await state.finish()  # Завершаем состояние

@dp.callback_query_handler(lambda c: c.data == 'formulas')
async def show_formulas(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(callback_query.from_user.id, "Здесь будет информация о формулах.")

@dp.message_handler(lambda message: message.text != '/start')
async def other_messages(message: types.Message):
    await message.reply("Введите команду /start, чтобы начать.")

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)






