# REQUIREMENTS
# TODO установка нужных библиотек pip install -r requirements.txt
import requests
from bs4 import BeautifulSoup
import psycopg2, datetime, random
from psycopg2 import Error
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from settings import *


headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.186 Safari/537.36'}
domain = domain['domain']

def getHtml(url):
    # return requests.get(url, headers=headers, proxies=proxies).text   # TODO Если нужно использовать прокси
    return requests.get(url, headers=headers).text

def parse(html):
    soup = BeautifulSoup(html, 'lxml')
    content = soup.find("div", class_="item-view-content")
    content_l = content.find('div', class_="item-view-content-left")
    content_r = content.find('div', class_="item-view-content-right")
    title = content_l.find("div", class_="item-view-title-info").find("h1", class_="title-info-title").text.strip()
    seller_name = content_r.find("div", class_="seller-info").find("div", class_="seller-info-value").find("a").text.strip()
    gallery = content_l.find("div", class_="gallery").find("div", class_="gallery-imgs-wrapper").find("div", class_="gallery-img-wrapper")
    img_url = gallery.find("div", class_="gallery-img-frame").get("data-url")

    return title, seller_name, img_url

def run(url):
    html = getHtml(url)
    title, seller, img_url = parse(html)
    alias = datetime.datetime.now().strftime('%Y%m%d%H%m%S') + random.choice(['0', '1', '2', '3', '4', '5', '6', '7', '8', '9'])
    try:
        # Подключение к существующей базе данных
        connection = psycopg2.connect(user=db_data["user"],
                                    password=db_data["password"],
                                    host=db_data["host"],
                                    port=db_data["port"],
                                    database=db_data["database"])
        connection.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        # Курсор для выполнения операций с базой данных
        cursor = connection.cursor()

        # Выполнение SQL-запроса для вставки данных в таблицу
        insert_query = """ INSERT INTO parsing_datas (title, alias, seller, img) VALUES (%s, %s, %s, %s)"""
        cursor.execute(insert_query, [title, alias, seller, img_url])
        connection.commit()
        
    except (Exception, Error) as error:
        print("Ошибка при работе с PostgreSQL", error)
    finally:
        if connection:
            cursor.close()
            connection.close()
    return f'{domain}/order/{alias}'

if __name__ == "__main__":
    run('https://www.avito.ru/yoshkar-ola/doma_dachi_kottedzhi/kottedzh_90_m_na_uchastke_12_sot._2127130116')