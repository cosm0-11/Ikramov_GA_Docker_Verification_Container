from pathlib import Path  # импортируем класс Path для работы с путями и файловой системой


def get_files_from_directory(directory: Path):  # функция получения списка файлов из указанной директории
    files = sorted(directory.glob("*"))  # получаем все объекты в директории и сортируем их по имени
    return [file_path for file_path in files if file_path.is_file()]  # оставляем только файлы, исключая вложенные каталоги


def build_signature_path(file_path: Path, signatures_dir: Path):  # функция построения пути к файлу подписи для заданного файла
    return signatures_dir / f"{file_path.stem}.sig"  # формируем путь к подписи по имени файла без исходного расширения