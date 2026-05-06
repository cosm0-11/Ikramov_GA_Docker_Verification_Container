import binascii
import ed25519

from core.config import KEYS_DIR, PUBLIC_KEY_PATH


def main():
    KEYS_DIR.mkdir(parents=True, exist_ok=True)  # создаём каталог для хранения ключей

    signing_key, verifying_key = ed25519.create_keypair()  # генерируем новую пару ключей

    private_seed = signing_key.to_seed()  # получаем приватный ключ в виде seed-значения
    private_seed_hex = binascii.hexlify(private_seed).decode("utf-8")  # преобразуем seed в hex-строку
    public_key_hex = verifying_key.to_ascii(encoding="hex").decode("utf-8")  # преобразуем открытый ключ в hex-строку

    PUBLIC_KEY_PATH.write_text(public_key_hex, encoding="utf-8")  # сохраняем открытый ключ в файл

    print("Новая пара ключей создана.")
    print("Приватный ключ для Replit Secrets (PRIVATE_KEY_HEX):")
    print(private_seed_hex)
    print(f"Публичный ключ сохранен в {PUBLIC_KEY_PATH}")


if __name__ == "__main__":
    main()