import os
import shutil
import random
import hashlib
import binascii
from pathlib import Path
from datetime import datetime

import ed25519

from core.config import (
    SIM_UPDATES_DIR,
    SIM_SIGNATURES_DIR,
    SIM_RESULTS_DIR,
    PUBLIC_KEY_PATH,
    SIMULATION_FILE_COUNT,
    SIMULATION_COMPROMISED_COUNT,
    SIMULATION_MISSING_SIGNATURE_COUNT,
    SIMULATION_BAR_CHART_NAME,
    SIMULATION_PIE_CHART_NAME,
)
from core.reports import save_results, create_bar_chart, create_pie_chart


def prepare_simulation_directories(): # функция подготовки директорий для симуляции
    SIM_UPDATES_DIR.mkdir(parents=True, exist_ok=True)
    SIM_SIGNATURES_DIR.mkdir(parents=True, exist_ok=True)
    SIM_RESULTS_DIR.mkdir(parents=True, exist_ok=True)


def clear_simulation_directories(): # функция очистки директорий симуляции
    for directory in (SIM_UPDATES_DIR, SIM_SIGNATURES_DIR):
        if directory.exists():
            for item in directory.iterdir():  # удаляем все файлы и подкаталоги в указанной директории
                if item.is_file():  # проверяем, является ли элемент файлом
                    item.unlink()  # удаляем файл
                elif item.is_dir():  # проверяем, является ли элемент каталогом
                    shutil.rmtree(item)  # рекурсивно удаляем каталог и всё его содержимое

    if SIM_RESULTS_DIR.exists(): # оставляем только JSON-файлы в каталоге результатов
        for item in SIM_RESULTS_DIR.iterdir(): # перебираем все элементы в каталоге результатов
            if item.is_file() and item.suffix.lower() != ".json": # проверяем, что элемент является файлом и не имеет расширения JSON
                item.unlink()  # удаляем файлы, не являющиеся JSON
            elif item.is_dir():  # если в каталоге результатов случайно оказались каталоги
                shutil.rmtree(item)  # удаляем каталоги, если они случайно попали в каталог результатов


def get_signing_key(): # функция получения закрытого ключа для подписания файлов
    private_key_hex = os.getenv("PRIVATE_KEY_HEX")
    if not private_key_hex:
        raise ValueError("Переменная окружения PRIVATE_KEY_HEX не задана.")

    try:
        private_key_data = binascii.unhexlify(private_key_hex)
    except binascii.Error as error:
        raise ValueError("PRIVATE_KEY_HEX содержит некорректный hex-формат.") from error

    try:
        return ed25519.SigningKey(private_key_data)
    except Exception as error:
        raise ValueError("Не удалось создать закрытый ключ для симуляции.") from error


def get_verifying_key(): # функция получения открытого ключа для проверки подписи
    if not PUBLIC_KEY_PATH.exists():
        raise FileNotFoundError("Файл публичного ключа отсутствует.")

    public_key_hex = PUBLIC_KEY_PATH.read_text(encoding="utf-8").strip()
    if not public_key_hex:
        raise ValueError("Файл публичного ключа пуст.")

    try:
        public_key_data = binascii.unhexlify(public_key_hex)
    except binascii.Error as error:
        raise ValueError("Публичный ключ имеет некорректный hex-формат.") from error

    try:
        return ed25519.VerifyingKey(public_key_data)
    except Exception as error:
        raise ValueError("Не удалось создать объект открытого ключа.") from error


def calculate_hash(file_path: Path, algorithm: str) -> str:  # функция вычисления хеша файла
    if algorithm not in ("sha256", "sha512"):
        raise ValueError("Допустимы только sha256 и sha512.")

    hash_obj = hashlib.new(algorithm)  # создаём объект хеширования для указанного алгоритма
    with file_path.open("rb") as file:
        for chunk in iter(lambda: file.read(4096), b""):
            hash_obj.update(chunk)
    return hash_obj.hexdigest()  # возвращаем шестнадцатеричное представление хеша


def build_signature_path(file_path: Path) -> Path:  # функция построения пути к файлу подписи
    return SIM_SIGNATURES_DIR / f"{file_path.stem}.sig"


def generate_test_updates(count: int = SIMULATION_FILE_COUNT):  # функция генерации тестовых файлов обновлений
    created_files = []

    for index in range(1, count + 1):
        file_path = SIM_UPDATES_DIR / f"update_{index}.txt"
        content = (
            f"Версия: 1.0.{index}\n"
            f"Дата: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"Описание: SIM-{index}\n"
            f"Статус: prepared\n"
        )
        file_path.write_text(content, encoding="utf-8")
        created_files.append(file_path)

    return created_files


def sign_all_updates(files):  # функция подписания всех файлов обновлений
    signing_key = get_signing_key()

    for file_path in files:
        message = file_path.read_bytes()
        signature = signing_key.sign(message)
        signature_path = build_signature_path(file_path)
        signature_path.write_bytes(signature) # сохраняем подпись в отдельный файл


def compromise_random_updates(files, count: int = SIMULATION_COMPROMISED_COUNT):  # функция компрометации случайных файлов обновлений
    if not files:
        return []

    selected = random.sample(files, min(count, len(files)))  # выбираем случайные файлы для компрометации
    for file_path in selected:
        original_content = file_path.read_text(encoding="utf-8")
        compromised_content = original_content + "."
        file_path.write_text(compromised_content, encoding="utf-8")

    return selected


def remove_random_signatures(files, count: int = SIMULATION_MISSING_SIGNATURE_COUNT):  # функция удаления подписей у случайных файлов
    if not files:
        return []

    selected = random.sample(files, min(count, len(files)))
    removed = []

    for file_path in selected:
        signature_path = build_signature_path(file_path)
        if signature_path.exists():
            signature_path.unlink()
            removed.append(file_path)

    return removed


def verify_signature(file_path: Path, signature_path: Path, verifying_key):  # функция проверки подписи файла
    try:
        message = file_path.read_bytes()
        signature = signature_path.read_bytes()

        if not signature:
            return False, "Подпись пуста."

        verifying_key.verify(signature, message)
        return True, "Подпись действительна."
    except ed25519.BadSignatureError:
        return False, "Подпись недействительна."
    except Exception as error:
        return False, f"Ошибка проверки: {error}"


def verify_all_updates(files, compromised_files=None, missing_signature_files=None):  # функция проверки всех файлов обновлений
    compromised_files = compromised_files or []  # используем пустой список, если параметр не передан
    missing_signature_files = missing_signature_files or []

    compromised_names = {file_path.name for file_path in compromised_files}  # создаём множество имён компрометированных файлов
    missing_signature_names = {file_path.name for file_path in missing_signature_files} 

    verifying_key = get_verifying_key()
    results = []

    for file_path in files:
        sha256_hash = calculate_hash(file_path, "sha256")
        sha512_hash = calculate_hash(file_path, "sha512")
        signature_path = build_signature_path(file_path)

        if not signature_path.exists():
            results.append({
                "filename": file_path.name,
                "status": "REJECTED",
                "details": "Файл подписи отсутствует.",
                "sha256": sha256_hash,
                "sha512": sha512_hash,
                "compromised": file_path.name in compromised_names,
                "missing_signature": True,
            })
            continue

        signature_valid, details = verify_signature(file_path, signature_path, verifying_key)
        results.append({
            "filename": file_path.name,
            "status": "ACCEPTED" if signature_valid else "REJECTED",
            "details": details,
            "sha256": sha256_hash,
            "sha512": sha512_hash,
            "compromised": file_path.name in compromised_names,
            "missing_signature": file_path.name in missing_signature_names,
        })

    return results


def summarize_results(results):  # функция подсчёта статистики по результатам проверки
    accepted_count = sum(1 for item in results if item["status"] == "ACCEPTED")
    rejected_count = sum(1 for item in results if item["status"] == "REJECTED")
    compromised_count = sum(1 for item in results if item["compromised"])
    missing_signature_count = sum(1 for item in results if item["missing_signature"])

    return {
        "accepted_count": accepted_count,
        "rejected_count": rejected_count,
        "compromised_count": compromised_count,
        "missing_signature_count": missing_signature_count,
    }


def run_simulation():  # основная функция запуска симуляции проверки обновлений
    prepare_simulation_directories()  # подготавливаем директории для симуляции
    clear_simulation_directories()  # очищаем директории перед началом симуляции

    files = generate_test_updates()  # генерируем тестовые файлы обновлений
    sign_all_updates(files)  # подписываем все файлы обновлений
    compromised_files = compromise_random_updates(files)  # компрометируем случайные файлы
    missing_signature_files = remove_random_signatures(files)  # удаляем подписи у случайных файлов

    results = verify_all_updates( # проверяем все файлы обновлений
        files,
        compromised_files=compromised_files,
        missing_signature_files=missing_signature_files,
    )

    summary = summarize_results(results)  # подсчитываем статистику по результатам проверки
    result_path = save_results(results)  # сохраняем результаты проверки в JSON-файл
    bar_chart_path = create_bar_chart(results)  # создаём столбчатую диаграмму по результатам
    pie_chart_path = create_pie_chart(results)  # создаём круговую диаграмму по результатам

    return { # возвращаем результаты симуляции в виде словаря
        "results": results,
        "summary": summary,
        "result_file_name": result_path.name,
        "bar_chart_name": bar_chart_path.name,
        "pie_chart_name": pie_chart_path.name,
    }