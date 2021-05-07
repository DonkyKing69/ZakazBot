import logging
from socket import timeout
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import reply_keyboard
import AvitoParser
import asyncio
import psycopg2
from psycopg2 import Error
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import settings
import bot_buttons
import log_handler

API_TOKEN = '1734443248:AAGIjGxNmp3SpVHpENfBuwlOciBi6jTHYas'

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)


@dp.message_handler(commands=['start', 'help'])
async def send_welcome(message: types.Message):
    await bot.send_message(message.from_user.id, f'Добро пожаловать, {message.from_user.username}!', reply_markup=bot_buttons.start_btn)

@dp.callback_query_handler(lambda callback: callback.data == 'today')
async def process_choice_period(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(callback_query.from_user.id, 'Вот ссылки за сегодня:', reply_markup=bot_buttons.period(1))

@dp.callback_query_handler(lambda callback: callback.data == '3days')
async def process_choice_period(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(callback_query.from_user.id, 'Вот ссылки за последние 3 дня:', reply_markup=bot_buttons.period(3))

@dp.callback_query_handler(lambda callback: callback.data == 'week')
async def process_choice_period(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(callback_query.from_user.id, 'Вот ссылки за неделью:', reply_markup=bot_buttons.period(7))

@dp.callback_query_handler(lambda callback: callback.data.split('[|]')[0] == 'link')
async def process_choice_period(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)

    try:
        alias = eval(callback_query.data.split('[|]')[1])[0]
        try:
            connection = psycopg2.connect(user=settings.db_data["user"],
                password=settings.db_data["password"],
                host=settings.db_data["host"],
                port=settings.db_data["port"],
                database=settings.db_data["database"])
            connection.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            cursor = connection.cursor()

            select_query = "SELECT title FROM parsing_datas WHERE alias=%s;"
            cursor.execute(select_query, [alias])
            title = cursor.fetchall()
            
            select_query = "SELECT * FROM user_datas WHERE alias=%s;"
            cursor.execute(select_query, [alias])
            data = cursor.fetchall()
        except Exception as error:
            log_handler.write_log([error, "Ошибка при попытке получить данные из базы, Блок process_choice_period()"], 'bot.py')
        msg = f"Данные ползователей со страницы {title[0][0]}\nФ.И.О: {data[0][2]}\nemail: {data[0][3]}\nНомер телефона: {data[0][4]}\nАдресс: {data[0][5]}"
    except Exception as error:
        msg = "Форма на этой странице ни разу не был заполнен."
    await bot.send_message(callback_query.from_user.id, msg)

@dp.message_handler()
async def parse(message: types.Message):
    if 'Посмотреть данные' not in message.text:
        if 'avito.ru' in message.text:
            try:
                url = message.text
                answer = AvitoParser.run(url)
                alias = answer.split('/')[-1]
                user = message.from_user.id

                try:
                    connection = psycopg2.connect(user=settings.db_data["user"],
                                                password=settings.db_data["password"],
                                                host=settings.db_data["host"],
                                                port=settings.db_data["port"],
                                                database=settings.db_data["database"])
                    connection.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
                    cursor = connection.cursor()
                    insert_query = """ INSERT INTO telegram_datas (alias, uname, created_date) VALUES (%s, %s, CURRENT_DATE)"""
                    cursor.execute(insert_query, [alias, user])
                    connection.commit()
                except Exception as error:
                    log_handler.write_log([error, "Ошибка при попытке записать данные в таблицу telegram_datas, Блок parse()"], 'bot.py')
            except Exception as error:
                log_handler.write_log([error, "Ошибка, не существущая страница, Блок parse()"], 'bot.py')
                answer = "Ваша ссылка на авито не валидна!"
        else:
            answer = 'Не могу найти ссылку на авито...'
            print(AvitoParser.run('http://httpbin.org/ip'))
        await message.reply(answer)
    else:
        await bot.send_message(message.from_user.id,'Выберите период' , reply_markup=bot_buttons.choice_period)

async def send_form_data(wait_for):
    try:
        connection = psycopg2.connect(user=settings.db_data["user"],
                                    password=settings.db_data["password"],
                                    host=settings.db_data["host"],
                                    port=settings.db_data["port"],
                                    database=settings.db_data["database"])
        connection.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = connection.cursor()
        while True:
            del_list = []
            await asyncio.sleep(wait_for)
            cursor.execute('SELECT * FROM messages')
            messages_on_order = cursor.fetchall()
            if messages_on_order:
                for msg in messages_on_order:
                    formated_message = msg[1].split('\n')
                    alias = formated_message[0].strip()
                    full_name = formated_message[1].strip()
                    email = formated_message[2].strip()
                    phone = formated_message[3].strip()
                    address = formated_message[4].strip()
                    cursor.execute('SELECT uname FROM telegram_datas where (alias) = (%s)', [alias])
                    recipient_id = cursor.fetchone()
                    recipient_id = recipient_id[0]
                    await bot.send_message(recipient_id, f"Имя пользователья: {full_name}\nemail: {email}\nНомер телефона: {phone}\nАдресс: {address}\nСсылка: {settings.domain['domain']}/order/{alias}")
                    del_list.append(msg[0])
                    messages_on_order.remove(msg)
            for del_id in del_list:
                delete_query = """DELETE FROM messages WHERE id = %s"""
                cursor.execute(delete_query, [del_id])
            
    except Exception as error:
        log_handler.write_log([error, "Ошибка при попытке получить сообщения из messages, Блок send_form_data()"], 'bot.py')


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.create_task(send_form_data(10))
    executor.start_polling(dp, skip_updates=True)
