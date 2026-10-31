from __future__ import annotations

import re
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT.parent / "Учеба" / "ПТК" / "Проект" / "подготовка к экзу (VMs)"
DOCS = ROOT / "docs"

CHAPTERS = [
    ("chapter-1", "1. Базовая настройка сетей (Задание 1 ДЭ)", [
        "IP-адресация тема", "Базовая настройка тема", "Коммутация L2 тема",
        "Маршрутизация тема", "Туннелирование тема", "Трансляция адресов",
        "Служба DHCP", "Служба DNS", "Удаленный доступ", "Нейрохрючевый пример тут",
    ]),
    ("chapter-2", "2. Сетевое администрирование (Задание 2 ДЭ)", [
        "Виртуализация и гипервизоры", "Администрирование Linux",
        "Windows Server и Active Directory", "Файловые и печатные службы",
        "Веб-служба", "Службы электронной почты",
        "DNS и DHCP в администрировании", "Контейнеры и облака",
    ]),
    ("chapter-3", "3. Эксплуатация и мониторинг (Задание 3 ДЭ + МДК.03.01)", [
        "Мониторинг инфраструктуры", "Сбор и анализ логов",
        "Диагностика сети и анализ трафика", "Автоматизация и IaC",
        "Обновление и сопровождение систем", "Резервное копирование и восстановление",
        "Инвентаризация и документация", "ITSM и обработка инцидентов",
    ]),
    ("chapter-4", "4. Промышленные сети и АСУ ТП (МДК.03.02)", [
        "АСУ ТП и модель уровней (Purdue)", "ПЛК, HMI и SCADA",
        "Промышленный Ethernet", "Полевые шины и последовательные интерфейсы",
        "Протоколы АСУ ТП", "Промышленная коммутация и резервирование",
        "Сегментация и защита промышленных сетей", "Монтаж, среда и надёжность",
    ]),
    ("chapter-5", "5. Безопасность инфраструктуры (МДК.03.03)", [
        "Основы ИБ и модель угроз", "Защита периметра и межсетевые экраны",
        "VPN и защищённые каналы", "Безопасность канального уровня",
        "Аутентификация и управление доступом", "Криптография и PKI",
        "Защита хостов и ОС", "Мониторинг ИБ и реагирование",
        "Нормативная база РФ в области ИБ",
    ]),
]


def display_name(name: str) -> str:
    """Keep Obsidian filenames intact while hiding placeholder suffixes."""
    return name.removesuffix(" тема")


def normalize_display_names(text: str) -> str:
    text = re.sub(
        r"^(#+\s+)(.+?) тема\s*$",
        lambda match: match.group(1) + match.group(2),
        text,
        flags=re.MULTILINE,
    )
    return re.sub(r"\[([^\]]+?) тема\](?=\()", r"[\1]", text)


def convert_wikilinks(text: str, available: set[str]) -> str:
    def replace(match: re.Match[str]) -> str:
        target = match.group(1).strip()
        label = match.group(2).strip() if match.group(2) else display_name(target)
        anchor = ""
        if "#" in target:
            target, anchor = target.split("#", 1)
            anchor = "#" + anchor.lower().replace(" ", "-")
        if target in available:
            return f"[{label}]({display_name(target)}.md{anchor})"
        return f"**{label}**"

    return re.sub(r"\[\[([^\]|]+)(?:\|([^\]]+))?\]\]", replace, text)


def ensure_title(text: str, title: str) -> str:
    if re.search(r"^#\s+", text, flags=re.MULTILINE):
        return text
    lines = text.splitlines()
    if lines and lines[0].strip() and not lines[0].startswith(("```", "<", "-", "|")):
        intro = lines.pop(0).strip()
        return f"# {title}\n\n{intro}\n" + "\n".join(lines).lstrip()
    return f"# {title}\n\n{text.lstrip()}"


def main() -> None:
    if not SOURCE.exists():
        raise SystemExit(f"Source folder not found: {SOURCE}")

    for slug, source_name, topics in CHAPTERS:
        src = SOURCE / source_name
        dst = DOCS / "documentation" / slug
        if dst.exists():
            shutil.rmtree(dst)
        dst.mkdir(parents=True)
        available = {p.stem for p in src.glob("*.md")}

        overview_name = source_name.removeprefix(source_name.split(". ", 1)[0] + ". ")
        overview = src / f"{overview_name}.md"
        if overview.exists():
            text = overview.read_text(encoding="utf-8-sig")
            text = normalize_display_names(convert_wikilinks(text, available))
            text = ensure_title(text, source_name)
        else:
            text = f"# {source_name}\n"

        text += "\n\n## Темы главы\n\n"
        text += "\n".join(
            f"- [{display_name(topic)}]({display_name(topic)}.md)" for topic in topics
        )
        (dst / "index.md").write_text(text.rstrip() + "\n", encoding="utf-8")

        for topic in topics:
            source_file = src / f"{topic}.md"
            if not source_file.exists():
                raise SystemExit(f"Missing source: {source_file}")
            text = source_file.read_text(encoding="utf-8-sig")
            text = normalize_display_names(convert_wikilinks(text, available))
            text = ensure_title(text, display_name(topic))
            (dst / f"{display_name(topic)}.md").write_text(
                text.rstrip() + "\n", encoding="utf-8"
            )

    print("Documentation synchronized successfully.")


if __name__ == "__main__":
    main()
