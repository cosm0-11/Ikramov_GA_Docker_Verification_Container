from pathlib import Path  # импортируем класс Path для удобной работы с путями к файлам


def compromise_file_content(file_path: Path):  # функция для компрометации содержимого файла
    original_content = file_path.read_text(encoding="utf-8")  # читаем исходное текстовое содержимое файла в кодировке UTF-8
    modified_content = original_content + "\nКомпрометация: содержимое файла было изменено."  # формируем новое содержимое с добавлением пометки о компрометации
    file_path.write_text(modified_content, encoding="utf-8")  # перезаписываем файл модифицированным содержимым


def delete_signature_file(signature_path: Path):  # функция для удаления файла подписи
    signature_path.unlink()  # удаляем файл подписи с файловой системы


def clear_signature_file(signature_path: Path):  # функция для очистки файла подписи
    signature_path.write_bytes(b"")  # перезаписываем файл подписи пустым набором байтов


def compromise_file_with_result(file_path: Path, signature_path: Path, action: str):  # основная функция сценария компрометации с формированием результата
    try:  # оборачиваем логику в блок try для обработки возможных исключений
        if action == "modify_file":  # ветка выполнения для изменения содержимого файла
            compromise_file_content(file_path)  # вызываем функцию, изменяющую содержимое файла
            return {
                "file_name": file_path.name,  # имя файла, над которым выполнялась операция
                "status": "COMPROMISED",  # статус успешной компрометации
                "details": "Содержимое файла было изменено.",  # текстовое описание выполненного действия
            }

        if action == "delete_signature":  # ветка выполнения для удаления файла подписи
            if not signature_path.exists():  # проверяем, существует ли файл подписи
                return {
                    "file_name": file_path.name,
                    "status": "ERROR",  # статус ошибки при отсутствии файла подписи
                    "details": "Файл подписи отсутствует.",  # поясняющее сообщение об ошибке
                }

            delete_signature_file(signature_path)  # вызываем функцию удаления файла подписи
            return {
                "file_name": file_path.name,
                "status": "COMPROMISED",  # статус успешной компрометации подписи
                "details": f"Подпись {signature_path.name} была удалена.",  # описание конкретного действия над подписью
            }

        if action == "clear_signature":  # ветка выполнения для очистки содержимого файла подписи
            if not signature_path.exists():  # проверяем, существует ли файл подписи
                return {
                    "file_name": file_path.name,
                    "status": "ERROR",  # статус ошибки, если файл подписи отсутствует
                    "details": "Файл подписи отсутствует.",  # пояснение причины ошибки
                }

            clear_signature_file(signature_path)  # вызываем функцию, очищающую файл подписи
            return {
                "file_name": file_path.name,
                "status": "COMPROMISED",  # статус успешной компрометации содержимого подписи
                "details": f"Подпись {signature_path.name} была очищена.",  # текстовое описание выполненной операции
            }

        return {
            "file_name": file_path.name,
            "status": "ERROR",  # статус ошибки при неизвестном типе операции
            "details": "Некорректный тип операции компрометации.",  # сообщение о том, что параметр action не поддерживается
        }

    except Exception as error:  # перехватываем любые непредвиденные исключения во время выполнения операций
        return {
            "file_name": file_path.name,
            "status": "ERROR",  # статус ошибки при возникновении исключения
            "details": f"Ошибка при выполнении операции: {error}",  # включаем текст исключения в описание для диагностики
        }