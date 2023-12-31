cad_numbers = [
    '77:06:0009004:1020',
    '77:06:0008011:4102',
    '77:06:0009004:4372',
    '77:06:0008011:4100',
    '77:06:0008011:4105',
    '77:06:0008011:4104',
    '77:06:0008011:4103',
    '50:21:0120114:2764',
    '50:21:0130206:231',
    '77:17:0120114:14311',
    '77:09:0004009:1056',
    '77:09:0004006:9952',
    '77:09:0004009:7736',
    '77:09:0004009:1055',
    '77:09:0004009:7317',
    '77:09:0004006:9949',
    '77:09:0004006:9950',
    '77:09:0004009:7737',
    '50:49:0020103:1254',
    '77:02:0022009:1026',
    '77:02:0022009:20',
    '77:02:0022011:1288',
    '77:02:0022011:1287'
]

proxy_url = ''

ANTICAPTCHA_KEY = ""

headers = {
    'Accept': 'application/json, text/plain, */*',
    'Accept-Encoding': 'gzip, deflate, br',
    'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
    'Connection': 'keep-alive',
    'Host': 'lk.rosreestr.ru',
    'Pragma': 'no-cache',
    'Referer': 'https://lk.rosreestr.ru/eservices/real-estate-objects-online',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'same-origin',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"'
}

columns = [
    'Кадастровый номер', 'Адрес', 'Статус объекта', 'Тип объекта', 'Назначение', 'Этаж',
    'Количество этажей', 'Количество подземных этажей', 'Площадь, кв.м', 'Кадастровая стоимость',
    'Год завершения строительства', 'Категория земель', 'Вид разрешенного использования',
    'Вид, номер и дата государственной регистрации права', 'Ограничение прав и обременение объекта недвижимости'
]

urls = {
    'cookie': 'https://lk.rosreestr.ru/account-back/access-key/cancellation/status/information',
    'captcha': 'https://lk.rosreestr.ru/account-back/captcha.png',
    'object_type_codes': 'https://lk.rosreestr.ru/account-back/dictionary/OBJECT_TYPE_CODES?sortKey=code',
    'building_purpose_codes': 'https://lk.rosreestr.ru/account-back/dictionary/BUILDING_PURPOSE_CODES?sortKey=code',
    'room_purpose_codes': 'https://lk.rosreestr.ru/account-back/dictionary/ROOM_PURPOSE_CODES?sortKey=code',
    'land_category_codes': 'https://lk.rosreestr.ru/account-back/dictionary/LAND_CATEGORY_CODES?sortKey=code',
    'search_url': 'https://lk.rosreestr.ru/account-back/on'
}