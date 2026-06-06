# Homepage

开发机入口页，用于汇总 SelfOps、k3s、NetBird、PVE 和后续服务入口。

## 部署

```bash
kubectl apply -f dev/dev-machine/k3s/apps/homepage/
kubectl -n homepage rollout status deploy/homepage
```

## 访问

内网通过 Traefik + NetBird 访问：

```bash
curl -H "Host: home.gezi-dev.local" http://100.117.255.204/
```

浏览器访问后续优先通过 NetBird Reverse Proxy，或在本机 hosts / DNS 中解析 `home.gezi-dev.local`。

## 清理

```bash
kubectl delete -f dev/dev-machine/k3s/apps/homepage/
```

该服务无 PVC。
