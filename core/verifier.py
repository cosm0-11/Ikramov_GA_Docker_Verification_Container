import hashlib  # импортируем модуль hashlib для вычисления криптографических хэш‑функций
import binascii  # импортируем модуль binascii для преобразования данных из/в шестнадцатеричный формат
import shutil  # импортируем модуль shutil для операций перемещения файлов
from pathlib import Path  # импортируем класс Path для работы с путями к файлам и каталогам

import ed25519  # импортируем библиотеку для проверки цифровой подписи по алгоритму Ed25519

from core.config import (  # импортируем пути к рабочим директориям и файлу открытого ключа
    USER_UPDATES_DIR,
    USER_SIGNATURES_DIR,
    PUBLIC_KEY_PATH,
    QUARANTINE_UPDATES_DIR,
    QUARANTINE_SIGNATURES_DIR,
)
from core.utils import (  # импортируем общие вспомогательные функции
    get_files_from_directory,  # не используется в данном фрагменте, но может применяться в других сценариях проверки
    build_signature_path,  # функция построения пути к файлу подписи по пути исходного файла
)


def calculate_hash(file_path: Path, algorithm="sha256"):  # функция вычисления хэш‑значения для файла по заданному алгоритму
    if algorithm not in {"sha256", "sha512"}:  # проверяем, поддерживается ли указанный алгоритм
        raise ValueError("Поддерживаются только алгоритмы sha256 и sha512.")  # сообщаем об ошибке при неподдерживаемом алгоритме

    hash_object = hashlib.new(algorithm)  # создаём объект хэш‑функции с выбранным алгоритмом

    with file_path.open("rb") as file:  # открываем файл в бинарном режиме для чтения
        for chunk in iter(lambda: file.read(4096), b""):  # читаем файл по частям фиксированного размера до конца
            hash_object.update(chunk)  # обновляем состояние хэш‑функции очередной порцией данных

    return hash_object.hexdigest()  # возвращаем итоговое хэш‑значение в виде шестнадцатеричной строки


def get_verifying_key():  # функция получения объекта открытого ключа для проверки подписи
    if not PUBLIC_KEY_PATH.exists():  # проверяем наличие файла открытого ключа на диске
        raise FileNotFoundError("Файл открытого ключа не найден.")  # сообщаем об ошибке, если файл отсутствует

    public_key_hex = PUBLIC_KEY_PATH.read_text(encoding="utf-8").strip()  # читаем содержимое файла и удаляем пробелы и переводы строк по краям

    if not public_key_hex:  # проверяем, не оказался ли файл пустым после чтения
        raise ValueError("Файл открытого ключа пуст.")  # сообщаем о некорректном состоянии файла ключа

    try:  # пытаемся декодировать ключ из текстового hex‑представления в байты
        public_key_data = binascii.unhexlify(public_key_hex)  # преобразуем шестнадцатеричную строку в байтовую последовательность
    except binascii.Error as error:  # перехватываем ошибки декодирования hex‑строки
        raise ValueError("Открытый ключ имеет некорректный формат.") from error  # формируем понятное сообщение об ошибке формата

    try:  # пытаемся создать объект открытого ключа Ed25519 из байтов
        return ed25519.VerifyingKey(public_key_data)  # возвращаем объект открытого ключа для последующей проверки подписи
    except Exception as error:  # перехватываем ошибки при создании объекта ключа
        raise ValueError("Не удалось создать объект открытого ключа.") from error  # пробрасываем информативное сообщение об ошибке


def verify_signature(file_path: Path, signature_path: Path, verifying_key):  # функция проверки подписи для заданного файла
    try:  # оборачиваем проверку подписи в блок обработки исключений
        message = file_path.read_bytes()  # считываем содержимое проверяемого файла в виде байтов
        signature = signature_path.read_bytes()  # считываем содержимое файла подписи в виде байтов

        if not signature:  # проверяем, не является ли файл подписи пустым
            return False, "Файл подписи пуст."  # возвращаем отрицательный результат с пояснением причины

        verifying_key.verify(signature, message)  # выполняем криптографическую проверку подписи относительно содержимого файла
        return True, "Подпись действительна."  # при отсутствии исключений считаем подпись корректной

    except ed25519.BadSignatureError:  # перехватываем специфичное исключение библиотек при недействительной подписи
        return False, "Подпись недействительна."  # возвращаем отрицательный результат проверки
    except Exception as error:  # перехватываем любые другие ошибки во время проверки
        return False, f"Ошибка криптографической проверки: {error}"  # возвращаем текст ошибки для диагностики


def verify_file(file_path: Path):  # функция комплексной проверки файла и формирования результата для интерфейса
    sha256_hash = calculate_hash(file_path, "sha256")  # вычисляем хэш файла по алгоритму SHA‑256
    sha512_hash = calculate_hash(file_path, "sha512")  # вычисляем хэш файла по алгоритму SHA‑512
    signature_path = build_signature_path(file_path, USER_SIGNATURES_DIR)  # строим путь к ожидаемому файлу подписи

    if not signature_path.exists():  # если файл подписи отсутствует в пользовательском каталоге
        return {
            "file_name": file_path.name,  # имя проверяемого файла
            "status": "REJECTED",  # статус проверки — отклонён из‑за отсутствия подписи
            "details": "Файл подписи отсутствует.",  # текстовое объяснение причины отклонения
            "sha256": sha256_hash,  # вычисленное значение SHA‑256
            "sha512": sha512_hash,  # вычисленное значение SHA‑512
        }

    verifying_key = get_verifying_key()  # получаем объект открытого ключа для проверки подписи
    signature_valid, details = verify_signature(file_path, signature_path, verifying_key)  # проверяем подпись и получаем статус и комментарий

    return {
        "file_name": file_path.name,  # имя проверяемого файла
        "status": "ACCEPTED" if signature_valid else "REJECTED",  # статус проверки в зависимости от валидности подписи
        "details": details,  # текстовое описание результата проверки подписи
        "sha256": sha256_hash,  # вычисленное значение SHA‑256 для отображения и контроля целостности
        "sha512": sha512_hash,  # вычисленное значение SHA‑512 для дополнительного контроля
    }


def move_to_quarantine(file_path: Path):  # функция переноса файла и его подписи в карантин при неуспешной проверке
    quarantine_file_path = QUARANTINE_UPDATES_DIR / file_path.name  # формируем путь для файла обновления в каталоге карантина
    signature_path = build_signature_path(file_path, USER_SIGNATURES_DIR)  # определяем текущий путь к файлу подписи в пользовательском каталоге
    quarantine_signature_path = QUARANTINE_SIGNATURES_DIR / f"{file_path.stem}.sig"  # формируем путь к файлу подписи в карантине

    shutil.move(str(file_path), str(quarantine_file_path))  # перемещаем файл обновления из пользовательского каталога в карантин

    moved_signature = False  # инициализируем флаг, указывающий, была ли перенесена подпись
    if signature_path.exists():  # проверяем наличие файла подписи рядом с исходным файлом
        shutil.move(str(signature_path), str(quarantine_signature_path))  # перемещаем подпись в соответствующий карантинный каталог
        moved_signature = True  # отмечаем, что подпись была успешно перемещена

    return quarantine_file_path, quarantine_signature_path, moved_signature  # возвращаем пути к карантинным файлам и флаг переноса подписи