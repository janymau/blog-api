# HW4 — Nginx Reverse Proxy

## Setup

```bash
docker compose up --build
```

## Verification

### 1. nginx отвечает на порту 80
```bash
curl -I http://localhost/admin/login/
# → HTTP/1.1 200 OK
# → Server: nginx/1.27.5
```

### 2. Статика отдаётся nginx с долгим кэшем
```bash
curl -I http://localhost/static/admin/css/base.css
# → HTTP/1.1 200 OK
# → Server: nginx/1.27.5
# → Cache-Control: max-age=2592000
```

### 3. API постов возвращает JSON
```bash
curl http://localhost/api/posts
# → [{"id":1,"title":...}]
```

### 4. Остановка web даёт 502 от nginx
```bash
docker compose stop web
curl -I http://localhost/api/posts
# → HTTP/1.1 502 Bad Gateway
# → Server: nginx/1.27.5
docker compose start web
```

### 5. Порт 8000 недоступен снаружи
```bash
curl http://localhost:8000/
# → curl: (7) Failed to connect to localhost port 8000
```

### 6. WebSocket — 101 Switching Protocols

Получи JWT токен:
```bash
curl -X POST http://localhost/api/users/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@admin.com","password":"Bezdar123@"}'
```

Подключись к WebSocket:
```bash
wscat -c "ws://localhost/ws/posts/<slug>/comments/?token=<access_token>" \
  -H "Origin: http://localhost"
# → Connected (press CTRL+C to quit)
```