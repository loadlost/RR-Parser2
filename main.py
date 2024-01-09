# main.py
# Основной модуль скрипта, предназначенный для обработки кадастровых номеров.
# Использует функции из других модулей для отправки запросов, обработки данных
# и сохранения результатов в файл Excel. Включает в себя логику аутентификации,
# обработки ошибок и логирование основных шагов выполнения.


import logging

from dataframe_functions import add_data_to_dataframe, clean_dataframe, save_to_excel
from requests_functions import get_captcha, get_cookie, get_object_info

from config import cad_numbers

# Настройка логирования для отслеживания процесса выполнения скрипта
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def process_objects(cadastral_numbers):
    # Функция обработки списка кадастровых номеров.
    # Для каждого номера осуществляется отправка запроса и обработка ответа.
    # Входные данные:
    #   cad_numbers: список строк кадастровых номеров.
    # Выходные данные: отсутствуют, но в процессе работы данные добавляются в DataFrame
    # и последующему сохранению в Excel.

    def process_loop(captcha):
        # Внутренняя функция для обработки одного объекта с учетом капчи.
        # Отправляет запрос, обрабатывает ответ и, в случае ошибки капчи, повторяет попытку.
        # Входные данные:
        #   captcha_text: текст капчи, используемый для отправки запроса.
        # Выходные данные: отсутствуют, осуществляется логирование и обработка данных.

        response = get_object_info(captcha, cadNumber)
        if response.status_code == 200:
            # Успешный запрос: данные добавляются в DataFrame.
            add_data_to_dataframe(response)
        elif response.status_code == 406:
            result = response.json()
            error_message = result.get('error')
            if error_message == 'Wrong captcha':
                # Ошибка "Неправильная капча": повтор запроса с новой капчей.
                logger.warning("Ошибка: Неправильная капча. Повторный запрос с новой капчей.")
                process_loop(get_captcha())
            else:
                # Обработка других ошибок.
                logger.error(error_message)
        else:
            # Логирование неудачных запросов с иными статусами.
            logger.error(f"Не удалось выполнить запрос. Статус код: {response.status_code}")
            logger.error(response.text)

    total_objects = len(cadastral_numbers)
    logger.info(f"Начало обработки {total_objects} объектов.")

    # Получение куки для аутентификации и запуск обработки объектов.
    get_cookie()
    for current_object, cadNumber in enumerate(cadastral_numbers, start=1):
        logger.info(f"Обработка объекта {current_object} из {total_objects} (КН: {cadNumber})...")
        process_loop(get_captcha())


def main():
    # Основная функция модуля. Инициирует процесс обработки кадастровых номеров,
    # очистку DataFrame и сохранение результатов в Excel.
    # Входные данные: отсутствуют.
    # Выходные данные: отсутствуют, но результаты работы сохраняются в файл Excel.

    process_objects(cad_numbers)
    clean_dataframe()
    save_to_excel()
    logger.info("Обработка объектов завершена.")


if __name__ == '__main__':
    main()
