# k3s 管理模式

用于记录 `gezi-dev` 单机 k3s 的应用管理方式。

## 目录

```text
k3s/
├── README.md
└── examples/
    ├── whoami-ingress.yaml
    └── redis-statefulset.yaml
```

后续长期服务可以按应用放到 `apps/<name>/`，临时实验只保留必要模板和结论。

## 操作模式

1. 所有资源先写成 manifest 或 Helm values，再执行。
2. 部署前先看 diff：

```bash
kubectl diff -f dev/dev-machine/k3s/examples/whoami-ingress.yaml
```

3. 部署使用：

```bash
kubectl apply -f dev/dev-machine/k3s/examples/whoami-ingress.yaml
```

4. 检查使用：

```bash
kubectl -n dev-machine-lab get deploy,svc,ingress,pod -o wide
kubectl -n dev-machine-lab get sts,pod,pvc,pv -o wide
```

5. 清理必须显式处理 PVC：

```bash
kubectl delete namespace dev-machine-lab --wait=true
```

或只删除 StatefulSet 时，再手动删除 PVC：

```bash
kubectl -n dev-machine-lab delete statefulset redis --wait=true
kubectl -n dev-machine-lab delete pvc data-redis-0 --wait=true
```

## 实验结论

- Traefik 会自动接管 Ingress。
- 通过 NetBird IP 访问时，使用 Host header 即可命中对应 Ingress。
- `local-path` PVC 会创建目录到 `/data/volumes/k3s`。
- 删除 StatefulSet 不会自动删除它创建的 PVC。
- 删除 PVC 后，local-path 目录会回收。

## 访问约定

内网服务默认走 Traefik + NetBird。

示例：

```bash
curl -H "Host: whoami.gezi-dev.local" http://100.117.255.204/
```

公网入口策略：

1. 默认私网访问：Traefik + NetBird。
2. 下一步公网实验：NetBird Reverse Proxy。
3. 临时公网备用：cloudflared quick tunnel。
4. 长期 Cloudflare 入口：有自有域名 / Cloudflare zone 后，再评估 `cloudflare-tunnel-ingress-controller`。

NetBird Reverse Proxy 可作为当前阶段的公网暴露选型：
- 不要求先有自有域名。
- 可把开发机上的内网服务暴露为公网 HTTPS 入口。
- 适合先验证“公网访问 k3s Traefik 服务”的使用体验。
- 后续需要确认 beta 稳定性、访问控制和日志能力。

`cloudflare-tunnel-ingress-controller` 当前暂不部署。

原因：
- 当前没有接入 Cloudflare 的自有域名 / zone。
- controller 的主要价值是把 Ingress host 自动映射到 Cloudflare DNS 和 Tunnel。
- 没有 zone 时，无法验证 `Ingress host -> Cloudflare DNS -> Tunnel -> k3s Service` 的完整链路。

临时公网访问可以使用 cloudflared quick tunnel：

```bash
cloudflared tunnel --url http://127.0.0.1:80
```

quick tunnel 会生成临时 `*.trycloudflare.com` 地址，适合短期验证，不纳入长期服务管理。
