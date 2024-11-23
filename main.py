import requests
import json
import time
import re

import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

import config

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

    def get_contacts(self, tunnus):
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service)

        # Устанавливаем размер окна
        desired_width = 1920
        desired_height = 1080
        driver.set_window_size(desired_width, desired_height)

        # Открываем нужную страницу
        driver.get(f'{self.url}{tunnus}')

        # Ждем, пока страница загрузится полностью.
        time.sleep(config.sleep_before)
        # Нажмем на все кнопки.
        try:
            button = driver.find_element(By.CLASS_NAME, 'btn-secondary')
            button.click()  # Нажимаем на кнопку
        except: print("Кнопки нет")

        try:
            button = driver.find_element(By.CLASS_NAME, 'btn-secondary')
            button.click()  # Нажимаем на кнопку
        except: print("Кнопки нет")

        try:
            button = driver.find_element(By.CLASS_NAME, 'btn-secondary')
            button.click()  # Нажимаем на кнопку
        except: print("Кнопки нет")

        try:
            button = driver.find_element(By.CLASS_NAME, 'btn-secondary')
            button.click()  # Нажимаем на кнопку
        except: print("Кнопки нет")

        # Ждем, пока новые данные на странице загрузятся полностью.
        time.sleep(config.sleep_after)

        # Получаем HTML-контент страницы
        html_content = driver.page_source
        # Используем BeautifulSoup для парсинга HTML-контента
        soup = BeautifulSoup(html_content, 'html.parser')

        # Поиск названия компании
        company_name = self.parser_div('Companyname', soup)
        try: company_name = company_name[0]
        except IndexError: company_name = ''

        # Тип деятельности
        main_line_of_business = self.parser_div('Mainlineofbusiness', soup)
        try: main_line_of_business = main_line_of_business[0]
        except IndexError: main_line_of_business = ''

        # Поиск адреса компании
        address = self.parser_div('Streetaddress', soup)
        if len(address) < 2:
            address[1] = ''
        elif len(address) < 1:
            address[0] = ''

        # Поиск телефона
        phone = self.parser_div('Mobilephone', soup)
        try: phone = phone[0]
        except IndexError: phone = ''

        # Поиск почты
        email = self.parser_div('Email', soup)
        try: email = email[0]
        except IndexError: email = ''

        # Сайт
        website = self.parser_div('Website', soup)
        try: website = website[0]
        except IndexError: website = ''

        return [tunnus, company_name, main_line_of_business, address[0], address[1], phone, email, website]

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



def main():
    # Получение компаний с определенным типом
    # company_type = "kuljetuspalvelut"  # Тип компаний
    # api = Ytj()
    # companies = api.get_companies(company_type)

    # Парсер данных с сайта, в том числе скрытых за кнопкой.
    parser_contact = Parser()
    lst = ['3007803-6', '3257002-4', '3303297-3', '3257002-4', '1700111-4']
    for i in lst:
        contacts = parser_contact.get_contacts(i)
        if not contacts:
            print("Нет контактных данных.")
        else:
            print(contacts)

if __name__ == "__main__":
    main()