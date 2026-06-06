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

浏览器内网访问可以通过本机 hosts / DNS 解析 `home.gezi-dev.local`。

NetBird Reverse Proxy 已试用后放弃，当前不作为 Homepage 公网入口。

## 清理

```bash
kubectl delete -f dev/dev-machine/k3s/apps/homepage/
```

该服务无 PVC。
