# Запуск бота @hot_makler_fukuok_bot

## Шаг 1 — Установить Python 3.11

Скачайте и установите Python с официального сайта:
https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe

**Важно:** при установке отметьте галочку "Add Python to PATH"

---

## Шаг 2 — Узнать ваш Telegram ID

Напишите боту @userinfobot в Telegram — он ответит вашим ID.
Вставьте его в файл `.env` в строку `REALTOR_TG_ID=`.

---

## Шаг 3 — Установить зависимости

Откройте командную строку в папке проекта и выполните:

```
cd C:\Users\geter\projects\hot-makler-bot
pip install -e .
```

---

## Шаг 4 — Запустить бота (без Google Sheets)

```
cd C:\Users\geter\projects\hot-makler-bot
python -m src.bot.main
```

Бот запустится с тестовыми объектами (3 апартамента на Фукуоке).

---

## Шаг 5 — Подключить Google Sheets (необязательно для теста)

### 5.1 Создать таблицу

Создайте новую Google Таблицу по адресу: https://sheets.google.com

Первый лист переименуйте в **Properties**, добавьте заголовки в первую строку:

```
id | district | rooms | has_kitchen | bathrooms | has_ac | max_guests | price_per_day | currency | photos_url | description_ru | realtor_whatsapp | unavailable_dates | status
```

Пример строки данных:
```
A001 | Дуонг-Донг | 2 | TRUE | 1 | TRUE | 4 | 55 | USD | https://drive.google.com/... | Уютные апартаменты... | +84901234567 | | active
```

Формат занятых дат: `2026-05-01:2026-05-07,2026-05-15:2026-05-20`

### 5.2 Создать Service Account

1. Зайдите на https://console.cloud.google.com
2. Создайте проект → включите Google Sheets API и Google Drive API
3. Создайте Service Account → скачайте JSON-ключ
4. Сохраните JSON-файл как `credentials.json` в папке проекта
5. В Google Sheets нажмите «Поделиться» → добавьте email Service Account (из JSON-файла) с правами редактора

### 5.3 Добавить ID таблицы в .env

ID таблицы — это длинная строка в URL:
`https://docs.google.com/spreadsheets/d/ВОТ_ЭТО_ИДЕНТИФИКАТОР/edit`

Вставьте его в `.env`:
```
GOOGLE_SHEETS_ID=ВОТ_ЭТО_ИДЕНТИФИКАТОР
```

---

## Структура проекта

```
hot-makler-bot/
├── src/
│   ├── bot/
│   │   ├── main.py          ← точка входа
│   │   ├── handlers/        ← логика диалога
│   │   ├── keyboards/       ← кнопки
│   │   ├── states.py        ← FSM состояния
│   │   └── texts.py         ← все тексты бота
│   ├── core/
│   │   ├── models.py        ← Pydantic модели
│   │   ├── search.py        ← фильтрация + альтернативы
│   │   └── pricing.py       ← расчёт цены
│   ├── integrations/
│   │   ├── sheets.py        ← Google Sheets
│   │   ├── whatsapp.py      ← уведомления риелтору
│   │   └── scheduler.py     ← синхронизация раз в 8ч
│   └── storage/
│       ├── db.py            ← SQLite
│       └── repositories.py  ← CRUD
├── .env                     ← токены (не коммитить!)
├── .env.example             ← шаблон
└── pyproject.toml           ← зависимости
```

---

## Как работает бот

1. Клиент пишет `/start`
2. Выбирает даты, гостей, район, комнаты, санузлы, кухню, кондиционер, бюджет
3. Бот показывает подходящие объекты с ценой
4. Клиент нажимает «❤️ Интересно» → вводит имя и контакт
5. Бот уведомляет вас в Telegram с кнопкой «Открыть WhatsApp»
6. Вы звоните клиенту одним тапом
