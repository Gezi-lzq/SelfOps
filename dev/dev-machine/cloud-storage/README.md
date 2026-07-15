# Cloud Storage

为 `gezi-dev` 提供 Agent 可直接使用的文件上传和异地备份约定。子系统按能力命名，Google Drive 是当前 provider。

## 当前状态

- 已创建 rclone remote `gdrive`，使用个人 Google Drive，不使用 Shared Drive。
- OAuth scope 为 `drive.file`；rclone 只能管理由该 OAuth app 创建的文件，不能读取 Drive 中其他既有文件。
- 本机配置为 `~/.config/rclone/rclone.conf`，权限 `600`，不提交仓库。
- 已创建 `gdrive:gezi-dev/uploads/` 和 `gdrive:gezi-dev/backups/`。
- 已完成单文件上传与 MD5 校验，并清理 `_smoke` 测试对象。
- 已安装 `fuse3`，预留 `/home/debian/Drive` 挂载点和 `/data/scratch/rclone-cache/gdrive` VFS 缓存目录。
- `cloud-storage-gdrive-mount.service` 已完成启动、目录读取、经挂载路径写入、远端 MD5、删除和卸载验证；当前为手动启动的 `active/running` 状态，挂载可用，但尚未启用开机自启。
- 尚未配置定期备份任务。
- 当前使用 rclone 内置的公共 Google OAuth client，验证时遇到共享 API 配额限流；低频操作可以重试，启用定期备份前建议改用个人 client ID。

## 实现约定

- 上传和备份默认使用 `rclone` 直接传输，不依赖挂载路径；FUSE 只服务于可选的本地浏览入口。
- 不增加 mise task 或通用命令 wrapper；Agent 直接执行 `rclone`。
- remote 名称为 `gdrive`，远端根目录为 `gdrive:gezi-dev/`。

## 远端布局

```text
gdrive:gezi-dev/
├── uploads/       # 一次性或按需上传
└── backups/       # 固定目标的覆盖式备份
```

## 默认操作

单文件上传或覆盖固定目标：

```bash
rclone copyto /local/path/file \
  gdrive:gezi-dev/backups/name/file
```

目录增量覆盖，不删除远端多余文件：

```bash
rclone copy /local/path/directory \
  gdrive:gezi-dev/backups/name
```

查看远端结果：

```bash
rclone lsjson gdrive:gezi-dev/backups/name
```

## Agent 安全边界

- 默认只使用 `copyto` 或 `copy`；同名内容可以覆盖，但不主动删除远端其他文件。
- 只有用户明确要求远端与本地完全一致时才使用 `sync`，执行前必须先运行同参数的 `rclone sync --dry-run` 并检查删除项。
- 不默认上传整个 `/home/debian`，也不主动上传 `.ssh`、`.env`、OAuth token、API key 或其他凭证。
- 上传前确认源路径和远端目标；上传后使用 `lsjson`，必要时配合 `rclone check` 验证。
- Google Drive 自身的文件修订不能替代可靠的长期版本备份；需要历史快照时再单独引入 restic 策略。

## 定期备份

出现明确的源目录、远端目标和执行频率后，为每个任务建立独立的 systemd user service/timer。unit 直接调用 rclone，不通过 mise task；使用 mise shim 的稳定路径：

```text
/home/debian/.local/share/mise/shims/rclone
```

每个任务必须能够单独启停和查看日志。应用到机器并验证后，在 `../STATE.md` 记录 unit 名、源目录、远端目标和验证结果，但不记录凭证。

## 可选挂载

挂载只作为浏览和临时文件访问入口，不替代直接执行 `rclone copy`/`copyto` 的备份流程，也不用于 Git 仓库、数据库或高频构建目录。

```text
remote:      gdrive:gezi-dev
mountpoint:  /home/debian/Drive
VFS cache:   /data/scratch/rclone-cache/gdrive
cache mode:  writes
cache limit: 20G
```

unit 模板位于 `systemd/cloud-storage-gdrive-mount.service`，本机 user systemd 通过链接加载。当前已手动启动并保持运行，但未 enable；服务停止或机器重启后不会自动恢复挂载。启用开机自启前，优先为 rclone 配置个人 Google OAuth client ID，避免公共 client 的共享配额限流。

手动挂载和卸载：

```bash
systemctl --user start cloud-storage-gdrive-mount.service
systemctl --user stop cloud-storage-gdrive-mount.service
```

检查状态：

```bash
systemctl --user status cloud-storage-gdrive-mount.service
findmnt /home/debian/Drive
```

只有明确需要开机自动挂载时才执行：

```bash
systemctl --user enable cloud-storage-gdrive-mount.service
```

## 验证流程

1. 运行 `rclone config` 创建可写的 `gdrive` remote，并在可信浏览器完成 Google OAuth。
2. 上传一个不含敏感信息的临时文件到 `gdrive:gezi-dev/uploads/_smoke/`。
3. 使用 `rclone lsjson` 查看对象，下载到临时目录并比较内容。
4. 验证结束后清理测试对象，再把已确认事实写入 `../STATE.md`。
