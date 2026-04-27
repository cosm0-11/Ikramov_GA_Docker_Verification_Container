import shutil  # импортируем модуль для высокоуровневых операций с файлами и директориями (перемещение, копирование)

from core.config import (  # импортируем пути к директориям, связанным с карантином и пользовательскими подписями
    QUARANTINE_UPDATES_DIR,
    QUARANTINE_SIGNATURES_DIR,
    USER_SIGNATURES_DIR,
)
from core.utils import build_signature_path, get_files_from_directory  # импортируем вспомогательные функции для работы с файлами и подписями


def get_quarantine_files():  # функция получения списка файлов обновлений, находящихся в карантине
    return get_files_from_directory(QUARANTINE_UPDATES_DIR)  # возвращаем все файлы из каталога обновлений карантина


def get_quarantine_signatures():  # функция получения списка файлов подписей, находящихся в карантине
    return get_files_from_directory(QUARANTINE_SIGNATURES_DIR)  # возвращаем все файлы из каталога подписей карантина


def move_to_quarantine(file_path):  # функция перемещения файла и связанной подписи в карантин
    quarantine_file_path = QUARANTINE_UPDATES_DIR / file_path.name  # вычисляем целевой путь файла обновления в каталоге карантина

    signature_path = build_signature_path(file_path, USER_SIGNATURES_DIR)  # определяем путь к исходному файлу подписи в пользовательском каталоге
    quarantine_signature_path = QUARANTINE_SIGNATURES_DIR / f"{file_path.stem}.sig"  # вычисляем целевой путь подписи в каталоге карантина

    shutil.move(str(file_path), str(quarantine_file_path))  # переносим файл обновления из пользовательского каталога в карантин

    moved_signature = False  # флаг, отражающий факт переноса связанной подписи
    if signature_path.exists():  # проверяем, существует ли файл подписи для данного обновления
        shutil.move(str(signature_path), str(quarantine_signature_path))  # переносим файл подписи в каталог карантина
        moved_signature = True  # отмечаем, что подпись была успешно перемещена

    return quarantine_file_path, quarantine_signature_path, moved_signature  # возвращаем пути к карантинным файлам и признак переноса подписи


def clear_quarantine():  # функция полной очистки карантинной зоны
    quarantine_files = get_quarantine_files()  # получаем список файлов обновлений в карантине
    quarantine_signatures = get_quarantine_signatures()  # получаем список файлов подписей в карантине

    for file_path in quarantine_files:  # поочерёдно обрабатываем каждый файл обновления
        file_path.unlink()  # удаляем файл обновления из файловой системы

    for signature_path in quarantine_signatures:  # поочерёдно обрабатываем каждый файл подписи
        signature_path.unlink()  # удаляем файл подписи из файловой системы

    return len(quarantine_files), len(quarantine_signatures)  # возвращаем количество удалённых файлов обновлений и подписей