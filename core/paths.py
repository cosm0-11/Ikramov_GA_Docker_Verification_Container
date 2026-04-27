from core.config import (  # импортируем набор путей к рабочим директориям из файла конфигурации
    DATA_DIR,
    KEYS_DIR,
    USER_DIR,
    USER_UPDATES_DIR,
    USER_SIGNATURES_DIR,
    SIM_DIR,
    SIM_UPDATES_DIR,
    SIM_SIGNATURES_DIR,
    SIM_RESULTS_DIR,
    QUARANTINE_DIR,
    QUARANTINE_UPDATES_DIR,
    QUARANTINE_SIGNATURES_DIR,
)


def prepare_directories():  # функция подготовки (создания) всех необходимых каталогов проекта
    directories = [  # формируем единый список всех директорий, которые должны существовать на диске
        DATA_DIR,
        KEYS_DIR,
        USER_DIR,
        USER_UPDATES_DIR,
        USER_SIGNATURES_DIR,
        SIM_DIR,
        SIM_UPDATES_DIR,
        SIM_SIGNATURES_DIR,
        SIM_RESULTS_DIR,
        QUARANTINE_DIR,
        QUARANTINE_UPDATES_DIR,
        QUARANTINE_SIGNATURES_DIR,
    ]

    for directory in directories:  # поочередно обрабатываем каждый путь из списка
        directory.mkdir(parents=True, exist_ok=True)  # создаём каталог вместе с родителями, если он ещё не существует