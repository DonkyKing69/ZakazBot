import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import settings
import log_handler
from aiogram.types import ReplyKeyboardRemove, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

start_btn = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
start_btn.add(KeyboardButton('Посмотреть данные'))

choice_today = InlineKeyboardButton('За сегодня', callback_data='today')
choice_last_three_days = InlineKeyboardButton('За 3 дня', callback_data='3days')
choice_last_week = InlineKeyboardButton('За неделью', callback_data='week')
choice_period = InlineKeyboardMarkup().add(choice_today, choice_last_three_days, choice_last_week)


def period(period_days_count):
    try:
        connection = psycopg2.connect(user=settings.db_data["user"],
            password=settings.db_data["password"],
            host=settings.db_data["host"],
            port=settings.db_data["port"],
            database=settings.db_data["database"])
        connection.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = connection.cursor()
        select_query = f"SELECT alias FROM telegram_datas WHERE created_date > (CURRENT_DATE - INTERVAL '{period_days_count} day');"
        cursor.execute(select_query)
        res = cursor.fetchall()

        try:
            btn_group = InlineKeyboardMarkup()
            for alias in res:
                select_query = "SELECT title FROM parsing_datas WHERE alias=%s;"
                cursor.execute(select_query, [alias])
                title = cursor.fetchall()
                
                btn_group.add(InlineKeyboardButton(f'{title[0][0]} [{str(alias[0])[11:]}]', callback_data=f'link[|]{alias}'))
            return btn_group
        except Exception as error:
            log_handler.write_log([error, "Ошибка при попытке title"], 'bot_buttons.py')
    except Exception as error:
        log_handler.write_log([error, "Ошибка при попытке создать список кнопок"], 'bot_buttons.py')