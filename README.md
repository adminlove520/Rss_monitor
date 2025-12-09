# RSS Monitor

一个基于Python的RSS监控工具，可以定期检查安全社区的更新，并通过多种渠道推送通知。

## 功能特点

- 支持多个RSS源监控
- 多种推送渠道：钉钉、飞书、Server酱、PushPlus、Telegram Bot
- 支持夜间休眠（北京时间0-7点），避免打扰
- 支持通过GitHub Action定时运行
- 支持通过提交Issue添加新的RSS源
- 环境变量优先级高于配置文件
- 数据持久化存储

## 安装

1. 克隆仓库
```bash
git clone https://github.com/adminlove520/Rss_monitor.git
cd Rss_monitor
```

2. 安装依赖
```bash
pip install -r requirements.txt
```

## 配置

### 1. 配置文件 (`config.yaml`)

```yaml
# 配置推送
push:
  dingding:
    webhook: "https://oapi.dingtalk.com/robot/send?access_token=你的token"
    secret_key: "你的Key"
    app_name: "钉钉"
    switch: "ON"  # 设置开关为 "ON" 进行推送，设置为其他值则不进行推送
  feishu:
    webhook: "飞书的webhook地址"
    app_name: "飞书"
    switch: "OFF"
  server_chan:
    sckey: "Server酱的sckey"
    app_name: "Server酱"
    switch: "OFF"
  pushplus:
    token: "token地址"
    app_name: "PushPlus"
    switch: "OFF"
  tg_bot:
    token: "Telegram Bot的token"
    group_id: "Telegram Bot的group_id"
    app_name: "Telegram Bot"
    switch: "OFF"

# 夜间休眠配置
night_sleep:
  switch: "ON"  # 设置开关为 "ON" 开启夜间休眠，设置为其他值则关闭
```

### 2. RSS源配置 (`rss.yaml`)

```yaml
"示例网站":
  "rss_url": "https://example.com/feed.xml"
  "website_name": "示例网站"
```

### 3. 环境变量

环境变量优先级高于配置文件，可以通过环境变量覆盖配置：

| 环境变量名 | 说明 |
| --- | --- |
| DINGDING_WEBHOOK | 钉钉机器人Webhook |
| DINGDING_SECRET | 钉钉机器人密钥 |
| DINGDING_SWITCH | 钉钉推送开关（ON/OFF） |
| FEISHU_WEBHOOK | 飞书机器人Webhook |
| FEISHU_SWITCH | 飞书推送开关（ON/OFF） |
| SERVER_SCKEY | Server酱SCKEY |
| SERVER_CHAN_SWITCH | Server酱推送开关（ON/OFF） |
| PUSHPLUS_TOKEN | PushPlus Token |
| PUSHPLUS_SWITCH | PushPlus推送开关（ON/OFF） |
| TELEGRAM_TOKEN | Telegram Bot Token |
| TELEGRAM_GROUP_ID | Telegram群组ID |
| TELEGRAM_SWITCH | Telegram推送开关（ON/OFF） |
| NIGHT_SLEEP_SWITCH | 夜间休眠开关（ON/OFF） |

## 使用

### 1. 本地运行

#### 单次执行模式
```bash
python Rss_monitor.py --once
```

#### 循环执行模式
```bash
python Rss_monitor.py
```

### 2. GitHub Action

项目包含两个GitHub Action工作流：

1. **RSS_Monitor.yml**：定期运行RSS监控，默认每天国际标准时间2点（北京时间10点）执行

2. **add-rss-from-issue.yml**：通过提交Issue添加新的RSS源

## 通过Issue添加RSS源

您可以通过提交Issue来添加新的RSS源，支持两种格式：

### 格式1
```
网站名称: 示例网站
RSS URL: https://example.com/feed.xml
```

### 格式2
直接在标题或正文中包含网站名称和URL，例如：

标题：添加示例网站
正文：https://example.com/feed.xml

## 夜间休眠功能

默认情况下，脚本会在北京时间0-7点之间自动休眠，跳过推送。您可以通过以下方式控制：

1. 修改 `config.yaml` 中的 `night_sleep.switch` 配置
2. 设置环境变量 `NIGHT_SLEEP_SWITCH`

## 数据存储

监控的数据会存储在 `articles.db` SQLite数据库中，包含以下字段：
- id：自增主键
- title：文章标题
- link：文章链接
- timestamp：添加时间

## 推送渠道

### 1. 钉钉

- 支持签名验证
- 发送文本消息

### 2. 飞书

- 支持飞书机器人API
- 发送文本消息

### 3. Server酱

- 支持微信推送
- 简单易用

### 4. PushPlus

- 支持多种推送方式
- 需注册获取Token

### 5. Telegram Bot

- 支持Telegram群组推送
- 需创建Bot获取Token

## 日志

- 控制台输出执行日志
- 错误信息会打印到控制台

## 许可证

MIT License

## 贡献

欢迎提交Issue和Pull Request！

## 更新日志

- 2025.12.09：初始版本
- 2025.12.09：
  - 增加夜间休眠功能
  - 支持通过Issue添加RSS源
  - 完善配置文件支持
  - 优化推送逻辑