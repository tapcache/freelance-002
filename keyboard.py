from aiogram.types import ReplyKeyboardRemove, \
    ReplyKeyboardMarkup, KeyboardButton, \
    InlineKeyboardMarkup, InlineKeyboardButton


""" Reply Keyboard Buttons"""
login_btn = KeyboardButton('Логин 🔑')
get_data_btn = KeyboardButton(text='Справка ℹ️')
get_documents = KeyboardButton(text='Мои документы 📚')
vacation_btn = KeyboardButton(text='Установить дату отпуска ✈️')

""" Reply Keyboards Markups """
start_kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True).row(login_btn)
control_kb = ReplyKeyboardMarkup(resize_keyboard=True).row(get_data_btn).row(get_documents).row(vacation_btn)