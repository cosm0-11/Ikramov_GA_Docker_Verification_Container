from django.shortcuts import render, redirect  # импортируем функции для рендеринга шаблонов и перенаправления пользователя

from core.config import ( # импортируем константы конфигурации, используемые в представлениях
    USER_UPDATES_DIR, 
    USER_SIGNATURES_DIR, 
    MAX_USER_FILES,
    SIMULATION_FILE_COUNT,
    SIMULATION_COMPROMISED_COUNT,
    SIMULATION_MISSING_SIGNATURE_COUNT,
    SIMULATION_BAR_CHART_NAME,
    SIMULATION_PIE_CHART_NAME,
)
from core.utils import build_signature_path
from core.paths import prepare_directories
from core.file_manager import (
    get_user_files,
    normalize_filename,
    validate_filename,
    validate_content,
    create_file_with_content,
    generate_random_content,
)
from core.signer import sign_file_with_result
from core.verifier import verify_file
from core.compromise_manager import compromise_file_with_result
from core.quarantine_manager import (
    move_to_quarantine,
    get_quarantine_files,
    get_quarantine_signatures,
    clear_quarantine,
)
from core.simulation import run_simulation, clear_simulation_directories


def index(request):  # представление для отображения списка пользовательских файлов
    prepare_directories()
    files = get_user_files()
    return render(request, "web_container/index.html", {"files": files})


def create_file_view(request):  # представление для создания нового файла
    prepare_directories()

    if request.method == "POST": # проверяем, что запрос является POST-запросом (отправка формы)
        files = get_user_files()  # получаем список существующих пользовательских файлов
        if len(files) >= MAX_USER_FILES:  # проверяем, не превышено ли максимальное количество файлов
            context = {
                "error": f"Достигнуто максимальное количество пользовательских файлов: {MAX_USER_FILES}.",
                "filename": request.POST.get("filename", "").strip(),
                "content": request.POST.get("content", ""),
                "mode": request.POST.get("mode", "manual"),
            }
            return render(request, "web_container/create_file.html", context)  # возвращаем шаблон с сообщением об ошибке

        raw_filename = request.POST.get("filename", "").strip()  # получаем имя файла из POST-данных и удаляем пробелы по краям
        mode = request.POST.get("mode", "manual")  # получаем режим создания файла (по умолчанию "manual")
        content = request.POST.get("content", "")  # получаем содержимое файла из POST-данных

        is_valid, error_message = validate_filename(raw_filename)  # проверяем корректность имени файла
        if not is_valid:
            context = {
                "error": error_message,
                "filename": raw_filename,
                "content": content,
                "mode": mode,
            }
            return render(request, "web_container/create_file.html", context)  # возвращаем шаблон с сообщением об ошибке

        filename = normalize_filename(raw_filename)  # нормализуем имя файла (добавляем расширение, если нужно)
        file_path = USER_UPDATES_DIR / filename

        if file_path.exists():  # проверяем, не существует ли уже файл с таким именем
            context = {
                "error": f"Файл {filename} уже существует.",
                "filename": raw_filename,
                "content": content,
                "mode": mode,
            }
            return render(request, "web_container/create_file.html", context)  # возвращаем шаблон с сообщением об ошибке

        if mode == "random":  # если выбран режим случайной генерации содержимого
            content = generate_random_content()  # генерируем случайное содержимое файла
        elif mode != "manual":  # если указан некорректный режим создания файла
            context = {
                "error": "Некорректный режим создания файла.",
                "filename": raw_filename,
                "content": content,
                "mode": "manual",
            }
            return render(request, "web_container/create_file.html", context)  # возвращаем шаблон с сообщением об ошибке

        is_valid, error_message = validate_content(content)  # проверяем допустимость содержимого файла
        if not is_valid:  # если содержимое файла не прошло валидацию
            context = {
                "error": error_message,
                "filename": raw_filename,
                "content": content,
                "mode": mode,
            }
            return render(request, "web_container/create_file.html", context)  # возвращаем шаблон с сообщением об ошибке

        try:
            create_file_with_content(file_path, content)  # создаём файл с указанным содержимым
        except Exception as error:  # перехватываем любые ошибки при создании файла
            context = {
                "error": f"Ошибка при создании файла: {error}",
                "filename": raw_filename,
                "content": content,
                "mode": mode,
            }
            return render(request, "web_container/create_file.html", context)

        context = {
            "result": {
                "file_name": filename,
                "status": "CREATED",
                "details": "Файл успешно создан.",
                "mode": "Случайная генерация" if mode == "random" else "Ручной ввод",
            }
        }
        return render(request, "web_container/create_result.html", context)  # возвращаем шаблон с результатом создания файла

    context = {  # контекст для отображения формы создания файла при GET-запросе
        "mode": "manual",
    }
    return render(request, "web_container/create_file.html", context)  # возвращаем шаблон формы создания файла


def delete_file_view(request):  # представление для удаления файла и его подписи
    prepare_directories()

    file_name = request.GET.get("file") if request.method == "GET" else request.POST.get("file")  # получаем имя файла из GET- или POST-параметров

    if not file_name:  # если имя файла не указано, перенаправляем пользователя на главную страницу
        return redirect("index")

    file_path = USER_UPDATES_DIR / file_name
    signature_path = build_signature_path(file_path, USER_SIGNATURES_DIR)

    if not file_path.exists():  # если указанный файл не существует
        context = {
            "error": f"Файл {file_name} не найден.",
        }
        return render(request, "web_container/delete_result.html", context)  # возвращаем шаблон с сообщением об ошибке

    if request.method == "POST":  # если запрос является POST-запросом (подтверждение удаления)
        try:
            file_path.unlink()  # удаляем файл из файловой системы

            signature_deleted = False
            if signature_path.exists():
                signature_path.unlink()
                signature_deleted = True

            context = {
                "result": {
                    "file_name": file_name,
                    "status": "DELETED",
                    "details": "Файл успешно удален.",
                    "signature_deleted": signature_deleted,
                    "signature_name": signature_path.name,
                }
            }
            return render(request, "web_container/delete_result.html", context)  # возвращаем шаблон с результатом удаления

        except Exception as error:  # перехватываем любые ошибки при удалении файла
            context = {
                "error": f"Ошибка при удалении файла: {error}",
            }
            return render(request, "web_container/delete_result.html", context)  # возвращаем шаблон с сообщением об ошибке

    context = { # контекст для отображения страницы подтверждения удаления при GET-запросе
        "file_name": file_name,
        "signature_exists": signature_path.exists(),
        "signature_name": signature_path.name,
    }
    return render(request, "web_container/delete_confirm.html", context)  # возвращаем шаблон с подтверждением удаления


def sign_view(request):  # представление для подписания файла
    prepare_directories()

    if request.method == "POST":  # если запрос является POST-запросом (подтверждение подписания)
        file_name = request.POST.get("file") # получаем имя файла из POST-параметров
        overwrite = request.POST.get("overwrite") == "yes"  # проверяем, нужно ли перезаписать существующую подпись
    else:
        file_name = request.GET.get("file")  # получаем имя файла из GET-параметров
        overwrite = False  # по умолчанию не перезаписываем подпись

    if not file_name:
        return redirect("index")

    file_path = USER_UPDATES_DIR / file_name

    if not file_path.exists():  # если указанный файл не существует
        context = {
            "error": f"Файл {file_name} не найден.",
        }
        return render(request, "web_container/sign_result.html", context)  # возвращаем шаблон с сообщением об ошибке

    signature_path = build_signature_path(file_path, USER_SIGNATURES_DIR)

    if request.method == "GET" and signature_path.exists():  # если подпись уже существует и это GET-запрос
        context = {
            "file_name": file_name,
            "signature_name": signature_path.name,
        }
        return render(request, "web_container/sign_confirm_overwrite.html", context)  # возвращаем шаблон с подтверждением перезаписи подписи

    result = sign_file_with_result(file_path, overwrite=overwrite)  # подписываем файл и получаем результат операции

    context = {
        "result": result,
    }
    return render(request, "web_container/sign_result.html", context)  # возвращаем шаблон с результатом подписания


def verify_view(request):  # представление для проверки файла
    prepare_directories()

    if request.method == "POST":  # если запрос является POST-запросом (подтверждение перемещения в карантин)
        file_name = request.POST.get("file") # получаем имя файла из POST-параметров
        move_to_quarantine_confirmed = request.POST.get("move_to_quarantine") == "yes"  # проверяем, подтверждено ли перемещение в карантин
    else:
        file_name = request.GET.get("file")  # получаем имя файла из GET-параметров
        move_to_quarantine_confirmed = False  # по умолчанию не подтверждаем перемещение в карантин

    if not file_name:
        return redirect("index")

    file_path = USER_UPDATES_DIR / file_name

    if not file_path.exists():  # если указанный файл не существует
        context = {
            "error": f"Файл {file_name} не найден.",
        }
        return render(request, "web_container/verify_result.html", context)  # возвращаем шаблон с сообщением об ошибке

    if request.method == "POST" and move_to_quarantine_confirmed:  # если подтверждено перемещение в карантин
        try:
            quarantine_file_path, quarantine_signature_path, moved_signature = move_to_quarantine(file_path)  # перемещаем файл и подпись в карантин

            context = {
                "quarantine_result": {
                    "file_name": quarantine_file_path.name,
                    "moved_signature": moved_signature,
                    "signature_name": quarantine_signature_path.name,
                }
            }
            return render(request, "web_container/quarantine_move_result.html", context)  # возвращаем шаблон с результатом перемещения в карантин

        except Exception as error:  # перехватываем любые ошибки при перемещении в карантин
            context = {
                "error": f"Ошибка при перемещении в карантин: {error}",
            }
            return render(request, "web_container/quarantine_move_result.html", context)  # возвращаем шаблон с сообщением об ошибке

    result = verify_file(file_path)  # проверяем файл и получаем результат проверки

    if result["status"] == "REJECTED":  # если файл отклонён при проверке
        context = {
            "result": result,
            "file_name": file_name,
        }
        return render(request, "web_container/confirm_quarantine.html", context)  # возвращаем шаблон с подтверждением перемещения в карантин

    context = {
        "result": result,
    }
    return render(request, "web_container/verify_result.html", context)  # возвращаем шаблон с результатом проверки


def compromise_view(request):  # представление для компрометации файла
    prepare_directories()

    if request.method == "POST":
        file_name = request.POST.get("file")
        action = request.POST.get("action")
        confirmed = request.POST.get("confirmed") == "yes"
    else:
        file_name = request.GET.get("file")
        action = request.GET.get("action")
        confirmed = False

    if not file_name:
        return redirect("index")

    file_path = USER_UPDATES_DIR / file_name
    signature_path = build_signature_path(file_path, USER_SIGNATURES_DIR)

    if not file_path.exists(): # если указанный файл не существует
        context = {
            "error": f"Файл {file_name} не найден.",
        }
        return render(request, "web_container/compromise_result.html", context)  # возвращаем шаблон с сообщением об ошибке

    if not action:  # если тип операции компрометации не указан
        context = {
            "file_name": file_name,
            "signature_exists": signature_path.exists(),
            "signature_name": signature_path.name,
        }
        return render(request, "web_container/compromise_menu.html", context)  # возвращаем шаблон с выбором типа операции компрометации

    action_titles = {  # словарь с названиями операций компрометации для отображения пользователю
        "modify_file": "Изменение содержимого файла",
        "delete_signature": "Удаление подписи",
        "clear_signature": "Очистка подписи",
    }

    if action not in action_titles:  # если указан некорректный тип операции компрометации
        context = {
            "error": "Некорректный тип операции компрометации.",
        }
        return render(request, "web_container/compromise_result.html", context)  # возвращаем шаблон с сообщением об ошибке

    if not confirmed:  # если операция компрометации не подтверждена
        context = {
            "file_name": file_name,
            "action": action,
            "action_title": action_titles[action],
            "signature_exists": signature_path.exists(),
            "signature_name": signature_path.name,
        }
        return render(request, "web_container/compromise_confirm.html", context)  # возвращаем шаблон с подтверждением операции компрометации

    result = compromise_file_with_result(file_path, signature_path, action)  # выполняем операцию компрометации и получаем результат

    context = {
        "result": result,
    }
    return render(request, "web_container/compromise_result.html", context)  # возвращаем шаблон с результатом операции компрометации


def quarantine_view(request):  # представление для отображения содержимого карантина
    prepare_directories()

    quarantine_files = get_quarantine_files()  # получаем список файлов в карантине
    quarantine_signatures = get_quarantine_signatures()  # получаем список подписей в карантине

    context = {
        "quarantine_files": quarantine_files,
        "quarantine_signatures": quarantine_signatures,
    }
    return render(request, "web_container/quarantine.html", context)  # возвращаем шаблон с содержимым карантина


def clear_quarantine_view(request):  # представление для очистки карантина
    prepare_directories()

    if request.method == "POST":
        confirmed = request.POST.get("confirmed") == "yes"

        if confirmed:  # если очистка карантина подтверждена
            deleted_files_count, deleted_signatures_count = clear_quarantine()  # очищаем карантин и получаем количество удалённых файлов и подписей
            context = {
                "deleted_files_count": deleted_files_count,
                "deleted_signatures_count": deleted_signatures_count,
            }
            return render(request, "web_container/quarantine_clear_result.html", context)  # возвращаем шаблон с результатом очистки карантина

    quarantine_files = get_quarantine_files()  # получаем список файлов в карантине
    quarantine_signatures = get_quarantine_signatures() # получаем список подписей в карантине

    context = {
        "quarantine_files": quarantine_files,
        "quarantine_signatures": quarantine_signatures,
    }
    return render(request, "web_container/quarantine_clear_confirm.html", context)  # возвращаем шаблон с подтверждением очистки карантина


def simulation_view(request):  # представление для запуска симуляции проверки обновлений
    prepare_directories()

    if request.method == "POST":
        try:
            simulation_data = run_simulation()  # запускаем симуляцию и получаем её результаты

            context = {
                "results": simulation_data["results"],
                "summary": simulation_data["summary"],
                "result_file_name": simulation_data["result_file_name"],
                "bar_chart_url": f"/media/simulation/results/{SIMULATION_BAR_CHART_NAME}",
                "pie_chart_url": f"/media/simulation/results/{SIMULATION_PIE_CHART_NAME}",
            }
            return render(request, "web_container/simulation_result.html", context)  # возвращаем шаблон с результатами симуляции

        except Exception as error:  # перехватываем любые ошибки при выполнении симуляции
            context = {
                "error": f"Ошибка при выполнении симуляции: {error}",
                "file_count": SIMULATION_FILE_COUNT,
                "compromised_count": SIMULATION_COMPROMISED_COUNT,
                "missing_signature_count": SIMULATION_MISSING_SIGNATURE_COUNT,
            }
            return render(request, "web_container/simulation_start.html", context)  # возвращаем шаблон с сообщением об ошибке

    context = {
        "file_count": SIMULATION_FILE_COUNT,
        "compromised_count": SIMULATION_COMPROMISED_COUNT,
        "missing_signature_count": SIMULATION_MISSING_SIGNATURE_COUNT,
    }
    return render(request, "web_container/simulation_start.html", context)  # возвращаем шаблон с параметрами симуляции


def clear_simulation_view(request):  # представление для очистки данных симуляции
    prepare_directories()

    if request.method == "POST":
        confirmed = request.POST.get("confirmed") == "yes"  # проверяем, подтверждена ли очистка симуляции

        if confirmed:
            clear_simulation_directories()  # очищаем директории симуляции
            context = {
                "message": "Временные файлы симуляции удалены. JSON-лог сохранен.",
            }
            return render(request, "web_container/simulation_clear_result.html", context)  # возвращаем шаблон с результатом очистки

    context = {}
    return render(request, "web_container/simulation_clear_confirm.html", context)  # возвращаем шаблон с подтверждением очистки симуляции