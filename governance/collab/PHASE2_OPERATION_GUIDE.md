# Phase 2 完整操作指南

## 架构说明

```
Nova 的 Mac                          Jarvis 的电脑 (192.168.31.64)
   |                                      |
   +- collab_daemon.py (my_id=nova)      +- collab_daemon.py (my_id=jarvis)
   |                                      |
   +- phase2_test_sender.py              +- NATS server (0.0.0.0:4222)
   |                                      |
   +-------- NATS 总线 (192.168.31.64:4222) --------+
```

两条消息流：
1. **Nova → Jarvis**：test_sender 发 `review_request` → Jarvis daemon 收
2. **Jarvis → Nova**：Jarvis daemon 发 ACK → Nova 的 test_sender 收

---

## 第一步：NAT 服务器（Jarvis 电脑）

Jarvis 电脑上已启动：

```bash
nats-server -a 0.0.0.0 -p 4222
```

验证：
```bash
nc -zv 127.0.0.1 4222
```

---

## 第二步：代码同步（两台电脑都要做）

```bash
cd ~/.openclaw/workspace/Nexus
git pull
```

---

## 第三步：本地配置文件（两台电脑都要做）

**从模板创建本地配置：**

```bash
cp governance/collab/collab_config.json.template governance/collab/collab_config.json
```

**编辑 `collab_config.json`，填入以下内容：**

### Jarvis 电脑的配置（my_id = jarvis）

```json
{
  "my_id": "jarvis",
  "sender_id": "jarvis",
  "target_id": "nova",
  "nats_url": "nats://192.168.31.64:4222",
  "subjects": {
    "command": "gov.collab.command",
    "ack": "gov.collab.ack",
    "event": "gov.collab.event",
    "notify": "gov.collab.notify"
  },
  "poll_interval": 30,
  "heartbeat_interval": 60,
  "shutdown_grace": 30,
  "data_dir": null,
  "protocol_version": "0.2"
}
```

### Nova 电脑的配置（my_id = nova）

```json
{
  "my_id": "nova",
  "sender_id": "nova",
  "target_id": "jarvis",
  "nats_url": "nats://192.168.31.64:4222",
  "subjects": {
    "command": "gov.collab.command",
    "ack": "gov.collab.ack",
    "event": "gov.collab.event",
    "notify": "gov.collab.notify"
  },
  "poll_interval": 30,
  "heartbeat_interval": 60,
  "shutdown_grace": 30,
  "data_dir": null,
  "protocol_version": "0.2"
}
```

---

## 第四步：安装依赖（两台电脑都要做）

```bash
pip install nats-py
```

（只需一次）

---

## 第五步：启动 Daemon

### Jarvis 电脑（已启动，确认状态）

```bash
python governance/collab/collab_daemon.py
```

日志显示 `[INFO] Subscribed to gov.collab.command` 即为成功。

### Nova 电脑（启动步骤同上）

```bash
python governance/collab/collab_daemon.py
```

---

## 第六步：发送测试消息

从 **Nova 电脑** 运行：

```bash
python governance/collab/phase2_test_sender.py
```

### 成功输出

```
Connecting to nats://192.168.31.64:4222...
Connected.
Subscribing to gov.collab.ack...
Subscription active. Now publishing command.

Publishing: collab_id=phase2-test-20260421-XXXXX from=nova to=jarvis
Published. Waiting for ACK...

[ACK RECEIVED] message_id=ack-XXXXX ack_for=msg-XXXXX status=received result=None to=nova from=jarvis

[SUCCESS] ACK received within timeout
[SUCCESS] Total ACKs received: 1
  -> ack_id=ack-XXXXX status=received result=None
Done.
```

### 失败输出

```
[FAIL] No ACK received within 10 seconds
[FAIL] ACKs received before timeout: 0
```

---

## 验证清单

| 验证项 | Jarvis 日志 | Nova 日志 |
|--------|-------------|-----------|
| 消息发出 | `[CMD] [collab_id] review_request` | `[SUCCESS]` |
| 事件触发 | `[EVENT_DRIVEN]` | — |
| ACK 发出 | `[SKIP] ACK ... to=nova (not me)` | `[ACK RECEIVED]` |
| 状态更新 | `skill_dispatched` in state | — |

---

## 日志位置

**Jarvis 电脑：**
```
D:\Projects\Nexus\governance\data\nats_collab_daemon.log
```

查看最新日志：
```bash
Get-Content D:\Projects\Nexus\governance\data\nats_collab_daemon.log -Tail 20
```

---

## 常见问题

**Q: 显示 `[FAIL] No ACK received`**
A: 检查三点 — 1) Jarvis daemon 是否在运行；2) NATS 是否在 192.168.31.64:4222；3) 两台电脑在同一个网络

**Q: 显示 `[CMD]` 但没有 `[EVENT_DRIVEN]`**
A: 代码有问题，检查 handler.py 的 `_skill_dispatch` 是否正常

**Q: `collab_config.json` 修改后报错**
A: JSON 格式必须正确，字段不能为空字符串

---

## 配置文件规则

| 规则 | 说明 |
|------|------|
| `collab_config.json` 不上传 Git | 本地机器单独管理 |
| 模板文件是 `collab_config.json.template` | 永远在 Git 里 |
| 每台机器配置值可以不同 | `my_id` 决定身份 |
| 所有 NATS subject 从配置读 | 代码无硬编码 |