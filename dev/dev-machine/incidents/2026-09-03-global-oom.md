# gezi-dev 全局 OOM 复发事件（2026-09-03）

## 概要

- 机器：`gezi-dev`（PVE VMID `240`，16 vCPU、32 GiB RAM、8 GiB Swap）。
- 时间：2026-09-03 15:30 CST 触发全局 OOM；15:33 CST 左右通过 PVE 硬重启恢复。
- 影响：SSH 仅能建立 TCP 连接但无法发送 banner，QEMU Guest Agent 不响应，PVE 串口输入严重延迟，普通 guest 内恢复通道全部失效。
- 结论：AutoMQ 测试/Gradle 构建并发、14 个 Ducker 测试容器与 Nowledge Mem 常驻内存叠加，再次耗尽整机 RAM 和 Swap。

## 证据

- 内核日志明确记录 `s3-log-0-s3-sch invoked oom-killer`，当时 Swap 剩余为 0。
- OOM 快照中：
  - `nmem-server` RSS 约 5.5 GiB。
  - 最大 Java 进程 RSS 约 3.4 GiB；多个 Java/Gradle 进程合计至少 12 GiB。
  - shared memory 约 10.8 GiB。
- `ducker01` 至 `ducker14` 与 LocalStack 于 10:55 CST 同时创建并运行到硬重启：
  - 每个 Ducker 容器内存上限为 3,145,728,000 bytes（约 3 GiB）。
  - 14 个容器的聚合额度约 42 GiB，已经超过整机物理内存；LocalStack 无内存上限。
  - OOM 调用线程来自 `ducker12` 内的 AutoMQ `s3-log` 调度线程。
- 内核实际先杀死 k3s `traefik`，因为其 `oom_score_adj=1000`；Traefik 只有约 26 MiB anonymous RSS，是牺牲者而非压力根因。
- 重启后两组 Gradle 构建被同一个远程 Codex 进程自动重新拉起：
  - `tgz-artifact-security`
  - `automq-kafka-enterprise-fabric8`
- 第一次只终止 Java/Gradle 子进程后，两组构建约 20 秒内重新启动；终止对应的 `just/gradlew` 进程组和上层 Codex 执行进程后，内存稳定恢复。

## 恢复动作

1. 通过 PVE 集群定位 VM 240 实际位于节点 `pve1`（10.1.1.1）。
2. 三次发送 `Alt+SysRq+F`，未恢复 SSH、QGA 或串口控制面。
3. 执行 `qm reset 240` 硬重启。
4. 重启后确认 QGA、SSH、NetBird 均为 active，QGA 的 `OOMScoreAdjust=-1000` 等保护仍生效。
5. 停止两组复发的 Gradle 构建及其具体上层 Codex 执行进程。
6. 观察 30 秒确认构建未再次启动；最终内存约 5.6 GiB，available 约 25 GiB，Swap 0，Nowledge Mem 健康。
7. 经用户确认，回收已退出且 `restart=no` 的 `ducker01` 至 `ducker14` 容器及其匿名卷；保留 Ducker 镜像、LocalStack、bind mount 数据和其他容器。回收后确认 Ducker 容器剩余数为 0。

## 后续改进

- 单容器 3 GiB limit 不等于整机安全：Ducker 批量测试需要聚合并发上限，保证全部测试容器额度与常驻服务预算之和小于整机容量。
- 对 Codex 启动的构建应用统一的 systemd scope/cgroup 总预算，限制总内存、CPU 与并发 worker，不能只依赖 JVM 或单容器限制。
- 测试结束或任务中断时必须清理 Ducker/LocalStack 拓扑，避免长期残留。
- QGA/SSH 的 OOM 保护能避免进程被选为 OOM victim，但无法在 16 核 CPU 饱和和 Swap thrashing 时保证及时响应；仍需要全局资源预算。
- 建议增加低频历史资源采样（例如 atop/sysstat），便于在硬重启后精确还原进程级资源曲线。
