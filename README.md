# xminer-api Web UI

Python клієнт та веб-інтерфейс для API майнера (anthill.farm / xminer-api).

## Встановлення

```bash
pip install -r requirements.txt
```

## Конфігурація

Налаштування зберігаються у `config.json`:

```json
{
  "miner_host": "192.168.1.147",
  "miner_port": 80,
  "miner_password": "admin",
  "miner_api_key": null,
  "server_host": "0.0.0.0",
  "server_port": 8000
}
```

- `miner_password` — пароль від веб-інтерфейсу майнера (Vnish)
- `miner_api_key` — альтернатива паролю (32-символьний ключ)
- `server_host` / `server_port` — адреса веб-сервера

## Запуск

```bash
python main.py
```

Сервер запуститься на `http://0.0.0.0:8000`. Відкрий у браузері.

### Аргументи

```bash
python main.py --config my-config.json
python main.py --host 127.0.0.1 --port 9000
```

## Веб-інтерфейс

- **Хешрейт** — realtime / average / nominal
- **Потужність** — W, ефективність J/TH, HW помилки
- **Температури** — chip / PCB
- **Охолодження** — fan duty %, RPM кожного вентилятора
- **Керування майнінгом** — кнопки Старт / Пауза / Resume / Restart / Стоп
- **Пресети автотюну** — вибір та застосування пресета
- **Пули** — список пулів зі статусом та статистикою
- **Система** — перезавантаження майнера, перегляд логів

Автооновлення кожні 10 секунд.

## Python клієнт (без сервера)

```python
from xminer_client import XMinerClient

c = XMinerClient("192.168.1.147")
c.unlock("admin")

summary = c.get_summary()
print(summary.miner.hr_realtime)

c.mining_start()
c.save_settings({"miner": {"overclock": {"preset": "3080"}}})
```

## Структура

```
miner-api/
├── config.json            # Налаштування (пароль, хост, порт)
├── requirements.txt
├── main.py                # FastAPI сервер + веб-інтерфейс
├── README.md
└── xminer_client/
    ├── __init__.py
    ├── client.py          # HTTP клієнт з усіма ендпоінтами
    └── models.py          # Dataclass-моделі даних
```
