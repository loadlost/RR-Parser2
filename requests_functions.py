# requests_functions.py
# Модуль для выполнения HTTP-запросов, обработки капчи и форматирования данных.
# Включает функции для аутентификации, получения данных об объектах и их подготовки.
# Используется в основных скриптах для взаимодействия с внешними API и сервисами.


import logging
import time

import requests
from requests.utils import dict_from_cookiejar
from python3_anticaptcha import ImageToTextTask
from datetime import datetime

from config import urls, headers, proxy_url, ANTICAPTCHA_KEY

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def send_request(method, url, payload):
    # Функция отправки HTTP-запроса.
    # Осуществляет отправку запроса методом GET или POST на указанный URL с данными и заголовками.
    # Входные данные:
    #   method (str): Метод запроса, 'GET' или 'POST'.
    #   url (str): URL-адрес для отправки запроса.
    #   payload (dict): Данные для POST-запроса или None для GET-запроса.
    # Выходные данные:
    #   response: Объект Response, полученный в результате запроса.

    logger.info(f"Отправка {method} запроса по адресу: {urls[url]}")

    # Определение метода запроса и отправка запроса
    if method.upper() == 'GET':
        response = requests.get(urls[url], headers=headers, proxies={'http': proxy_url, 'https': proxy_url},
                                verify=False)
    elif method.upper() == 'POST':
        response = requests.post(urls[url], json=payload, proxies={'http': proxy_url, 'https': proxy_url},
                                 headers=headers, verify=False)
    else:
        # Если указан неподдерживаемый метод, выбрасываем исключение
        raise ValueError("Неподдерживаемый метод. Поддерживаются только 'GET' и 'POST'.")

    logger.info(f"Получен ответ: {response.status_code}")

    if response.status_code in [200, 401, 406]:
        return response

    time.sleep(5)
    send_request(method, url, payload)
    return None


def get_cookie():
    # Функция получения куки для аутентификации.
    # Выполняет GET-запрос для получения и установки куки в заголовки запросов.
    # Входные данные: отсутствуют.
    # Выходные данные: отсутствуют, но куки устанавливается в заголовки запросов.

    logger.info("Получение куки...")

    # Выполнение GET-запроса для получения куки
    cookie_response = send_request('GET', 'cookie', None)

    # Преобразование полученных куки в словарь
    cookie_dict = requests.utils.dict_from_cookiejar(cookie_response.cookies)

    # Обновление словаря headers
    cookie = {'Cookie': '; '.join([f'{key}={value}' for key, value in cookie_dict.items()])}
    headers.update(cookie)


def get_captcha():
    # Функция получения капчи для запросов.
    # Выполняет GET-запрос для получения изображения капчи и распознавания текста.
    # Входные данные: отсутствуют.
    # Выходные данные:
    #   str: Распознанный текст капчи, используемый в дальнейших запросах.

    logger.info("Получение капчи...")

    # Выполнение GET-запроса для получения капчи
    captcha_response = send_request('GET', 'captcha', None)

    # Если запрос успешен (статус код 200), сохраняем изображение в файл captcha.png
    if captcha_response.status_code == 200:
        with open('captcha.png', 'wb') as f:
            f.write(captcha_response.content)
        logger.info("Файл captcha.png успешно сохранен")

    # Задаем путь к файлу с изображением капчи
    captcha_file = 'captcha.png'

    # Используем сервис распознавания капчи для получения текста
    raw_result = ImageToTextTask.ImageToTextTask(anticaptcha_key=ANTICAPTCHA_KEY).captcha_handler(
        captcha_file=captcha_file)

    # Получаем текст капчи из результата
    captcha = raw_result.get('solution').get('text')

    logger.info(f"Получена капча: {captcha}")
    return captcha


def add_to_dataframe(element):
    # Функция добавления данных из элемента в DataFrame.
    # Обрабатывает и форматирует информацию об объекте для включения в словарь данных.
    # Входные данные:
    #   element (dict): Словарь с информацией об объекте.
    # Выходные данные:
    #   dict: Форматированный словарь данных для включения в DataFrame.

    logger.info("Добавление данных в словарь data...")

    def get_normal_date(millis):
        # Преобразование миллисекунд в формат даты (день.месяц.год).
        if millis is None:
            return None
        seconds = millis / 1000.0
        date_object = datetime.utcfromtimestamp(seconds)
        formatted_date = date_object.strftime('%d.%m.%Y')
        return formatted_date

    def get_object_type(obj_type):
        # Получение типа объекта по его коду.
        logger.info(f"Получение типа объекта для кода: {obj_type}...")
        object_type_code = (send_request('GET', 'object_type_codes', None).json())
        return get_value_by_code(obj_type, object_type_code)

    def get_purpose(purpose, obj_type):
        # Получение назначения объекта по его коду и типу объекта.
        logger.info(f"Получение назначения объекта для кода: {purpose} и типа объекта: {obj_type}...")
        if obj_type in ['Здание', 'Сооружение', 'Объект незавершенного строительства',
                        'Предприятие как имущественный комплекс', 'Единый недвижимый комплекс']:
            building_purpose_code = send_request('GET', 'building_purpose_codes', None).json()
            return get_value_by_code(purpose, building_purpose_code)

        elif obj_type in ['Помещение', 'Машино-место']:
            room_purpose_code = send_request('GET', 'room_purpose_codes', None).json()
            return get_value_by_code(purpose, room_purpose_code)

    def get_land_category(land_category):
        # Получение категории земель по её коду.
        logger.info(f"Получение категории земель для кода: {land_category}...")
        land_category_code = send_request('GET', 'land_category_codes', None).json()
        return get_value_by_code(land_category, land_category_code)

    def get_value_by_code(code, dictionary):
        # Получение значения по коду из словаря.
        logger.info(f"Получение значения по коду: {code}...")
        for item in dictionary:
            if item['code'] == code:
                return item['value']

    def format_rights(right):
        # Форматирование данных о правах на недвижимость.
        return f"{right.get('rightTypeDesc', '')}, {right.get('rightNumber', '')} " \
               f"от {get_normal_date(right.get('rightRegDate'))}"

    def format_encumbrances(encumbrance):
        # Форматирование данных об обременениях недвижимости.
        return f"{encumbrance.get('typeDesc', '')} {encumbrance.get('encumbranceNumber', '')}" + \
            (f" от {get_normal_date(encumbrance.get('startDate'))}" if encumbrance.get('startDate') else "")

    # Формирование словаря с данными
    data = {
        'Кадастровый номер': element.get('cadNumber'),
        'Статус объекта': "Актуально" if element.get('status') == "1" else "Погашено",
        'Адрес': element.get('address', {}).get('readableAddress', ''),
        'Тип объекта': get_object_type(element.get('objType', '')),
        'Назначение': get_purpose(element.get('purpose', ''), get_object_type(element.get('objType', ''))),
        'Количество этажей': element.get('floor'),
        'Количество подземных этажей': element.get('undergroundFloor'),
        'Этаж': element.get('levelFloor'),
        'Категория земель': get_land_category(element.get('landCategory', '')),
        'Вид разрешенного использования': element.get('permittedUseByDoc', ''),
        'Год завершения строительства': element.get('oksYearBuild', ''),
        'Кадастровая стоимость': element.get('cadCost', ''),
        'Площадь, кв.м': element.get('area', ''),
        'Вид, номер и дата государственной регистрации права':
            '\n'.join([format_rights(right) for right in element.get('rights', [])]),
        'Ограничение прав и обременение объекта недвижимости':
            '\n'.join([format_encumbrances(encumbrance) for encumbrance in element.get('encumbrances', [])])
    }

    # Преобразование пустых строк в None
    data = {key: None if value == "" else value for key, value in data.items()}
    logger.info("Данные успешно добавлены в словарь data.")
    return data


def get_object_info(captcha, cad_number):
    # Функция получения информации об объекте недвижимости.
    # Осуществляет POST-запрос с кадастровым номером объекта и капчей для получения данных.
    # Входные данные:
    #   captcha (str): Текст капчи.
    #   cad_number (str): Кадастровый номер объекта.
    # Выходные данные:
    #   response: Объект Response с информацией об объекте или ошибкой запроса.

    # Подготовка данных для запроса
    payload = {"filterType": "cadastral", "cadNumbers": [cad_number], "captcha": captcha}

    # Отправка POST-запроса для получения информации о недвижимости
    response = send_request('POST', 'search_url', payload)

    return response
