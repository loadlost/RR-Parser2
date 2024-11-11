"""
# Модуль requests_config.py содержит объекты конфигурации запросов, каждый из которых представляет собой экземпляр
# класса RequestConfig.
#
# Объект RequestConfig включает следующие параметры:
# - url: URL, на который будет отправлен запрос.
# - method: HTTP-метод (GET, POST и т.д.).
# - headers: Заголовки запроса.
# - before_request_method: Метод, который выполняется перед отправкой запроса для подготовки данных.
# - after_request_method: Метод, который выполняется после получения ответа для обработки данных.
# - data: Данные для POST-запросов.
# - use_proxies: Флаг, определяющий, нужно ли использовать прокси для запроса."""


from classes import RequestConfig

initial_response = RequestConfig(
    url='https://lk.rosreestr.ru/eservices/real-estate-objects-online',
    method='GET'
)

information_response = RequestConfig(
    url='https://lk.rosreestr.ru/account-back/access-key/cancellation/status/information',
    method='GET'
)

object_type_codes_response = RequestConfig(
    url='https://lk.rosreestr.ru/account-back/dictionary/OBJECT_TYPE_CODES?sortKey=code',
    method='GET',
    after_request_method='object_type_codes_after_method'
)

land_category_codes_response = RequestConfig(
    url='https://lk.rosreestr.ru/account-back/dictionary/LAND_CATEGORY_CODES?sortKey=code',
    method='GET',
    after_request_method='land_category_codes_after_method'
)

land_permitted_usage_codes_response = RequestConfig(
    url='https://lk.rosreestr.ru/account-back/dictionary/LAND_PERMITTED_USAGE_CODES?sortKey=code',
    method='GET',
    after_request_method='land_permitted_usage_codes_after_method'
)

room_purpose_codes_response = RequestConfig(
    url='https://lk.rosreestr.ru/account-back/dictionary/ROOM_PURPOSE_CODES?sortKey=code',
    method='GET',
    after_request_method='room_purpose_codes_after_method'
)

building_purpose_codes_response = RequestConfig(
    url='https://lk.rosreestr.ru/account-back/dictionary/BUILDING_PURPOSE_CODES?sortKey=code',
    method='GET',
    after_request_method='building_purpose_codes_after_method'
)

get_captcha_response = RequestConfig(
    url='https://lk.rosreestr.ru/account-back/captcha.png',
    method='GET',
    after_request_method='get_captcha_after_method'
)

on_response = RequestConfig(
    url='https://lk.rosreestr.ru/account-back/on',
    method='POST',
    before_request_method='set_on_response_data',
    after_request_method='process_on_response'

)
