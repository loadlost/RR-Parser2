"""
Главный модуль.

Основные функции:
- Инициализация и конфигурация сессии для выполнения HTTP-запросов с поддержкой кастомных заголовков и прокси.
- Последовательное выполнение запросов для получения информации по кадастровым номерам.
- Чтение входных данных из файлов, автоматическое формирование задач и запись результатов в Excel.
- Вывод результатов обработки в удобочитаемом виде.

Основные функции модуля:
- `get_session`: Создаёт и возвращает сессию с установленными заголовками и прокси.
- `initialization`: Выполняет последовательность запросов необходимую перед поиском.
- `parse`: Парсит информацию для заданного списка кадастровых номеров.
- `process_single_cadastral_number`: Обрабатывает единичный кадастровый номер.
- `send_requests`: Выполняет запросы и обрабатывает результаты с учётом кода ответа.
- `read_files_from_input_folder`: Читает данные из файлов в папке `input`.
- `start`: Запускает полную обработку задач, включая сохранение данных и вывод результатов.

"""

import msvcrt
import os
import logging
from typing import List, Tuple, Optional

import requests
import urllib3
from pandas import DataFrame

from classes import CustomSession
from common_headers import session_headers
from format_data import save_to_excel, print_pretty_table
from requests_config import *
from credentials import proxy_url

# Настройка форматтера для логов
formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(message)s',
                              datefmt='%d-%m-%Y %H:%M:%S')

handler = logging.StreamHandler()
handler.setFormatter(formatter)
logger = logging.getLogger()
logger.addHandler(handler)
logger.setLevel(logging.INFO)

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def get_session() -> CustomSession:
    """
    Инициализирует и возвращает сессию с обновленными заголовками и прокси.

    Функция создает экземпляр CustomSession, обновляет его заголовки
    и прокси, после чего возвращает готовую сессию.

    Заголовки берутся из глобальной переменной session_headers (определена в модуле common_headers).
    Прокси устанавливаются на основе глобальной переменной proxy_url (определена в модуле credentials).


    :return:  Сессия с обновленными заголовками и прокси
    :rtype: CustomSession
    :raises: None
    """
    # Инициализация сессии
    with CustomSession() as session:
        # Обновляем заголовки сессии из common_headers
        session.headers.update(session_headers)

        # Настраиваем прокси из credentials
        session.proxies.update({
            'http': proxy_url,
            'https': proxy_url
        })

    return session


def initialization(session: CustomSession) -> None:
    """
    Инициализирует процесс входа в систему, выполняя серию запросов.

    :param session: Активная сессия для выполнения запросов.
    :type session: CustomSession
    :return: None
    :rtype: None
    :raises requests.exceptions.RequestException: Возникает при неудачном выполнении одного из запросов
    из login_sequence
    """
    logger.info('Initialization process started')

    # Список с объектами класса RequestConfig, которые содержат параметры запросов
    # Объекты RequestConfig определены в модуле requests_config
    initialization_sequence: List[RequestConfig] = [
        initial_response,
        information_response,
        object_type_codes_response,
        land_category_codes_response,
        land_permitted_usage_codes_response,
        room_purpose_codes_response,
        building_purpose_codes_response
    ]

    try:
        # Выполнение последовательности запросов
        send_requests(session, initialization_sequence)
        logger.info('Initialization process completed successfully')

    except requests.exceptions.RequestException as e:
        logger.error('Initialization process failed with error: ' + str(e))
        raise requests.exceptions.RequestException('Initialization process failed with error: ' + str(e))


def parse(session: CustomSession, cad_list: List[str]) -> None:
    """
    Выполняет процесс парсинга информации для списка кадастровых номеров.

    Функция парсит информацию по каждому кадастровому номеру в списке,
    используя последовательность запросов parsing_sequence.

    :param session: Активная сессия для выполнения запросов.
    :type session: CustomSession
    :param cad_list: Список кадастровых номеров для обработки.
    :type cad_list: List[str]
    :return: None
    :rtype: None
    :raises requests.exceptions.RequestException: Возникает при неудачном выполнении запроса или других ошибках
    в процессе парсинга.
    """
    logger.info('Parsing process started')

    logger.info(f'Cadastral numbers for parsing: {cad_list}')

    for cad in cad_list:
        process_single_cadastral_number(session, cad)

    logger.info('Parsing process completed successfully')


def process_single_cadastral_number(session: CustomSession, cad: str) -> None:
    """
    Обрабатывает один кадастровый номер, выполняя необходимые запросы.

    :param session: Активная сессия для выполнения запросов.
    :type session: CustomSession
    :param cad: Кадастровый номер для обработки.
    :type cad: str
    :return: None
    :rtype: None
    :raises requests.exceptions.RequestException: Возникает при неудачном выполнении запроса.
    """
    logger.info(f'Processing cadastral number: {cad}')

    # Устанавливаем текущий кадастровый номер для RequestConfig
    RequestConfig.cad_number = cad
    parsing_sequence: List[RequestConfig] = [
        get_captcha_response,
        on_response
    ]

    try:
        # Отправляем запросы из parsing_sequence
        send_requests(session, parsing_sequence)
        logger.info(f'Successfully parsed cadastral number: {RequestConfig.cad_number}')
    except (requests.exceptions.RequestException, Exception) as e:
        logger.error(f'Parsing failed for cadastral number: {RequestConfig.cad_number} with error: {str(e)}')
        raise requests.exceptions.RequestException('Parsing process failed with error: ' + str(e))


def send_requests(session: CustomSession, request_list: List[RequestConfig], max_url_length: int = 100,
                  url: str = 'Unknown URL') -> None:
    """
    Выполняет последовательность HTTP-запросов, используя CustomSession.

    Функция проходит по списку запросов, выполняя их через сессию.
    Логирует успешные и неуспешные запросы, ограничивает длину URL до max_url_length.
    При возникновении ошибки запросов вызывает исключение.

    :param session: Активная сессия для выполнения запросов.
    :type session: CustomSession
    :param request_list: Список объектов RequestConfig с конфигурациями запросов.
    :type request_list: List[RequestConfig]
    :param max_url_length: Максимальная длина отображаемого URL для логирования (по умолчанию 100).
    :type max_url_length: int
    :param url: URL для логирования в случае отсутствия URL в запросе.
    :type url: str
    :return: None
    :rtype: None
    :raises requests.exceptions.RequestException: Поднимает исключение в случае ошибки запроса.
    """
    successful_codes: List[int] = [200, 401]

    for request_config in request_list:
        try:
            # Выполняем запрос используя параметры запросов из объектов класса RequestConfig и метод
            # RequestConfig.execute
            response: requests.Response = request_config.execute(session)
            # Проверяем наличие URL в конфигурации запроса. Используется в логах.
            url: str = request_config.url if hasattr(request_config, 'url') else 'Unknown URL'

            # Ограничиваем длину URL для логирования
            if len(url) > max_url_length:
                url: str = url[:max_url_length] + '...'

            # Проверяем, является ли статус-код успешным
            if response.status_code in successful_codes:
                logger.info(f'{response.status_code} Request successful {url}')
            else:
                # Логируем и вызываем исключение, если запрос неуспешен
                response_text: str = response.text if hasattr(response, 'text') else 'No response text'
                logger.error(f'{response.status_code} Request failed {url} TEXT: {response_text}')
                raise requests.exceptions.RequestException(
                    'Request failed with status code: ' + str(response.status_code))
        except requests.exceptions.RequestException as e:
            # Логируем ошибку и поднимаем исключение с дополнительной информацией
            logger.error(f"Request failed {url} with error: {e}")
            raise requests.exceptions.RequestException('Request failed with error: ' + str(e))


def read_files_from_input_folder() -> List[Tuple[str, List[str]]]:
    """
    Читает все файлы в указанной папке и создает список строк для каждого файла.
    Возвращает список кортежей, где каждый кортеж содержит имя файла без расширения и список строк из файла.

    :return: Список кортежей, где каждый кортеж содержит имя файла без расширения и список строк из файла.
    :rtype: List[Tuple[str, List[str]]]
    """
    folder_path: str = 'input'

    # Проверяем, что указанный путь существует и является директорией, иначе возвращаем пустой список
    if not os.path.isdir(folder_path):
        logger.error("Input folder does not exist.")
        return []

    logger.info("Input folder exists, starting to read files.")
    result: List[Tuple[str, List[str]]] = []

    # Проходим по всем файлам в папке
    for filename in os.listdir(folder_path):
        file_path: str = os.path.join(folder_path, filename)

        # Пропускаем, если это не файл
        if not os.path.isfile(file_path):
            continue

        file_name_without_extension: str = os.path.splitext(filename)[0]
        # Читаем содержимое файла и сохраняем его строки в список
        lines: List[str] = read_file_content(file_path)
        result.append((file_name_without_extension, lines))

    return result


def read_file_content(file_path: str) -> List[str]:
    """
    Читает содержимое файла и возвращает список строк.

    :param: file_path: Путь к файлу.
    :type: file_path: str
    :return: Список строк из файла.
    :rtype: List[str]
    """
    with open(file_path, 'r', encoding='utf-8') as file:
        lines: List[str] = [line.strip() for line in file]
        logger.info(f"File '{os.path.basename(file_path)}' read successfully.")
    return lines


def add_all_data_to_dataframe() -> Optional[DataFrame]:
    """
    Преобразует данные из `RequestConfig.all_data` в DataFrame, удаляет пустые столбцы,
    сортирует по площади в порядке убывания и очищает `RequestConfig.all_data`.

    :return: DataFrame с данными из `RequestConfig.all_data`, отсортированный по площади в кв.м. Если данных нет,
    возвращает None.

    :rtype: Optional[DataFrame]
    """
    if not RequestConfig.all_data:
        logger.info("No data available to convert to DataFrame.")
        return None

    # Преобразуем данные в DataFrame и очищаем пустые столбцы
    df = DataFrame(RequestConfig.all_data).dropna(axis=1, how='all')
    logger.info("Data converted to DataFrame and empty columns dropped.")

    # Очищаем `all_data` после загрузки в DataFrame
    RequestConfig.all_data.clear()

    # Преобразуем строковые значения площади в числовой формат
    df['Площадь, кв.м'] = df['Площадь, кв.м'].str.replace(',', '.').astype(float)
    logger.info("Column 'Площадь, кв.м' converted to float.")

    # Сортируем DataFrame по площади в порядке убывания
    df = df.sort_values(by='Площадь, кв.м', ascending=False)
    logger.info("DataFrame sorted by 'Площадь, кв.м' in descending order.")

    return df


def main() -> None:
    """
    Запускает скрипт. Позволяет пользователю выбрать обработку задач из файла или ввод кадастрового номера вручную.

    :return: None
    """
    while True:
        print("Нажмите любую кнопку для обработки задач из файла или Escape для ввода кадастрового номера вручную.")

        key: bytes = msvcrt.getch()
        # Возвращает один символ, считанный с клавиатуры, в виде байтового объекта
        # key = b'\x1b'
        if key == b'\x1b':  # Если нажата клавиша Escape, то обрабатываем ввод вручную
            handle_manual_input()
        else:  # Иначе обрабатываем задачи из файла
            handle_file_tasks()


def handle_manual_input() -> None:
    """
    Обрабатывает ввод кадастрового номера вручную и запускает соответствующую задачу.
    """
    user_input: str = input("Введите кадастровый номер: ")

    # Проверка на пустую строку
    if not user_input.strip():
        logger.error("Input is empty.")
        return

    # Формируем задачу для обработки одного кадастрового номера
    tasks: List[Tuple[str, List[str]]] = [('console_task', [user_input])]
    start(tasks, flag='manual')  # Запускаем обработку задач


def handle_file_tasks() -> None:
    """
    Обрабатывает задачи, загруженные из файлов, и запускает их.
    """
    tasks: List[Tuple[str, List[str]]] = read_files_from_input_folder()  # Читаем задачи из файла
    if not tasks:
        logger.error("Input folder is empty.")
        return  # Если список задач пуст, возвращаемся к началу цикла
    start(tasks, flag='file')  # Запускаем обработку задач


def start(tasks: List[Tuple[str, List[str]]], flag: str) -> None:
    """
    Выполняет обработку задач, используя заданные кадастровые номера.

    Функция инициализирует сессию, выполняет начальную настройку, затем обрабатывает
    каждую задачу, указанную в списке `tasks`. Для каждой задачи создаётся
    DataFrame с результатами, который затем сохраняется в Excel и выводится в консоль.

    :param flag: Флаг, указывающий на то, что задачи были получены из файлов или вручную.
    :param tasks: Список задач, где каждая задача представлена кортежем,
                  содержащим имя файла и список кадастровых номеров.
    :type tasks: List[Tuple[str, List[str]]]
    :return: None
    """
    # Инициализация сессии и начальных параметров
    logger.info("Starting task processing.")
    session = get_session()
    initialization(session)

    # Обработка каждой задачи
    for file_name, lines in tasks:
        cad_list = lines
        logger.info(f"Processing file: {file_name} with cadastral numbers: {cad_list}")

        # Парсим данные для текущего списка кадастровых номеров
        parse(session, cad_list)

        # Создаём DataFrame с результатами
        df = add_all_data_to_dataframe()
        logger.info(f"Data parsed for {file_name}, DataFrame created.")

        # Сохраняем DataFrame в файл Excel
        save_to_excel(df, file_name)
        logger.info(f"Data saved to Excel for {file_name}.")
        # Выводим DataFrame в консоль (если флаг 'manual')
        if flag == 'manual':
            print_pretty_table(df)

    logger.info("Task processing completed.")


if __name__ == '__main__':
    main()
