from pathlib import Path  # импортируем класс Path для работы с путями в файловой системе

PROJECT_ROOT = Path(__file__).resolve().parent.parent  # определяем корневую директорию проекта относительно текущего файла

DATA_DIR = PROJECT_ROOT / "data"  # базовая директория для всех рабочих данных контейнера
KEYS_DIR = PROJECT_ROOT / "keys"  # директория для хранения файлов с криптографическими ключами

USER_DIR = DATA_DIR / "user"  # директория для пользовательских данных
USER_UPDATES_DIR = USER_DIR / "updates"  # каталог с пользовательскими файлами обновлений
USER_SIGNATURES_DIR = USER_DIR / "signatures"  # каталог с пользовательскими файлами подписей

SIM_DIR = DATA_DIR / "simulation"  # директория для данных, связанных с симуляцией
SIM_UPDATES_DIR = SIM_DIR / "updates"  # каталог с файлами обновлений, используемыми в симуляции
SIM_SIGNATURES_DIR = SIM_DIR / "signatures"  # каталог с файлами подписей для симулируемых обновлений
SIM_RESULTS_DIR = SIM_DIR / "results"  # каталог для сохранения результатов симуляции (графики, отчёты)

QUARANTINE_DIR = DATA_DIR / "quarantine"  # директория карантинной зоны
QUARANTINE_UPDATES_DIR = QUARANTINE_DIR / "updates"  # каталог с файлами обновлений, помещёнными в карантин
QUARANTINE_SIGNATURES_DIR = QUARANTINE_DIR / "signatures"  # каталог с файлами подписей, помещёнными в карантин

PUBLIC_KEY_PATH = KEYS_DIR / "public_key.hex"  # путь к открытому ключу проверки подписи в виде текстового файла
PRIVATE_KEY_ENV_NAME = "PRIVATE_KEY_HEX"  # имя переменной окружения, из которой считывается закрытый ключ

MAX_USER_FILES = 10  # максимальное количество пользовательских файлов, разрешённых в каталоге
MAX_USER_FILE_SIZE_BYTES = 256 * 1024  # максимальный размер одного пользовательского файла в байтах
MAX_FILENAME_LENGTH = 50  # максимальная допустимая длина имени файла
MAX_FILE_CONTENT_LENGTH = 5000  # максимальная допустимая длина текстового содержимого файла

SIMULATION_FILE_COUNT = 10  # количество файлов обновлений, обрабатываемых в одной симуляции
SIMULATION_COMPROMISED_COUNT = 5  # количество файлов, помечаемых как скомпрометированные в сценарии симуляции
SIMULATION_MISSING_SIGNATURE_COUNT = 2  # количество файлов без подписи в сценарии симуляции

SIMULATION_BAR_CHART_NAME = "simulation_status_bar.png"  # имя файла с диаграммой типа "столбчатая" для результатов симуляции
SIMULATION_PIE_CHART_NAME = "simulation_status_pie.png"  # имя файла с круговой диаграммой распределения результатов симуляции