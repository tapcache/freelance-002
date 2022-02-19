from webbrowser import get
import users_helper
import qdb
from aiogram import Bot, Dispatcher, executor, types
from tg_token import TOKEN
from keyboard import *
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from math import ceil
from callbacks import friday_callback
from aiogram.contrib.fsm_storage.memory import MemoryStorage

storage=MemoryStorage()
API_TOKEN = TOKEN
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot, storage=storage)


class GetUserData(StatesGroup):
  usr_login = State()
  usr_password = State()


class GetVacationData(StatesGroup):
  start_vacation_data = State()
  end_vacation_data = State()


@dp.message_handler(commands='start')
async def greeting(message: types.Message):
  await message.answer('Приветствую!', reply_markup=start_kb)


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
  qdb.save(message.from_user.id, user_data)
  if(user_data):
    msg = users_helper.get_formatted_message(user_data)
    await message.answer(msg, reply_markup=control_kb)
    print(qdb.get(message.from_user.id))
    await state.finish()
  else:
    await state.finish()
    await bot.send_message(message.from_user.id, 'Произошла ошибка, проверьте данные для авторизации.')


@dp.message_handler(text='Установить дату отпуска ✈️')
async def vacation_menu(message: types.Message):
  _user_data = qdb.get(message.from_user.id)
  print(f"login({_user_data['LOGIN']},{_user_data['PASSWORD']})")
  user_data = users_helper.login(_user_data["LOGIN"], _user_data["PASSWORD"])
  print(f"user_data = {user_data}")
  qdb.save(message.from_user.id, user_data)
  print(user_data)
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
      except Exception as ex:
        print(ex)
        await message.answer('Прозошла ошибка, обратитесь в тех. поддержку или администратору напрямую.')
    else:
      await message.answer('Вы уже зарезервировали отпуск :(')
  except Exception as ex:
    print(ex)
    await message.answer('Прозошла ошибка, обратитесь в тех. поддержку или администратору напрямую.')
  

@dp.callback_query_handler(friday_callback.filter())
async def get_vacation_cb(call: types.CallbackQuery, callback_data: dict):
  try:
    pyatnica = callback_data.get('friday_date')
    users_helper.REFRESH_TABLE_DUMP()
    _user_data = qdb.get(call.from_user.id)
    print(f"login({_user_data['LOGIN']},{_user_data['PASSWORD']})")
    user_data = users_helper.login(_user_data["LOGIN"], _user_data["PASSWORD"])
    print(f"user_data = {user_data}")
    qdb.save(call.from_user.id, user_data)
    print(f"all users: {qdb.users}")
    print(f"qdb getting : {qdb.get(call.from_user.id)}")
    users_helper.update_start_vocation_date(pyatnica, qdb.get(call.from_user.id))
    await call.message.answer(f'Отправлен запрос на установку даты отпуска на {pyatnica}!', reply_markup=control_kb)

  except Exception as ex:
    print(ex)
    await call.message.answer('Прозошла ошибка, обратитесь в тех. поддержку или администратору напрямую.')


@dp.message_handler(text='Справка ℹ️')
async def get_user_data(message: types.Message):
  try:
    _user_data = qdb.get(message.from_user.id)
    user_data = users_helper.login(_user_data["LOGIN"], _user_data["PASSWORD"])
    print(f"user_data = {user_data}")
    qdb.save(message.from_user.id, user_data)
    msg = users_helper.get_formatted_message(user_data)
    await message.answer(msg, reply_markup=control_kb)
  except Exception as ex:
    print(ex)
    await message.answer('Прозошла ошибка, обратитесь в тех. поддержку или администратору напрямую.')


@dp.message_handler(text='Мои документы 📚')
async def get_user_documents(message: types.Message):
  try:
    document_kb = InlineKeyboardMarkup()
    document_btn = InlineKeyboardButton(
      text='Ваши документы', 
      url = users_helper.get_folder_url(qdb.get(message.from_user.id))
      )
    document_kb.add(document_btn)
    await message.answer('Результат:', reply_markup=document_kb)
  except Exception as err:
    print(err)
    await message.answer('Прозошла ошибка, обратитесь в тех. поддержку или администратору напрямую.')


@dp.message_handler()
async def unknown_info(message: types.Message):
    await message.answer("Что-то я вас не понял 0_o")

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)