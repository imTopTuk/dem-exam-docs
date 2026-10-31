# Служба DNS

Прямые (A) и обратные (PTR) зоны, forwarders
### Служба DNS

DNS (Domain Name System) преобразует имена в IP-адреса и наоборот. Работает по **UDP/53** (обычные запросы) и **TCP/53** (крупные ответы, зонные трансферы).

Два типа серверов:

- **клиент/резолвер** — спрашивает у других, кэширует ответы (для него важно поле `forwarders`);
- **авторитативный (authoritative)** — хранит зону и отвечает «как первоисточник»; на нём создают зоны.

### Пространство имён и зоны

Зона — часть домена, за которую сервер отвечает. Записи (RR) внутри зоны:

| Тип   | Назначение                                    | Пример                              |
| ----- | --------------------------------------------- | ----------------------------------- |
| A     | **прямая**: имя → IPv4                         | `srv1 IN A 192.168.1.10`            |
| AAAA  | имя → IPv6                                     | `srv1 IN AAAA 2001:db8::10`         |
| PTR   | **обратная**: IP → имя                         | `10 IN PTR srv1.example.local.`     |
| CNAME | псевдоним                                      | `www IN CNAME srv1`                 |
| MX    | почтовый сервер                                | `@ IN MX 10 mail`                   |
| NS    | DNS-серверы зоны                               | `@ IN NS ns1.example.local.`        |
| SOA   | служебная: серийник, таймеры, первичный сервер | обязательна в каждой зоне           |
| TXT   | произвольный текст (SPF, DKIM, верификации)    | `@ IN TXT "v=spf1 ..."`             |

#### Прямая (forward) зона

Файл `example.local.zone`:

```
$TTL 86400
@   IN SOA ns1.example.local. admin.example.local. (
        2024010101 ; serial — увеличивают при каждом изменении
        3600       ; refresh
        1800       ; retry
        604800     ; expire
        86400 )    ; minimum (negative TTL)
@   IN NS  ns1.example.local.
@   IN A   192.168.1.10
ns1 IN A   192.168.1.10
srv1 IN A  192.168.1.20
www IN CNAME srv1
```

**Serial** обязателен к увеличению при правках — иначе вторичные серверы не увидят изменений.

#### Обратная (reverse) зона

Имя зоны — адрес, записанный **в обратном порядке**:

| Подсеть          | Имя обратной зоны   |
| ---------------- | ------------------- |
| 192.168.1.0/24   | `1.168.192.in-addr.arpa` |
| 10.0.0.0/8       | `10.in-addr.arpa`   |

Пример `1.168.192.in-addr.arpa`:

```
$TTL 86400
@   IN SOA ns1.example.local. admin.example.local. ( 2024010101 3600 1800 604800 86400 )
@   IN NS  ns1.example.local.
20  IN PTR srv1.example.local.
10  IN PTR ns1.example.local.
```

В PTR-записи **последняя точка обязательна** (иначе имя «допишется» текущей зоной).

### Forwarders и рекурсия

Локальный сервер принимает запрос и сам его разрешает (recursion), но для внешних имён удобно перекладывать на вышестоящий:

```
options {
    directory "/var/named";
    recursion yes;
    allow-recursion { 192.168.1.0/24; localhost; };
    forwarders { 8.8.8.8; 8.8.4.4; };
};
```

- **forwarders** — куда отправлять запросы, которые сервер не может разрешить сам;
- **allow-recursion** — кому разрешена рекурсия (иначе открытый резолвер = риск);
- **/etc/resolv.conf** на клиентах — список `nameserver`, `search`.

<span style="color: 00cc18">Конфигурация BIND (`named`):</span>

- `/etc/named.conf` — `options`, объявление зон: `zone "example.local" { type master; file "example.local.zone"; };` и `zone "1.168.192.in-addr.arpa" { type master; file "1.168.192.rev"; };`;
- проверка синтаксиса: `named-checkconf`, `named-checkzone example.local /var/named/example.local.zone`;
- перечитать: `rndc reload` / `systemctl reload named`;
- проверить `allow-query`, `allow-transfer` (для slave).

<span style="color: 00cc18">Диагностика:</span>

- `dig @192.168.1.10 srv1.example.local A` — прямая;
- `dig @192.168.1.10 -x 192.168.1.20` — обратная (PTR);
- `nslookup`, `host srv1`, `dig +trace example.local`;
- `ss -lunp | grep :53`, логи `/var/log/messages`.

#### Типичные ошибки на экзамене:

- не увеличили **serial** — зона «не обновляется»;
- **открытая рекурсия**: `allow-recursion { any; };` — сервер используют для DDoS-амплификации;
- не создана **обратная зона** (PTR) — часть сервисов (почта, Kerberos) не работает;
- в PTR забыли точку в конце имени;
- в SOA/NS указывают IP вместо FQDN или неверный FQDN;
- зона объявлена только в `named.conf`, а файл зоны с ошибкой — сервер не стартует (`named-checkzone`);
- не открыты **UDP/53 и TCP/53** в файрволе — крупные ответы и трансферы не проходят;
- forwarders указывают сами на себя — петля рекурсии.
