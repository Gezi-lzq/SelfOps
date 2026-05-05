# Bub Custom Plugins

自定义 Bub 插件源码统一放在这个目录。

## 约定

- 每个插件使用独立子目录，例如 `bub-my-plugin/`
- profile 通过各自的 `bub-reqs.txt` 决定是否启用某个插件
- 容器内挂载路径固定为 `/workspace/plugins`
- `bub-reqs.txt` 中使用 `file://` 路径引用本地插件，例如：

```txt
bub-my-plugin @ file:///workspace/plugins/bub-my-plugin
```

## 目录示例

```txt
agents/bub/plugins/
  bub-my-plugin/
    pyproject.toml
    README.md
    src/
      bub_my_plugin/
        __init__.py
        plugin.py
```
