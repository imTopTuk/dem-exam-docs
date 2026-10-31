# Администрирование Linux

пользователи, права, sudo, systemd, пакеты
### Администрирование Linux

Пользователи и группы хранятся в `/etc/passwd`, `/etc/shadow`, `/etc/group`. Пароли хешируются в `/etc/shadow` (только root читает).

<span style="color: 00cc18">Ключевые команды:</span>

- `useradd -m -s /bin/bash bob`, `passwd bob` — создать пользователя/пароль;
- `usermod -aG sudo bob`, `groups bob` — добавить в группу;
- `userdel -r bob` — удалить вместе с домашним каталогом;
- `id bob` — UID/GID и группы.

### Права доступа

Модель **ugo/rwx**: владелец (u), группа (g), остальные (o) — чтение (4), запись (2), выполнение (1).

| Запись | Права | Значение              |
| ------ | ----- | --------------------- |
| 644    | rw-r--r-- | файл: владелец пишет, все читают |
| 755    | rwxr-xr-x | каталоги, скрипты      |
| 600    | rw------- | приватные файлы, ключи |
| 700    | rwx------ | приватные каталоги `.ssh` |

- `chmod 640 file`, `chmod u+x script.sh`;
- `chown user:group file`, `chgrp`;
- **специальные биты**: `setuid` (s), `setgid` (s), `sticky` (t) — например, `/tmp` (1777);
- **ACL**: `setfacl -m u:bob:rw file`, `getfacl file` — права сверх ugo;
- **sudo**: `/etc/sudoers` (править только `visudo`), `bob ALL=(ALL) NOPASSWD:ALL`.

### Управление службами (systemd)

- `systemctl start/stop/restart/status sshd`;
- `systemctl enable/disable nginx` — автозапуск;
- `systemctl daemon-reload` — после правок unit-файлов;
- `systemctl list-units --failed` — что упало;
- юниты в `/etc/systemd/system/*.service`;
- журнал: `journalctl -u nginx -f` (см. тему логирования).

### Пакеты и репозитории

| Семейство     | Менеджер            | Установка           |
| ------------- | ------------------- | ------------------- |
| RedOS/Alt     | rpm + dnf/apt (Alt) | `dnf install nginx` |
| Debian/Ubuntu | dpkg + apt          | `apt install nginx` |

- `dnf update`, `apt update && apt upgrade`;
- репозитории: `/etc/yum.repos.d/*.repo`, `/etc/apt/sources.list`;
- локальная установка: `rpm -Uvh pkg.rpm`, `dpkg -i pkg.deb`;
- `dnf provides /usr/sbin/sshd` — какой пакет даёт файл.

### Типичные ошибки на экзамене:

- `chmod 777` «чтобы работало» — дыра в безопасности;
- правят `/etc/sudoers` напрямую, а не `visudo` — синтаксическая ошибка ломает sudo;
- путают владельца и группу в `chown` (порядок `user:group`);
- `systemctl start` без `enable` — после перезагрузки служба не поднимется;
- забывают `daemon-reload` после создания unit-файла;
- меняют права на `.ssh` (нужно `700` на каталог и `600` на ключи), иначе SSH отказывает;
- не смотрят `journalctl`/логи — гадают вместо причины;
- обновляют без бэкапа и снапшота — откатиться нечем.
