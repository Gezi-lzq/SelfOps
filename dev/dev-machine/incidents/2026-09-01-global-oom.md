# gezi-dev 全局 OOM 事件（2026-09-01）

## 概要

- 机器：`gezi-dev`（PVE VMID `240`，16 vCPU、32 GiB RAM、8 GiB Swap）
- 影响：内存与 Swap 耗尽后发生严重换页，CPU 和磁盘 I/O 饱和，SSH 与 QEMU Guest Agent 一度失去响应，最终触发全局 OOM。
- 根因：多个由 Codex 会话触发的 AutoMQ Gradle/Java 构建并发运行，叠加 Nowledge Mem、Codex、Trino 等常驻进程的内存占用，超过整机可用资源。
- 恢复：ACPI shutdown 无法完成，经确认后通过 PVE 执行 `qm reset 240`；重启后恢复关键访问链路并逐步恢复服务。

## 关键证据

- 并发构建约在 `14:11`、`14:26`、`14:28 CST` 启动。
- OOM 前的主要内存占用：
  - Java/Gradle：约 12.9 GiB RSS
  - Nowledge Mem server：约 5.36 GiB RSS
  - Codex：约 1.5 GiB RSS
  - Trino：约 852 MiB RSS，另使用约 566 MiB Swap
- 压力阶段磁盘读取达到约 300-400 MiB/s，符合内存耗尽后的 swap thrashing 特征。
- 未发现 EXT4 或块设备错误；MinIO、Trino 的超时属于资源枯竭后的连锁反应，不是物理磁盘故障。

## 恢复结果

- QEMU Guest Agent、SSH、systemd-logind、D-Bus、NetBird 已恢复并保持运行。
- Nowledge Mem 已重新启动，server 版本为 `0.10.73`；恢复后执行 embedding/projection 修复时仍可能占用约 4 GiB 内存及多个 CPU 核。
- NetBird 与当前 Mac 的连接已恢复为 P2P。

## 已应用保护

关键恢复服务均设置 systemd 资源保护，避免下一次全局内存压力同时摧毁所有远程恢复路径：

- QEMU Guest Agent：`OOMScoreAdjust=-1000`、`MemoryMin=16M`、`MemoryLow=32M`、`MemoryMax=64M`、`MemorySwapMax=0`。
- SSH、systemd-logind、D-Bus：`OOMScoreAdjust=-1000`、`MemoryMin=32M`、`MemoryLow=64M`、`MemoryMax=256M`、`MemorySwapMax=0`。
- NetBird：`OOMScoreAdjust=-1000`、`MemoryMin=128M`、`MemoryLow=256M`、`MemoryMax=1G`、`MemorySwapMax=0`。
- 上述服务同时提高 CPU/IO 权重并设置 `Nice=-10`。
- 普通 SSH 会话 scope 保持默认 OOM 分数，避免 Gradle、Codex 等从 SSH 继承 OOM 豁免。

## 独立异常与后续行动

以下服务的重启风暴已停止，但根因尚未修复，不能视为最终关闭：

- Kiro Gateway：AWS SSO refresh token 过期，持续出现 `invalid_grant`，此前约每 7-10 秒重启一次。当前为 `disabled/inactive`；应更新凭证并验证稳定后恢复启动。
- Schema Registry：无法解析 Kafka 地址 `automq:9092`，持续出现 `UnknownHostException: automq`。当前容器为 `exited` 且 restart policy 为 `no`；应修复容器 DNS/网络或 broker 地址后恢复运行，并重新设置合适的重启策略。

## 结论

本次故障不是单个服务泄漏或磁盘故障，而是没有整机资源预算时，多批并发构建与常驻服务共同耗尽 RAM 和 Swap。服务级保护只保障恢复通道，不能替代全局容量控制。后续应限制构建并发或为构建工作负载设置统一的内存/CPU 上限，并为 Nowledge Mem 等高占用常驻服务保留明确预算。
