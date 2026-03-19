# PDF → LEDES 98B Converter

Приложение для конвертации PDF-инвойсов в формат [LEDES 98B](https://www.ledes.org/).

## Требования

- Python 3.10+

## Установка зависимостей

```bash
pip install -r requirements.txt
```

## Запуск

**Через bat-файл (рекомендуется):**

```bash
make pdf to ledes
```

**Или напрямую через Python:**

```bash
python main.py
```

## Использование

1. Положите PDF-файлы в папку `Desktop\PDF_Input`
2. Запустите приложение
3. При необходимости измените папки через кнопку **Browse…**
4. Нажмите **Convert**
5. Готовые `.ledes` файлы появятся в папке `Desktop\LEDES_Output`

## Структура проекта

```
pdf_ledes_loading/
├── config.py           — пути по умолчанию и колонки LEDES 98B
├── pdf_parser.py       — извлечение данных из PDF
├── ledes_converter.py  — конвертация в формат LEDES 98B
├── main.py             — GUI-приложение
├── run.bat             — скрипт запуска
└── requirements.txt    — зависимости
```

## Выходной формат

Файл LEDES 98B — текстовый pipe-delimited формат:

```
LEDES1998B[]
INVOICE_DATE|INVOICE_TOTAL|MATTER_ID|CLIENT_ID|...|CLIENT_MATTER_ID[]
20240115|5000.00|MATTER-001|CLIENT|...|CLIENT-MATTER-001[]
```
