# 五分钟演示脚本

提前从项目根目录安装 workflow/api 依赖。全部使用虚构资料，不请求生成模型。
演示编号 qh-demo-001 已存在时，换一个新编号；先执行 forget 恢复默认资料条数。

## 0:00～0:40 说明需求

说：“值班人员要查预约错误说明、看自己的工单，还需要确认后才登记新问题。
这个作品先用有限规则接通各组件，便于定位问题。”

## 0:40～1:30 看证据

```bash
uv run --group workflow python -m capstone.main forget
uv run --group workflow python -m capstone.main ask "E101 预约失败怎么办？"
```

打开 day07/knowledge.json，定位 north/booking.md#1。
说：“首条是北店 E101 原文；当前没有请求生成模型，输出的是候选资料。”

## 1:30～2:20 看工具和权限

```bash
uv run --group workflow python -m capstone.main ask "查工单 T001"
uv run --group workflow python -m capstone.main ask "查工单 T002"
```

说：“第一条真正走本地 MCP stdio；第二条不返回他人工单正文。
演示身份固定 alice，真实登录需要后续实现。”

## 2:20～3:20 看暂停和恢复

```bash
uv run --group workflow python -m capstone.main draft qh-demo-001 "北店 E101 预约失败，请协助。"
uv run --group workflow python -m capstone.main show qh-demo-001
uv run --group workflow python -m capstone.main approve qh-demo-001
uv run --group workflow python -m capstone.main approve qh-demo-001
```

说：“每条命令是新进程；状态从 SQLite 恢复。重复批准仍对应同一动作。
写入重放也只有一条，由验收脚本直接查表核对。”

## 3:20～4:20 看验证与失败

```bash
uv run --group workflow --group api python -m day20.verify
uv run --group workflow python -m day13.eval_agent --fault
```

打开 day20/reports/local.md 和 day13/reports/fault.json。
说：“删除工具轨迹后答案仍正确，但任务不合格。第二个命令返回失败是故意的故障实验。”

## 4:20～5:00 说限制

说：“目前没有真实模型任务成功率，也没有公网认证和多 worker 状态一致性。
下一步会用真实门店问题标注检索/生成评估集，再接模型动态路由，保持执行层校验。”

可选加演：运行 --hybrid 展示真实本地向量分支。先下载并预热，别把等待伪装成运行失败。
无需为了完成演示发布仓库、调用外部写工具或给任何人发送消息。
