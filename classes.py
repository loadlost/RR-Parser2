"""Модуль содержит класс RequestConfig, который используется для хранения конфигурации запроса."""

import logging
from typing import Optional, Dict, Callable, Any, List

import requests
from PIL import Image
from captcha_recognizer.recognizer import CaptchaRecognizer

from format_data import format_rights, format_encumbrances

logger = logging.getLogger(__name__)


class CustomSession(requests.Session):
    """
    Класс-наследник requests.Session, изменяет проверку SSL-сертификатов.

    Этот класс отключает проверку SSL-сертификатов для всех запросов, отправляемых через Росреестр и Госуслуги,
    так как эти сервисы не используют корректные сертификаты.

    Methods:
    --------
    request(method: str, url: str, *args, **kwargs) -> requests.Response:
        Переопределяет стандартный метод request, отключая проверку сертификатов.
    """

    def request(self, method: str, url: str, *args, **kwargs) -> requests.Response:
        """
        Выполняет HTTP-запрос, отключая проверку SSL-сертификатов.

        :param method: Метод HTTP-запроса (GET, POST и т.д.).
        :type method: str
        :param url: URL для выполнения запроса.
        :type url: str
        :param args: Дополнительные аргументы для запроса.
        :param kwargs: Дополнительные именованные параметры для запроса.
        :return: Возвращает объект requests.Response.
        :rtype: requests.Response
        """
        kwargs['verify'] = kwargs.get('verify', False)
        return super().request(method, url, *args, **kwargs)


class RequestConfig:
    """
    Класс для конфигурирования и выполнения HTTP-запросов с поддержкой выполнения
    методов до и после запроса, а также сохранения и обработки данных.

    :ivar cad_number: Кадастровый номер, используемый для выполнения запроса.
    :type cad_number: Optional[str]

    :ivar building_purpose_codes_dict: Словарь кодов назначения зданий.
    :type building_purpose_codes_dict: List[Dict[str, Any]]

    :ivar room_purpose_codes_dict: Словарь кодов назначения помещений.
    :type room_purpose_codes_dict: List[Dict[str, Any]]

    :ivar land_permitted_usage_codes_dict: Словарь кодов разрешённого использования земель.
    :type land_permitted_usage_codes_dict: List[Dict[str, Any]]

    :ivar land_category_codes_dict: Словарь кодов категорий земель.
    :type land_category_codes_dict: List[Dict[str, Any]]

    :ivar object_type_codes_dict: Словарь кодов типов объектов.
    :type object_type_codes_dict: List[Dict[str, Any]]

    :ivar captcha: Расшифрованное значение капчи, используемое для выполнения запросов.
    :type captcha: Optional[str]

    :ivar all_data: Список, содержащий все данные, собранные при выполнении запросов.
    :type all_data: List[Dict[str, Any]]

    Methods:
        execute(session: requests.Session) -> requests.Response:
        Выполняет запрос на основе конфигурации объекта RequestConfig, используя указанную сессию
    """

    cad_number: Optional[str] = None
    building_purpose_codes_dict: List[Dict[str, Any]] = []
    room_purpose_codes_dict: List[Dict[str, Any]] = []
    land_permitted_usage_codes_dict: List[Dict[str, Any]] = []
    land_category_codes_dict: List[Dict[str, Any]] = []
    object_type_codes_dict: List[Dict[str, Any]] = []
    captcha: Optional[str] = None
    all_data: List[Dict[str, Any]] = []

    def __init__(self, url: Optional[str] = None, method: str = 'GET', headers: Optional[Dict[str, str]] = None,
                 data: Optional[Dict] = None, use_proxies: bool = True,
                 before_request_method: Optional[str] = None, after_request_method: Optional[str] = None):

        """
        Инициализирует объект RequestConfig для выполнения HTTP-запросов.

        :param url: URL запроса. Если не указан, используется None.
        :type url: Optional[str]

        :param method: Метод запроса ('GET' или 'POST'). По умолчанию 'GET'.
        :type method: str

        :param headers: Заголовки для запроса. Если не указаны, создается пустой словарь.
        :type headers: Optional[Dict[str, str]]

        :param data: Данные для POST-запросов. Если не указаны, используется None.
        :type data: Optional[Dict]

        :param use_proxies: Указывает, нужно ли использовать прокси для запроса. По умолчанию True.
        :type use_proxies: bool

        :param before_request_method: Имя метода, который будет выполнен перед отправкой запроса. Может быть None.
        :type before_request_method: Optional[str]

        :param after_request_method: Имя метода, который будет выполнен после получения ответа. Может быть None.
        :type after_request_method: Optional[str]

        """

        # URL запроса
        self.url: Optional[str] = url

        # Метод (GET или POST)
        self.method: str = method

        # Заголовки запроса, если не переданы — создается пустой словарь
        self.headers: Dict[str, str] = headers if headers else {}

        # Данные для POST-запросов, могут быть None
        self.data: Optional[Dict] = data

        # Указывает, использовать ли прокси для запросов. Если False, то прокси не будет использован для всех запросов.
        # Если True, то прокси будет использован для всех запросов. Если use_proxies, то значение берётся из
        # конфигурации запроса. (из объектов RequestConfig в requests_config.py)
        self.use_proxies: bool = use_proxies

        # Метод, который будет выполнен перед отправкой запроса (может быть None)
        self.before_request_method: Optional[str] = before_request_method

        # Метод, который будет выполнен после получения ответа (может быть None)
        self.after_request_method: Optional[str] = after_request_method

        # Сессия, используемая для выполнения запроса, инициализируется позже (requests.Session)
        self.session: Optional[requests.Session] = None

    def execute(self, session: requests.Session) -> requests.Response:
        """
        Выполняет запрос, используя requests.Session и конфигурацию объекта RequestConfig.

        Метод поддерживает выполнение GET и POST запросов. Если указан метод `before_request_method`,
        он будет выполнен перед отправкой запроса для подготовки данных. Аналогично, `after_request_method`
        выполняется после получения ответа. Если `after_request_method` возвращает новый ответ,
        то именно он будет возвращён.

        :param session: Активная сессия requests.Session для выполнения запроса.
        :type session: requests.Session
        :return: Ответ от сервера в виде объекта requests.Response. Если метод after_request_method возвращает
                 новый response, то именно он будет возвращён.
        :rtype: requests.Response
        :raises ValueError: Если указан неподдерживаемый HTTP-метод (не GET и не POST).
        """

        logger.info(f'Executing {self.method} request to {self.url}')

        self.session: requests.Session = session  # Сохраняет текущую сессию для использования в других методах

        if self.before_request_method:
            # Если указан метод, который должен выполняться перед запросом,
            # получает ссылку на этот метод и вызывает его, если он существует и может быть вызван.
            method_to_call: Optional[Callable] = getattr(self, self.before_request_method, None)
            if callable(method_to_call):
                method_to_call()  # Вызывает метод для подготовки данных перед выполнением запроса

        proxies: Dict[str, str] = session.proxies if self.use_proxies else {"http": "", "https": ""}
        # Если флаг self.use_proxies True (по умолчанию), используется прокси из сессии.
        # Если False, прокси не используется.

        if self.method.upper() == 'GET':
            # Выполняет GET запрос с указанными параметрами.
            response: requests.Response = session.get(self.url, headers=self.headers, proxies=proxies)
        elif self.method.upper() == 'POST':
            # Выполняет POST запрос с указанными параметрами и данными.
            response: requests.Response = session.post(self.url, headers=self.headers, json=self.data, proxies=proxies)
        else:
            # Выбрасывает исключение, если метод не поддерживается.
            raise ValueError(f"Unsupported method: {self.method}")

        if self.after_request_method:
            # Если указан метод для обработки ответа, вызывает его.
            method_to_call: Optional[Callable] = getattr(self, self.after_request_method, None)
            if callable(method_to_call):
                new_response: Optional[requests.Response] = method_to_call(response)
                # Если метод возвращает новый ответ, то возвращает его.
                if new_response:
                    logger.info(f'Received new response from after request method: {self.after_request_method}')
                    return new_response

        return response

    def object_type_codes_after_method(self, response: requests.Response) -> None:
        """
        Обрабатывает ответ, содержащий коды типов объектов, и сохраняет данные
        в атрибуте `object_type_codes_dict`.

        :param response: Ответ от сервера, содержащий JSON.
        :type response: requests.Response
        """
        logger.info("Saving object type codes from response.")
        self._save_dict(response, 'object_type_codes_dict')

    def land_category_codes_after_method(self, response: requests.Response) -> None:
        """
        Обрабатывает ответ, содержащий коды категорий земель, и сохраняет данные
        в `land_category_codes_dict`.

        :param response: Ответ от сервера, содержащий JSON.
        :type response: requests.Response
        """
        logger.info("Saving land category codes from response.")
        self._save_dict(response, 'land_category_codes_dict')

    def land_permitted_usage_codes_after_method(self, response: requests.Response) -> None:
        """
        Обрабатывает ответ, содержащий коды разрешённого использования земель,
        и сохраняет данные в `land_permitted_usage_codes_dict`.

        :param response: Ответ от сервера, содержащий JSON.
        :type response: requests.Response
        """
        logger.info("Saving land permitted usage codes from response.")
        self._save_dict(response, 'land_permitted_usage_codes_dict')

    def room_purpose_codes_after_method(self, response: requests.Response) -> None:
        """
        Обрабатывает ответ, содержащий коды назначения помещений, и сохраняет
        данные в `room_purpose_codes_dict`.

        :param response: Ответ от сервера, содержащий JSON.
        :type response: requests.Response
        """
        logger.info("Saving room purpose codes from response.")
        self._save_dict(response, 'room_purpose_codes_dict')

    def building_purpose_codes_after_method(self, response: requests.Response) -> None:
        """
        Обрабатывает ответ, содержащий коды назначения зданий, и сохраняет данные
        в `building_purpose_codes_dict`.

        :param response: Ответ от сервера, содержащий JSON.
        :type response: requests.Response
        """
        logger.info("Saving building purpose codes from response.")
        self._save_dict(response, 'building_purpose_codes_dict')

    @staticmethod
    def _save_dict(response: requests.Response, attribute_name: str) -> None:
        """
        Извлекает JSON-данные из ответа и сохраняет их в указанном атрибуте
        класса RequestConfig.

        :param response: Ответ от сервера, содержащий JSON-данные.
        :type response: requests.Response
        :param attribute_name: Имя атрибута класса для сохранения данных.
        :type attribute_name: str
        """
        logger.info(f"Extracting JSON data from response and saving to `{attribute_name}`.")
        json_data: Dict = response.json()
        setattr(RequestConfig, attribute_name, json_data)
        logger.info(f"Data saved to `{attribute_name}`.")

    def get_captcha_after_method(self, response: requests.Response) -> requests.Response:
        """
        Обрабатывает ответ, содержащий изображение капчи, сохраняет его локально,
        распознает и получает текст капчи.

        Если распознавание капчи не удалось или капча неверная, метод
        повторяет запрос.

        :param response: Ответ от сервера с изображением капчи.
        :type response: requests.Response
        :return: Повторный вызов метода execute с текущей сессией, если капча неверна.
        :rtype: requests.Response
        """
        # Проверка статуса ответа. Если код не 200, повторный запрос
        if response.status_code != 200:
            return self.execute(self.session)

        # Сохраняем изображение капчи в файл
        captcha_file = 'captcha.png'
        with open(captcha_file, 'wb') as f:
            f.write(response.content)
        logger.info("Captcha image saved as 'captcha.png'")

        # Создаем экземпляр распознавателя капчи
        recognizer = CaptchaRecognizer()

        try:
            # Открываем файл изображения и передаем его в распознаватель
            with Image.open(captcha_file) as img:
                captcha_text = recognizer.predict(img)

            # Проверка на пустой результат распознавания
            if not captcha_text:
                logger.info("Captcha recognition failed, retrying captcha request.")
                return self.execute(self.session)

            logger.info(f"Captcha text obtained: {captcha_text}")

            # Сохраняем распознанный текст капчи
            RequestConfig.captcha = captcha_text

        except RuntimeError as e:
            logger.error(f"Exception during captcha processing: {e}")
            raise e

        # Проверяем правильность капчи
        if not self._test_captcha():
            logger.info("Captcha verification failed, retrying.")
            return self.execute(self.session)

        return response  # Возвращаем ответ при успешной верификации капчи

    def _test_captcha(self) -> bool:
        """
        Проверяет правильность распознанной капчи, отправляя её на сервер для подтверждения.

        :return: True, если капча корректна, иначе False.
        :rtype: bool
        """
        # Формируем URL для проверки капчи
        captcha_text: str = RequestConfig.captcha
        logger.info(f"Testing captcha: {captcha_text}")
        url: str = f'https://lk.rosreestr.ru/account-back/captcha/{captcha_text}'

        # Отправляем запрос на проверку капчи
        response: requests.Response = self.session.get(url)

        # Если статус-код не 200, капча неверна
        if response.status_code != 200:
            logger.info(f"Captcha {captcha_text} is incorrect.")
            return False

        # Логирование успешной проверки капчи
        logger.info(f"Captcha {captcha_text} is correct.")
        return True

    def set_on_response_data(self) -> None:
        """
        Устанавливает значение `self.data` для POST-запроса, используя кадастровый номер
        и текст капчи из атрибутов класса RequestConfig.

        Метод вызывается перед выполнением `process_on_response` для подготовки данных запроса.

        :return: None
        """
        # Формируем данные для POST-запроса, включая тип фильтра, кадастровый номер и капчу
        self.data: Dict[str, Any] = {
            "filterType": "cadastral",
            "cadNumbers": [RequestConfig.cad_number],
            "captcha": RequestConfig.captcha
        }

        # Логируем установленные данные для запроса
        logger.info(f'Set data with cadNumber: {RequestConfig.cad_number} and captcha: {RequestConfig.captcha}')

    @staticmethod
    def process_on_response(response: requests.Response) -> None:
        """
        Обрабатывает ответ от сервера, извлекает информацию об объекте и сохраняет её
        в виде словаря в `RequestConfig.all_data`.

        :param response: Ответ от сервера, содержащий JSON с данными об объекте недвижимости.
        :type response: requests.Response
        :return: None
        """
        # Собираем все словари с кодами для сопоставления информации об объекте
        combined_dicts = (RequestConfig.object_type_codes_dict + RequestConfig.land_category_codes_dict
                          + RequestConfig.building_purpose_codes_dict + RequestConfig.room_purpose_codes_dict
                          + RequestConfig.land_permitted_usage_codes_dict)

        # Извлекаем JSON-данные из ответа
        json_data: Dict[str, Any] = response.json()
        # Получаем первый элемент из 'elements' или None, если данных нет
        elements = json_data.get('elements', [])
        element: Optional[Dict[str, Any]] = elements[0] if elements and isinstance(elements[0], dict) else None

        # Формируем словарь с информацией об объекте
        if element is not None:
            object_info: Dict[str, Any] = {
                'Кадастровый номер': element.get('cadNumber'),
                'Статус объекта': "Актуально" if element.get('status') == "1" else "Погашено",
                'Адрес': element.get('address', {}).get('readableAddress', ''),
                'Тип объекта': next(
                    (item['value'] for item in combined_dicts if item['code'] == element.get('objType', '')),
                    None
                ),
                'Назначение': next(
                    (item['value'] for item in combined_dicts if item['code'] == element.get('purpose', '')),
                    None
                ),
                'Количество этажей': element.get('floor'),
                'Количество подземных этажей': element.get('undergroundFloor'),
                'Этаж': element.get('levelFloor'),
                'Категория земель': next(
                    (item['value'] for item in combined_dicts if item['code'] == element.get('landCategory', '')),
                    None
                ),
                'Вид разрешенного использования': element.get('permittedUseByDoc'),
                'Год завершения строительства': element.get('oksYearBuild'),
                'Кадастровая стоимость': element.get('cadCost'),
                'Площадь, кв.м': element.get('area'),
                'Вид, номер и дата государственной регистрации права':
                    ('\n'.join([format_rights(right) for right in element.get('rights', [])])
                     if element.get('rights') else None),
                'Ограничение прав и обременение объекта недвижимости':
                    ('\n'.join([format_encumbrances(encumbrance) for encumbrance in element.get('encumbrances', [])])
                     if element.get('encumbrances') else None)
            }

            # Добавляем собранную информацию об объекте в all_data
            RequestConfig.all_data.append(object_info)
            logger.info(f"Object data appended to all_data: {object_info['Кадастровый номер']}")
