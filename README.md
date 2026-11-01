# Информация

Сайт является продуктом проекта

## Локальный запуск

```bash
python -m pip install -r requirements.txt
python scripts/sync_docs.py
python -m mkdocs serve
```

Сайт откроется на <http://127.0.0.1:8000>.

## Публикация

Репозиторий: <https://github.com/imTopTuk/dem-exam-docs>

Публичный сайт: <https://imtoptuk.github.io/dem-exam-docs/>

Workflow `.github/workflows/deploy.yml` автоматически собирает и публикует сайт после изменений в ветке `main`.

## Обновление материалов

После изменений в Obsidian выполните:

```bash
python scripts/sync_docs.py
```

Скрипт копирует главы 1–5 и преобразует Obsidian-ссылки, не меняя исходные заметки.
