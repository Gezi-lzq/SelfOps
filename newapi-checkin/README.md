# NewAPI 自动签到

## 本地使用

```bash
pip install requests
python checkin.py --url https://api.example.com --auth "2461:YOUR_SESSION"
```

## GitHub Actions

1. 添加 Variable `NEWAPI_ACCOUNTS`（Settings → Variables）：
```json
[{"name": "DuckCoding", "url": "https://free.duckcoding.com", "auth": "DUCKCODING_AUTH"}]
```

2. 添加 Secret `DUCKCODING_AUTH`（Settings → Secrets）：
```
2461:MTc2ODM1Nzg2NnxEWDhFQVFMX2dBQUJFQUVRQUFEXzRmLUFBQWNHYzNSeWFXNW5...
```

格式：`userId:session`

## 获取参数

1. 登录站点 → F12 → Network → 任意请求
2. `userId`: 请求头 `new-api-user` 的值
3. `session`: Cookie 中 `session=` 后的值
