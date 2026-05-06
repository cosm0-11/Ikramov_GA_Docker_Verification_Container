"""
Интеграционные тесты веб-контейнера верификации обновлений.
Идентификаторы TC-XX соответствуют спецификации тестов по ГОСТ Р 56920.
"""

import pytest
import requests
import urllib3
import time

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BASE_URL = "https://127.0.0.1"
HTTP_URL = "http://127.0.0.1"

SESSION = requests.Session()
SESSION.verify = False

TEST_FILENAME = f"tc_test_{int(time.time())}"


def _csrf(path="/create/"):
    r = SESSION.get(f"{BASE_URL}{path}", timeout=10)
    return r.cookies.get("csrftoken", "")


@pytest.fixture(scope="session", autouse=True)
def cleanup_after_session():
    """
    Фикстура очистки: после завершения всей сессии тестов удаляет
    тестовый файл из user/updates и очищает директории симуляции.
    """
    yield

    # 1. Удаление тестового файла — GET для CSRF, затем POST с подтверждением
    try:
        get_resp = SESSION.get(
            f"{BASE_URL}/delete/",
            params={"file": f"{TEST_FILENAME}.txt"},
            timeout=10,
        )
        csrf = get_resp.cookies.get("csrftoken", "")
        SESSION.post(
            f"{BASE_URL}/delete/",
            data={
                "file": f"{TEST_FILENAME}.txt",
                "csrfmiddlewaretoken": csrf,
            },
            headers={"Referer": f"{BASE_URL}/delete/"},
            timeout=10,
        )
    except Exception:
        pass

    # 2. Очистка симуляции — GET для CSRF, затем POST с подтверждением
    try:
        get_resp = SESSION.get(f"{BASE_URL}/simulation/clear/", timeout=10)
        csrf = get_resp.cookies.get("csrftoken", "")
        SESSION.post(
            f"{BASE_URL}/simulation/clear/",
            data={
                "confirmed": "yes",
                "csrfmiddlewaretoken": csrf,
            },
            headers={"Referer": f"{BASE_URL}/simulation/clear/"},
            timeout=10,
        )
    except Exception:
        pass


# ---------------------------------------------------------------------------
# TC-01: Доступность системы
# ---------------------------------------------------------------------------
def test_tc01_system_availability():
    """
    TC-01. Предусловие: все три контейнера запущены.
    Ожидаемый результат: GET / возвращает HTTP 200.
    Подтверждает: связь nginx -> web -> db установлена корректно.
    """
    response = SESSION.get(f"{BASE_URL}/", timeout=10)
    assert response.status_code == 200, (
        f"TC-01 FAILED: ожидался HTTP 200, получен {response.status_code}"
    )


# ---------------------------------------------------------------------------
# TC-02: Редирект HTTP -> HTTPS
# ---------------------------------------------------------------------------
def test_tc02_http_to_https_redirect():
    """
    TC-02. Предусловие: контейнер nginx запущен.
    Ожидаемый результат: GET http://127.0.0.1/ возвращает HTTP 301
    с заголовком Location, содержащим https://.
    Подтверждает: конфигурация TLS в nginx корректна.
    """
    response = requests.get(
        f"{HTTP_URL}/",
        allow_redirects=False,
        timeout=10,
        verify=False,
    )
    assert response.status_code == 301, (
        f"TC-02 FAILED: ожидался HTTP 301, получен {response.status_code}"
    )
    assert "https://" in response.headers.get("Location", ""), (
        "TC-02 FAILED: заголовок Location не содержит https://"
    )


# ---------------------------------------------------------------------------
# TC-03: Раздача статики через nginx
# ---------------------------------------------------------------------------
def test_tc03_static_files_served_by_nginx():
    """
    TC-03. Предусловие: collectstatic выполнен, static_volume подключён.
    Ожидаемый результат: GET /static/css/style.css возвращает HTTP 200
    с Content-Type text/css.
    Подтверждает: nginx отдаёт статику напрямую, минуя Django.
    """
    response = SESSION.get(f"{BASE_URL}/static/css/style.css", timeout=10)
    assert response.status_code == 200, (
        f"TC-03 FAILED: ожидался HTTP 200, получен {response.status_code}"
    )
    assert "text/css" in response.headers.get("Content-Type", ""), (
        "TC-03 FAILED: Content-Type не является text/css"
    )


# ---------------------------------------------------------------------------
# TC-04: Создание файла
# ---------------------------------------------------------------------------
def test_tc04_file_creation():
    """
    TC-04. Предусловие: система доступна, файл TEST_FILENAME не существует.
    Ожидаемый результат: POST /create/ с уникальным именем возвращает HTTP 200
    и страницу со статусом CREATED.
    Подтверждает: этап создания файла обновления работает корректно.
    """
    csrf = _csrf("/create/")
    response = SESSION.post(
        f"{BASE_URL}/create/",
        data={
            "filename": TEST_FILENAME,
            "content": "Test content for TC-04",
            "mode": "manual",
            "csrfmiddlewaretoken": csrf,
        },
        headers={"Referer": f"{BASE_URL}/create/"},
        timeout=10,
    )
    assert response.status_code == 200, (
        f"TC-04 FAILED: ожидался HTTP 200, получен {response.status_code}"
    )
    assert "CREATED" in response.text, (
        "TC-04 FAILED: статус CREATED не найден в ответе"
    )


# ---------------------------------------------------------------------------
# TC-05: Подпись файла
# ---------------------------------------------------------------------------
def test_tc05_file_signing():
    """
    TC-05. Предусловие: файл TEST_FILENAME создан (TC-04).
    Ожидаемый результат: GET /sign/?file=TEST_FILENAME.txt возвращает HTTP 200.
    Подтверждает: механизм формирования подписи Ed25519 работает корректно.
    """
    response = SESSION.get(
        f"{BASE_URL}/sign/",
        params={"file": f"{TEST_FILENAME}.txt"},
        timeout=10,
    )
    assert response.status_code == 200, (
        f"TC-05 FAILED: ожидался HTTP 200, получен {response.status_code}"
    )
    assert TEST_FILENAME in response.text, (
        "TC-05 FAILED: имя файла не найдено в ответе страницы подписи"
    )


# ---------------------------------------------------------------------------
# TC-06: Верификация корректного файла
# ---------------------------------------------------------------------------
def test_tc06_verify_valid_file():
    """
    TC-06. Предусловие: файл TEST_FILENAME подписан (TC-05).
    Ожидаемый результат: GET /verify/?file=TEST_FILENAME.txt возвращает HTTP 200
    и статус ACCEPTED.
    Подтверждает: верификация корректно подписанного файла проходит успешно.
    """
    response = SESSION.get(
        f"{BASE_URL}/verify/",
        params={"file": f"{TEST_FILENAME}.txt"},
        timeout=10,
    )
    assert response.status_code == 200, (
        f"TC-06 FAILED: ожидался HTTP 200, получен {response.status_code}"
    )
    assert "ACCEPTED" in response.text, (
        "TC-06 FAILED: статус ACCEPTED не найден — верификация корректного файла не прошла"
    )


# ---------------------------------------------------------------------------
# TC-07: Компрометация файла
# ---------------------------------------------------------------------------
def test_tc07_file_compromise():
    """
    TC-07. Предусловие: файл TEST_FILENAME существует и подписан.
    Ожидаемый результат: POST /compromise/ с action=modify_file возвращает HTTP 200.
    Подтверждает: механизм имитации нарушения целостности работает корректно.
    """
    get_resp = SESSION.get(
        f"{BASE_URL}/compromise/",
        params={"file": f"{TEST_FILENAME}.txt", "action": "modify_file"},
        timeout=10,
    )
    csrf = get_resp.cookies.get("csrftoken", "")
    response = SESSION.post(
        f"{BASE_URL}/compromise/",
        data={
            "file": f"{TEST_FILENAME}.txt",
            "action": "modify_file",
            "confirmed": "yes",
            "csrfmiddlewaretoken": csrf,
        },
        headers={"Referer": f"{BASE_URL}/compromise/"},
        timeout=10,
    )
    assert response.status_code == 200, (
        f"TC-07 FAILED: ожидался HTTP 200, получен {response.status_code}"
    )


# ---------------------------------------------------------------------------
# TC-08: Верификация скомпрометированного файла (ключевой тест)
# ---------------------------------------------------------------------------
def test_tc08_verify_compromised_file():
    """
    TC-08. Предусловие: файл TEST_FILENAME скомпрометирован (TC-07).
    Ожидаемый результат: GET /verify/?file=TEST_FILENAME.txt возвращает HTTP 200
    и статус REJECTED.
    Подтверждает: система обнаруживает нарушение целостности —
    основное требование безопасности не нарушено.
    """
    response = SESSION.get(
        f"{BASE_URL}/verify/",
        params={"file": f"{TEST_FILENAME}.txt"},
        timeout=10,
    )
    assert response.status_code == 200, (
        f"TC-08 FAILED: ожидался HTTP 200, получен {response.status_code}"
    )
    assert "REJECTED" in response.text, (
        "TC-08 FAILED: статус REJECTED не найден — "
        "система не обнаружила компрометацию. ТРЕБОВАНИЕ НЕ ВЫПОЛНЕНО."
    )


# ---------------------------------------------------------------------------
# TC-09: Доступность карантина
# ---------------------------------------------------------------------------
def test_tc09_quarantine_page():
    """
    TC-09. Предусловие: система доступна.
    Ожидаемый результат: GET /quarantine/ возвращает HTTP 200.
    Подтверждает: раздел управления карантином функционирует.
    """
    response = SESSION.get(f"{BASE_URL}/quarantine/", timeout=10)
    assert response.status_code == 200, (
        f"TC-09 FAILED: ожидался HTTP 200, получен {response.status_code}"
    )


# ---------------------------------------------------------------------------
# TC-10: Симуляция
# ---------------------------------------------------------------------------
def test_tc10_simulation():
    """
    TC-10. Предусловие: система доступна, ключи сгенерированы.
    Ожидаемый результат: POST /simulation/ возвращает HTTP 200
    и страницу с таблицей результатов.
    Подтверждает: сквозной цикл симуляции выполняется без ошибок.
    """
    get_resp = SESSION.get(f"{BASE_URL}/simulation/", timeout=10)
    csrf = get_resp.cookies.get("csrftoken", "")
    response = SESSION.post(
        f"{BASE_URL}/simulation/",
        data={"csrfmiddlewaretoken": csrf},
        headers={"Referer": f"{BASE_URL}/simulation/"},
        timeout=30,
    )
    assert response.status_code == 200, (
        f"TC-10 FAILED: ожидался HTTP 200, получен {response.status_code}"
    )
    assert "ACCEPTED" in response.text or "REJECTED" in response.text, (
        "TC-10 FAILED: таблица результатов симуляции не найдена в ответе"
    )


# ---------------------------------------------------------------------------
# TC-11: Раздача медиафайлов через nginx
# ---------------------------------------------------------------------------
def test_tc11_media_charts_served_by_nginx():
    """
    TC-11. Предусловие: симуляция запущена (TC-10), bind mount ./data подключён.
    Ожидаемый результат: GET /media/simulation/results/simulation_status_bar.png
    возвращает HTTP 200 с Content-Type image/png.
    Подтверждает: nginx отдаёт медиафайлы через bind mount корректно.
    """
    response = SESSION.get(
        f"{BASE_URL}/media/simulation/results/simulation_status_bar.png",
        timeout=10,
    )
    assert response.status_code == 200, (
        f"TC-11 FAILED: ожидался HTTP 200, получен {response.status_code}"
    )
    assert "image/png" in response.headers.get("Content-Type", ""), (
        "TC-11 FAILED: Content-Type не является image/png"
    )
