import os  # импортируем модуль os для чтения переменных окружения
from pathlib import Path  # импортируем класс Path для работы с путями к файлам

import ed25519  # импортируем библиотеку для формирования цифровой подписи по алгоритму Ed25519

from core.config import PRIVATE_KEY_ENV_NAME, USER_SIGNATURES_DIR  # импортируем имя переменной окружения и каталог хранения подписей
from core.utils import build_signature_path  # импортируем вспомогательную функцию построения пути к файлу подписи


def get_signing_key():  # функция получения объекта закрытого ключа для подписания файлов
    private_key_hex = os.getenv(PRIVATE_KEY_ENV_NAME)  # считываем приватный ключ из переменной окружения по заданному имени

    if not private_key_hex:  # проверяем, была ли переменная окружения действительно задана
        raise ValueError(
            f"Переменная окружения {PRIVATE_KEY_ENV_NAME} не задана."
        )  # возбуждаем ошибку, если приватный ключ отсутствует

    try:  # пытаемся преобразовать hex-строку в последовательность байтов
        private_key_bytes = bytes.fromhex(private_key_hex)  # декодируем приватный ключ из шестнадцатеричного представления
    except ValueError as error:  # перехватываем ошибку некорректного hex-формата
        raise ValueError("Приватный ключ имеет некорректный hex-формат.") from error  # пробрасываем более понятное сообщение об ошибке

    try:  # пытаемся создать объект закрытого ключа Ed25519 из байтового представления
        return ed25519.SigningKey(private_key_bytes)  # возвращаем объект закрытого ключа для последующего подписания
    except Exception as error:  # перехватываем любые ошибки создания объекта ключа
        raise ValueError("Не удалось создать объект закрытого ключа.") from error  # формируем понятное сообщение об ошибке


def sign_file(file_path: Path, overwrite=False):  # функция формирования подписи для указанного файла
    signing_key = get_signing_key()  # получаем закрытый ключ, необходимый для выполнения подписи
    signature_path = build_signature_path(file_path, USER_SIGNATURES_DIR)  # вычисляем путь, по которому будет сохранён файл подписи

    if signature_path.exists() and not overwrite:  # проверяем, существует ли уже подпись и не запрещена ли её перезапись
        raise FileExistsError(
            f"Подпись для файла {file_path.name} уже существует."
        )  # возбуждаем исключение, если подпись уже есть и флаг overwrite не установлен

    data = file_path.read_bytes()  # считываем исходный файл в виде набора байтов
    signature = signing_key.sign(data)  # формируем цифровую подпись содержимого файла с помощью закрытого ключа
    signature_path.write_bytes(signature)  # сохраняем полученную подпись в отдельный файл

    return signature_path  # возвращаем путь к созданному файлу подписи


def sign_file_with_result(file_path: Path, overwrite=False):  # функция обёртка для подписания файла с формированием результата в виде словаря
    try:  # оборачиваем вызов подписи в блок обработки исключений
        signature_path = sign_file(file_path, overwrite=overwrite)  # запускаем основную процедуру подписания файла
        return {
            "file_name": file_path.name,  # имя файла, для которого была сформирована подпись
            "status": "SIGNED",  # статус успешного завершения операции подписания
            "details": f"Подпись успешно сохранена: {signature_path.name}",  # подробное сообщение о результате операции
            "signature_name": signature_path.name,  # имя созданного файла подписи
        }
    except Exception as error:  # перехватываем любые ошибки, возникшие при подписании
        return {
            "file_name": file_path.name,  # имя файла, для которого пытались создать подпись
            "status": "ERROR",  # статус ошибки выполнения операции
            "details": str(error),  # текст ошибки для последующего отображения пользователю
            "signature_name": None,  # признак того, что файл подписи не был создан
        }