import requests
import json
import time
import re
import sqlite3

import pandas as pd
# from selenium import webdriver

from seleniumwire import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

# from selenium.webdriver.common.proxy import Proxy
# from selenium.webdriver.common.proxy import ProxyType
# from selenium.webdriver.common.by import By
# from selenium.webdriver.chrome.service import Service
# from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
# from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

import config

# Класс работы с БД.
class DatabaseHandler:
    def __init__(self, db_name):
        # self.conn = sqlite3.connect(db_name)
        # self.cursor = self.conn.cursor()
        self.db_name = db_name
        self.conn = None
        self.cursor = None

    def __enter__(self):
        """Контекстный менеджер. Открывает соединение с базой данных."""
        self.conn = sqlite3.connect(self.db_name)
        self.cursor = self.conn.cursor()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """Контекстный менеджер. Закрывает соединение с базой данных."""
        if self.conn:
            if exc_type is None:
                self.conn.commit()
            else:
                self.conn.rollback()
            self.conn.close()

    # def insert_data_company(self, tunnus, company_name, main_line_of_business, address_street,
    #                        address_city, address_ind, phone, email, website):
    #     # Вставляем данные в таблицу с инн
    #     self.cursor.execute('''
    #         INSERT INTO company (tunnus, company_name, main_line_of_business, address_street,
    #                        address_city, address_ind, phone, email, website)
    #         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    #     ''', (tunnus, company_name, main_line_of_business, address_street,
    #                        address_city, address_ind, phone, email, website))

    def update_contacts(self, value, mobile_phone="", phone="", email="", is_read=True):  # is_read = 1,
        self.cursor.execute('''UPDATE company 
                                SET mobile_phone = ?,
                                phone = ?,
                                email = ?,
                                is_read = ?
                                WHERE value = ?''',
                            (mobile_phone, phone, email, is_read, value))

    def update_is_read_by_tunnus(self, value, new_is_read):
        """ Обновляем значение is_read в таблице с инн"""
        self.cursor.execute('''UPDATE tunnus SET is_read = ? WHERE value = ?''',
                            (new_is_read, value))

    def get_tunnus(self):
        list_tunnus = self.cursor.execute(f'SELECT * FROM company WHERE is_read = 0 LIMIT {config.req_num}')
        # Извлечение всех строк из курсора
        list_tunnus = list_tunnus.fetchall()

        # Вывод результата
        # print("list_tunnus:")
        # for row in list_tunnus:
        #     print(row)
        return list_tunnus


# Класс для работы с api ytj.fi
class Ytj:
    def __init__(self):
        self.url = "https://avoindata.prh.fi/opendata-ytj-api/v3/"


    def get_companies(self, company_type):
        # headers = {
        #     'Accept': 'application/json',  # Указываем, что ожидаем ответ в формате JSON
        # }
        url = f"{self.url}companies?"
        # Параметры запроса
        params = {}
        if company_type:
            params['mainBusinessLine'] = company_type  # Добавляем параметр типа компании, если он указан

        # response = requests.get(url, params=params)
        # print(response.text)
        try:
            # Отправляем GET-запрос с параметрами
            response = requests.get(url, params=params)
            print(f"response {response}")
            # Проверяем статус-код ответа
            if response.status_code == 200:
                print("Ответ статус 200.")
                data = response.json()
                # print(data)
                # # Красивый вывод JSON
                # pretty_json = json.dumps(data, indent=4, ensure_ascii=False)
                # print(pretty_json)

                # Преобразование данных в DataFrame
                df = pd.DataFrame(data)
                # df = pd.DataFrame(data['employees'])
                # Сохранение DataFrame в файл Excel
                df.to_excel('employees_data.xlsx', index=False)
                print("Данные успешно сохранены в файл 'employees_data.xlsx'.")

                # # Сохранение данных в файл
                # with open('data.json', 'w', encoding='utf-8') as file:
                #     json.dump(data, file, ensure_ascii=False, indent=4)

                return data
            else:
                print(f"Ошибка: {response.status_code} - {response.text}")
                return None
        except requests.exceptions.RequestException as e:
            print(f"Произошла ошибка во время запроса: {e}")
            return None


# Парсер ytj.fi
class Parser:
    def __init__(self):
        self.url = 'https://tietopalvelu.ytj.fi/yritys/'
        # self.url = 'https://mail.ru/'

    def get_contacts(self, tunnus, prox):
        # print(chrome_options)
        # prox = 'http://user232340:lcrjmo@185.212.112.68:8124'
        # Добавления пользовательских заголовков
        # chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")

        # chrome_options = Options()
        # chrome_options.add_argument("--headless=new")  # Если нужно, чтобы браузер не отображался
        # # chrome_options.add_argument(f"--proxy-server={prox}")
        #
        # chrome_options.proxy = Proxy({ 'proxyType': ProxyType.MANUAL, 'httpProxy' : 'http.proxy:1234'})
        #
        # # Старый вариант с отображением браузера
        # # service = Service(ChromeDriverManager().install())
        # # driver = webdriver.Chrome(service=service, options=chrome_options)
        #

        # set selenium-wire options to use the proxy
        seleniumwire_options = {
            "proxy": {
                "http": prox,
                "https": prox
            },
        }

        # set Chrome options to run in headless mode
        options = Options()
        # options.add_argument("--headless")
        options.add_argument("--headless=new")

        # initialize the Chrome driver with service, selenium-wire options, and chrome options
        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            seleniumwire_options=seleniumwire_options,
            options=options
        )
        # Новый вариант с не отображением браузера
        # driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

        try:
            # Устанавливаем размер окна
            desired_width = 1920
            desired_height = 1080
            driver.set_window_size(desired_width, desired_height)

            # try:

            # Открываем нужную страницу
            driver.get(f'{self.url}{tunnus}')
            print(f'{self.url}{tunnus}')
            # # driver.get(f'{self.url}')
            # except:
            #     print("хз че тут")
            #     return

            # # Ждем, пока страница загрузится полностью.
            # time.sleep(config.sleep_before)

            # Ждем, пока все кнопки не загрузятся
            try:
                WebDriverWait(driver, config.sleep_all).until(
                    EC.presence_of_all_elements_located((By.CLASS_NAME, 'btn-secondary'))
                )
            except: print("Кнопок нет")

            # Находим все кнопки с общим классом
            buttons = driver.find_elements(By.CLASS_NAME, 'btn-secondary')

            # Нажимаем на каждую кнопку
            try:
                for button in buttons:
                    try:
                        button.click()
                    except: ...
            except: ...
            # # Ждем, пока новые данные на странице загрузятся полностью.
            time.sleep(config.sleep_after)

            # Получаем HTML-контент страницы
            html_content = driver.page_source
            # Используем BeautifulSoup для парсинга HTML-контента
            soup = BeautifulSoup(html_content, 'html.parser')

            # Поиск телефона
            mobile_phone = self.parser_div('Mobilephone', soup)
            try: mobile_phone = mobile_phone[0]
            except IndexError: mobile_phone = ''

            # Поиск телефона
            phone = self.parser_div('Phone', soup)
            try: phone = phone[0]
            except IndexError: phone = ''

            # Поиск почты
            email = self.parser_div('Email', soup)
            try: email = email[0]
            except IndexError: email = ''

            # return [tunnus, company_name, main_line_of_business, address_street, address_city, address_ind, mobile_phone, phone, email, website]
            print([tunnus, mobile_phone, phone, email])
            return [tunnus, mobile_phone, phone, email]
        finally:
            # Закрываем браузер
            driver.quit()

    def parser_div(self, reg, soup):
        # Используем регулярное выражение для поиска заголовка
        regex = re.compile(fr'{reg}')
        # Найти все <td> элементы 'headers'
        td_elements = soup.find_all('td', headers=regex)
        # Извлечь информацию из <div> в найденных <td>
        div_content = []
        for td in td_elements:
            divs = td.find_all('div')
            for div in divs:
                try:
                    div_content.append(div.get_text().strip())
                except AttributeError:
                    ...
        # print(div_content)
        return div_content

# Код для обновления is_read
# db_name = "database.db"
# value_to_update = "value"
# new_is_read_value = True
# with DatabaseHandler(db_name) as db_handler:
#     # db_handler.create_tables()  # Создадим таблицу если ее нет?
#     db_handler.update_is_read_by_value(value_to_update, new_is_read_value)

def main():
    # Получение компаний с определенным типом
    # company_type = "kuljetuspalvelut"  # Тип компаний
    # api = Ytj()
    # companies = api.get_companies(company_type)

    for _ in range(config.main_cicle):
        for prox in config.proxies_list:
            # Использование класса через контекстный менеджер.
            # Получаем список инн, где запись is_read == False.
            with DatabaseHandler('database.db') as db_handler:
                lst = db_handler.get_tunnus()

            # Парсер данных с сайта, в том числе скрытых за кнопкой.
            parser_contact = Parser()
            for i in lst:
                try:
                    contacts = parser_contact.get_contacts(i[1], prox)
                    print("Контактные данные получены.")
                    if not contacts:
                        print("Нет контактных данных.")
                    else:
                        with DatabaseHandler('database.db') as db_handler:
                            data_tuple = tuple(contacts)
                            print(data_tuple)
                            db_handler.update_contacts(data_tuple[0], data_tuple[1], data_tuple[2], data_tuple[3])
                            # db_handler.insert_data_company(data_tuple)
                            # # Обновим данные в таблице с инн, чтобы больше не читать его.
                            # db_handler.update_is_read_by_tunnus(contacts[0], True)
                except: continue


if __name__ == "__main__":
    main()