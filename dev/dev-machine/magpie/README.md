# magpie

本机 magpie CLI 安装在 `/home/debian/.local/bin/magpie`，作为 systemd user service
`magpie.service` 运行本地网关。

- 监听：`127.0.0.1:3425`
- unit 模板：`systemd/magpie.service`
- 当前用户配置：`/home/debian/.config/systemd/user/magpie.service`
- 验证：`systemctl --user is-active magpie.service`、`curl -fsS http://127.0.0.1:3425/v1/models`

应用模板：

```bash
mkdir -p ~/.config/systemd/user
cp systemd/magpie.service ~/.config/systemd/user/magpie.service
systemctl --user daemon-reload
systemctl --user enable --now magpie.service
```
