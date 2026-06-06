# k3s apps

长期服务放在这里，每个服务一个目录。

约定：
- 每个服务目录包含 `README.md` 和 Kubernetes manifest
- 部署前先 `kubectl diff -f <dir>/`
- 部署使用 `kubectl apply -f <dir>/`
- 清理方式必须写在服务 README 中
- Secret 不写入仓库

