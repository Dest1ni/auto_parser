import asyncio
import logging
from router import *
from aiogram import Bot
from aiogram import Dispatcher
from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram import types
from aiogram import F
from aiogram import *
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
import sqlite3
from models import *

BOT_TOKEN = TOKEN
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

class Stop(StatesGroup):
    start = State()
    finish = State()

class Route(StatesGroup):
    current = State()
    finish = State()
    search_state = State()


@dp.message(CommandStart())
async def commandstart(message:Message):
    kb = [
        [types.KeyboardButton(text="Найди меня")],
        [types.KeyboardButton(text="Отмена")],
    ]
    keyboard = types.ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True,
        input_field_placeholder="Давайте поищем вам маршрут :)"
        )
    return await message.answer(f"""Привет {message.from_user.first_name},это бот который поможет тебе не потеряться, просто нажми на кнопку ниже. \nP.S Бот ещё не протестирован я не рекомендую использовать его в экстренных ситуациях, если вы нашли не состыковки,баги и прочее уведомите меня (@dest1ni18)!\nБот очень привередлив к написанию остановки, если у вас не получается найти остановку попробуйте ключевые слова, например: Улица, Предприятие. Или попробуйте ввести часть остановки, например если ищите 8-ое марта, введите просто 8.""",reply_markup=keyboard)

@dp.message(F.text.lower() == "отмена")
async def commandcancel(message:Message):
    kb = [
        [types.KeyboardButton(text="Найди меня")],
        [types.KeyboardButton(text="Отмена")],
    ]
    keyboard = types.ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True,
        input_field_placeholder="Давайте поищем вам маршрут :)"
        )
    return await message.answer("Отменил всё что ты натворил :)",reply_markup=keyboard)

@dp.message(F.text.lower() == "найди меня")
async def find_me(message: types.Message, state: FSMContext):
    await state.set_state(Stop.start)
    await message.answer("Введите вашу остановку, например: Коминтерн или 60 лет или Солнечная")
    
@dp.message(Stop.start)
async def find_start(message: Message,state: FSMContext):
    await state.update_data(name=message.text)
    station_for_find = await state.get_data()
    stations = get_similar_station(station_for_find['name'])
    kb = [ 
        [types.KeyboardButton(text = x)] for x in stations
        
    ]
    kb.append([types.KeyboardButton(text="Отмена")])
    print(kb)
    keyboard = types.ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True,
        input_field_placeholder="Давайте поищем вам маршрут :)"
        )
    await message.answer("Выберите подходящую текущую остановку из списка ниже",reply_markup=keyboard)
    await state.set_state(Route.current)


@dp.message(Route.current)
async def set_current(message:types.Message,state:FSMContext):
    await state.update_data(current=message.text)
    kb = [
        [types.KeyboardButton(text="Отмена")],
    ]
    keyboard = types.ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True,
        input_field_placeholder="Давайте поищем вам маршрут :)"
        )
    await message.answer("Введите вашу желаемую остановку, например: Коминтерн или 60 лет или Солнечная",reply_markup=keyboard)
    await state.set_state(Stop.finish)

@dp.message(Stop.finish)
async def find_finish(message: types.Message,state: FSMContext):
    await state.update_data(finish = message.text)
    station_for_find = await state.get_data()
    stations = get_similar_station(station_for_find['finish'])
    kb = [ 
        [types.KeyboardButton(text = x)] for x in stations
        
    ]
    kb.append([types.KeyboardButton(text="Отмена")])
    keyboard = types.ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True,
        input_field_placeholder="Давайте поищем вам маршрут :)"
        )
    await message.answer("Выберите подходящую желаемую остановку из списка ниже",reply_markup=keyboard)
    await state.set_state(Route.finish)



async def search_route(message: types.Message,state: FSMContext):
    data = await state.get_data()
    answer = get_closest_routes(current=data['current'],finish=data['finish'])
    kb = [
            [types.KeyboardButton(text="Найди меня")],
            [types.KeyboardButton(text="Отмена")],
        ]
    keyboard = types.ReplyKeyboardMarkup(
            keyboard=kb,
            resize_keyboard=True,
            input_field_placeholder="Давайте поищем вам маршрут :)"
        )
    if answer:
        for key,value in answer.items():
            await message.answer(
                f"Маршрут: {key}\nБудет на вашей остановке в {value}"
            )
        await message.answer("Это немного, но это честная работа."
                ,reply_markup=keyboard
            )
    else:
        
        await message.answer("Вот это тебя занесло !\nМы не смогли найти подходящий вам маршрут, возможно следующее:\n 1. Вы ошиблись при вводе остановки. !\n2. Ошибка на нашей стороне :(\nP.S. Поиск проходит только по городсикм автобусам !",reply_markup=keyboard)

@dp.message(Route.finish)
async def set_current(message:types.Message,state:FSMContext):
    await state.update_data(finish=message.text)
    await message.answer("Сейчас подберём вам маршрут...")
    await search_route(message=message,state=state)
    
async def main() -> None:
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())

