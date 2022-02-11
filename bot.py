from glob import glob
import users_helper
from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from tg_token import TOKEN
from keyboard import *
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher.filters import BoundFilter
from aiogram.dispatcher.filters.builtin import Text
from aiogram.types import InputFile
from math import ceil
from callbacks import friday_callback

class IsData(BoundFilter):
  async def check(self, call: types.CallbackQuery):
    return call.message.text.startswith('date_')


storage=MemoryStorage()
API_TOKEN = TOKEN
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot, storage=storage)

global final_user_login
global final_user_password

class GetUserData(StatesGroup):
  usr_login = State()
  usr_password = State()


class GetVacationData(StatesGroup):
  start_vacation_data = State()
  end_vacation_data = State()


@dp.message_handler(commands='start')
async def greeting(message: types.Message):
  await message.answer('Приветствую!', reply_markup=start_kb)
  global final_user_tgid
  final_user_tgid = message.from_user.id


@dp.message_handler(text='Логин 🔑')
async def get_login(message: types.Message):
  await GetUserData.usr_login.set()
  await message.answer('Введите ваш логин...')


@dp.message_handler(state=GetUserData.usr_login)
async def process_get_login(message: types.Message, state: FSMContext):
  async with state.proxy() as data:
    data['usr_login'] = message.text  
  global final_user_login
  final_user_login = data['usr_login']
  await GetUserData.usr_password.set()
  await message.answer('Введите ваш пароль...')


@dp.message_handler(state=GetUserData.usr_password)
async def process_get_password(message: types.Message, state: FSMContext):
  async with state.proxy() as data:
    data['usr_password'] = message.text
  global final_user_password
  final_user_password = data['usr_password']
  user_data = users_helper.login(final_user_login, final_user_password)
  global uber_login
  uber_login = user_data
  if(user_data):
    msg = users_helper.get_formatted_message(uber_login)
    await message.answer(msg, parse_mode='markdown', reply_markup=control_kb)
    await state.finish()
  else:
    await state.finish()
    await bot.send_message(final_user_tgid, 'Произошла ошибка')


@dp.message_handler(text='Установить дату отпуска ✈️')
async def vacation_menu(message: types.Message):
  user_data = users_helper.login(final_user_login, final_user_password)
  try:
    if(len(users_helper.is_vocation_booked(user_data)) <= 1):
      try:
        aboba_kb = InlineKeyboardMarkup(row_width=3)
        for item in users_helper.get_all_fridays(user_data):
          button = InlineKeyboardButton(
            text=item,
            callback_data=friday_callback.new(friday_date=item)
          )
          aboba_kb.insert(button)
        await message.answer('Доступные пятницы по датам:', reply_markup=aboba_kb)
      except:
        await message.answer('Прозошла ошибка с выводом пятниц, обратитесь в тех. поддержку.')
    else:
      await message.answer('Вы уже зарезервировали отпуск :(')
  except:
    await message.answer('Прозошла ошибка, обратитесь в тех. поддержку или администратору напрямую.')
  

@dp.callback_query_handler(friday_callback.filter())
async def get_vacation_cb(call: types.CallbackQuery, callback_data: dict):
  pyatnica = callback_data.get('friday_date')
  user_data = users_helper.login(final_user_login, final_user_password)
  users_helper.update_start_vocation_date(pyatnica, user_data)
  await call.message.answer(f'Дата начала отпуска установлена на {pyatnica}!', reply_markup=control_kb)


@dp.message_handler(text='Справка ℹ️')
async def get_user_data(message: types.Message):
  try:
    user_data = users_helper.login(final_user_login, final_user_password)
    msg = users_helper.get_formatted_message(user_data)
    await message.answer(msg, parse_mode='markdown', reply_markup=control_kb)
  except:
    await message.answer('Тех. неполадки, пропишите команду /start')




@dp.message_handler(text='Мои документы 📚')
async def get_user_documents(message: types.Message):
  try:
    docs_kb = InlineKeyboardMarkup()
    urls = users_helper.get_all_urls(uber_login)
    for url in urls:
      for url_part in url:
        url_title = url_part
        url_value = url[url_title]
        button = InlineKeyboardButton(
        text=url_title,
        url=url_value
      )
      docs_kb.add(button)
    await message.answer('Ваши документы:', reply_markup=docs_kb)
  except:
    await message.answer('Тех. неполадки, пропишите команду /start')


@dp.message_handler()
async def unknown_info(message: types.Message):
    await message.answer("Что-то я вас не понял 0_o", reply_markup=control_kb)

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)