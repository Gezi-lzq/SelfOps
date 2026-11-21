# magpie

本机 magpie CLI 安装在 `/home/debian/.local/bin/magpie`，作为 systemd user service
`magpie.service` 运行 headless Web 管理页和本地网关。

- API：`127.0.0.1:3425`
- Web：`127.0.0.1:3430`
- unit 模板：`systemd/magpie.service`
- 当前用户配置：`/home/debian/.config/systemd/user/magpie.service`
- secret：`/home/debian/.config/selfops/magpie.env`，权限 `600`，不提交仓库
- 管理页登录凭证：`/home/debian/.config/selfops/magpie-web-login`，权限 `600`，不加载进服务环境
- 公网管理页：`/magpie-ui/`，独立 HTTP Basic Auth
- 公网 API：`/magpie/*`，独立 Magpie Gateway Key
- 验证：`systemctl --user is-active magpie.service`、`curl -fsS http://127.0.0.1:3425/v1/models`

应用模板：

```bash
mkdir -p ~/.config/systemd/user
cp magpie.env.example ~/.config/selfops/magpie.env
cp systemd/magpie.service ~/.config/systemd/user/magpie.service
systemctl --user daemon-reload
systemctl --user enable --now magpie.service
```

`MAGPIE_WEB_KEY` 是 Web 后端内部 key，不交给浏览器；Caddy 通过回环代理注入。
`MAGPIE_WEB_BASIC_AUTH_*` 保护管理页，明文登录密码只保存在
`~/.config/selfops/magpie-web-login`；`MAGPIE_PUBLIC_API_KEY` 使用
`magpie gateway-key add <name>` 生成，保护对外模型端点。三者不要复用。

## 本地 Kiro 插件

`plugins/kiro-local` 是 `magpie-community/plugins` 的 `packages/kiro` 本地副本，
基于 commit `8d6ae180766d653bd7d378432a00060c49a4584e`。本机定制删除
`generateAssistantResponse` 请求中 `userInputMessage.modelId`，避免 Kiro 返回
`INVALID_MODEL_ID`；登录后仍保留虚拟 `Auto` 模型，供 Kiro 自动选模。

Magpie 直接加载该目录，不依赖 GitHub fork 或 npm 发布：

```bash
magpie plugin add /home/debian/SelfOps/dev/dev-machine/magpie/plugins/kiro-local
magpie plugin move kiro
```

更新上游副本时重新同步 `packages/kiro`，保留上述两处定制和
`builderid.test.mjs` 中对应断言，然后先运行插件测试再迁移。
