"""
Интеграционные тесты веб-контейнера верификации обновлений.
Идентификаторы TC-XX соответствуют спецификации тестов по ГОСТ Р 56920.
"""

import os
import pytest
import requests
import urllib3
import time

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BASE_URL = os.environ.get("BASE_URL", "https://192.168.49.2:30443")
HTTP_URL = os.environ.get("HTTP_URL", "http://192.168.49.2:30080")

SESSION = requests.Session()
SESSION.verify = False

TEST_FILENAME = f"tc_test_{int(time.time())}"


def _csrf(path="/create/"):
    r = SESSION.get(f"{BASE_URL}{path}", timeout=10)
    return r.cookies.get("csrftoken", "")


@pytest.fixture(scope="session", autouse=True)
def cleanup_after_session():
    yield

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


def test_tc01_system_availability():
    response = SESSION.get(f"{BASE_URL}/", timeout=10)
    assert response.status_code == 200, (
        f"TC-01 FAILED: ожидался HTTP 200, получен {response.status_code}"
    )


def test_tc02_http_to_https_redirect():
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


def test_tc03_static_files_served_by_nginx():
    response = SESSION.get(f"{BASE_URL}/static/css/style.css", timeout=10)
    assert response.status_code == 200, (
        f"TC-03 FAILED: ожидался HTTP 200, получен {response.status_code}"
    )
    assert "text/css" in response.headers.get("Content-Type", ""), (
        "TC-03 FAILED: Content-Type не является text/css"
    )


def test_tc04_file_creation():
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


def test_tc05_file_signing():
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


def test_tc06_verify_valid_file():
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


def test_tc07_file_compromise():
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


def test_tc08_verify_compromised_file():
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


def test_tc09_quarantine_page():
    response = SESSION.get(f"{BASE_URL}/quarantine/", timeout=10)
    assert response.status_code == 200, (
        f"TC-09 FAILED: ожидался HTTP 200, получен {response.status_code}"
    )


def test_tc10_simulation():
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


def test_tc11_media_charts_served_by_nginx():
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
