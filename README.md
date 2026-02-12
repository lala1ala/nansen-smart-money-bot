# 智能资金监控 Telegram Bot 🤖

自动监控以太坊 (ETH)、Base、Solana (SOL) 和 BSC 链上的智能资金和机构交易活动，并通过 Telegram 发送定期报告。

## 功能特性 ✨

- 📊 **多链监控**: 支持 ETH、BASE、SOL、BSC 四条主流区块链
- ⏰ **多时间段**: 追踪 2小时、4小时、12小时、24小时的交易数据
- 💰 **智能资金追踪**: 监控聪明钱和机构的买入/卖出活动
- 🔔 **自动推送**: 每 2 小时自动发送监控报告到 Telegram
- 📈 **实时数据**: 接入 Nansen API，获取最新链上数据

## 快速开始 🚀

### 1. 前置要求

- Python 3.8 或更高版本
- Nansen API 密钥 ([获取地址](https://app.nansen.ai/api?tab=api))
- Telegram Bot Token (通过 [@BotFather](https://t.me/botfather) 创建)

### 2. 安装依赖

```bash
# 克隆或下载项目
cd nansen

# 安装 Python 依赖
pip install -r requirements.txt
```

### 3. 配置环境变量

复制 `.env.example` 为 `.env` 并填入配置：

```bash
cp .env.example .env
```

编辑 `.env` 文件：

```env
NANSEN_API_KEY=your_nansen_api_key_here
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here
REPORT_INTERVAL_HOURS=2
```

#### 如何获取 Telegram Chat ID？

**方法 1: 个人聊天**
1. 向 [@userinfobot](https://t.me/userinfobot) 发送任意消息
2. 它会回复您的 Chat ID

**方法 2: 频道**
1. 将您的 bot 添加为频道管理员
2. 使用频道用户名: `@your_channel_name`
3. 或使用 Chat ID (通常是 `-100xxxxxxxxxx` 格式)

### 4. 运行 Bot

```bash
python bot.py
```

成功启动后，您会看到：
```
🤖 Bot 启动中...
📡 监控链: ETH, BASE, SOL, BSC
⏰ 报告间隔: 每 2 小时
```

## 使用指南 📖

### Telegram 命令

| 命令 | 说明 |
|------|------|
| `/start` | 启动 bot 并显示欢迎信息 |
| `/report` | 立即生成并发送监控报告 |
| `/status` | 查看当前监控状态 |
| `/help` | 显示帮助信息 |

### 报告格式示例

```
📊 智能资金监控报告
🕐 时间：2026-02-12 17:30

━━━━━━━━━━━━━━━━━━
⏰ 过去 2 小时

🔵 Ethereum (ETH)
💰 买入最多：
  1. PEPE - $1.2M (15个地址)
  2. UNI - $800K (8个地址)

📉 卖出最多：
  1. SHIB - $950K (12个地址)
  2. LINK - $600K (6个地址)

━━━━━━━━━━━━━━━━━━
```

## 项目结构 📁

```
nansen/
├── bot.py              # 主程序
├── nansen_client.py    # Nansen API 客户端
├── scheduler.py        # 定时任务调度器
├── formatters.py       # 消息格式化
├── config.py           # 配置管理
├── requirements.txt    # 依赖列表
├── .env.example       # 环境变量模板
├── .gitignore         # Git 忽略文件
└── README.md          # 本文件
```

## 部署选项 🌐

### 选项 1: 本地运行

适合测试或临时使用：
```bash
python bot.py
```

### 选项 2: 后台运行 (Linux/Mac)

使用 `nohup` 或 `screen`:
```bash
nohup python bot.py > bot.log 2>&1 &
```

或使用 `screen`:
```bash
screen -S nansen-bot
python bot.py
# 按 Ctrl+A 然后 D 来分离会话
```

### 选项 3: 云服务器部署

推荐使用：
- **AWS EC2**: 创建一个小型实例 (t2.micro)
- **DigitalOcean**: Droplet (最便宜的配置即可)
- **Heroku**: 支持免费层级
- **Railway**: 简单易用的部署平台

### 选项 4: Docker 部署

创建 `Dockerfile`:
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["python", "bot.py"]
```

运行：
```bash
docker build -t nansen-bot .
docker run -d --env-file .env nansen-bot
```

### 选项 5: Systemd 服务 (Linux)

创建 `/etc/systemd/system/nansen-bot.service`:
```ini
[Unit]
Description=Nansen Smart Money Monitor Bot
After=network.target

[Service]
Type=simple
User=youruser
WorkingDirectory=/path/to/nansen
ExecStart=/usr/bin/python3 /path/to/nansen/bot.py
Restart=always

[Install]
WantedBy=multi-user.target
```

启动服务：
```bash
sudo systemctl enable nansen-bot
sudo systemctl start nansen-bot
sudo systemctl status nansen-bot
```

## 配置说明 ⚙️

### 支持的区块链

当前支持以下链（在 `config.py` 中配置）：
- Ethereum (ETH)
- Base (BASE)
- Solana (SOL)
- Binance Smart Chain (BSC)

### 时间段设置

默认监控以下时间段：
- 2 小时
- 4 小时
- 12 小时
- 24 小时

可在 `config.py` 中修改 `TIME_PERIODS` 列表。

### API 调用频率

为避免超出 Nansen API 限额：
- 默认每 2 小时发送一次报告
- 每次报告约调用 32 次 API
- 每天约消耗 384 次 API 调用

请根据您的 API 配额调整 `REPORT_INTERVAL_HOURS`。

## 故障排查 🔧

### 常见问题

**1. `ModuleNotFoundError`**
```bash
pip install -r requirements.txt
```

**2. API 密钥无效**
- 检查 `.env` 文件中的 `NANSEN_API_KEY` 是否正确
- 确认 API 密钥有足够的额度

**3. Bot 无法发送消息**
- 确认 `TELEGRAM_BOT_TOKEN` 正确
- 确认 `TELEGRAM_CHAT_ID` 正确
- 如果是频道，确保 bot 已被添加为管理员

**4. 数据为空**
- 检查选定的链是否有智能资金活动
- 尝试使用 `/report` 命令手动生成报告查看错误信息

## API 成本估算 💰

根据 Nansen API 定价：
- 每 2 小时运行: ~384 次调用/天
- 每 4 小时运行: ~192 次调用/天
- 每 24 小时运行: ~32 次调用/天

建议根据您的需求和 API 配额选择合适的报告间隔。

## 更新日志 📝

### v1.0.0 (2026-02-12)
- 🎉 首次发布
- ✅ 支持 4 条主流区块链
- ✅ 多时间段监控 (2h, 4h, 12h, 24h)
- ✅ 自动定时报告
- ✅ Telegram 命令交互

## 许可证 📄

MIT License

## 支持 💬

如有问题或建议，请通过以下方式联系：
- GitHub Issues: [创建 Issue](https://github.com/yourusername/nansen-bot/issues)
- Telegram: 在您的 bot 中使用 `/help` 命令

---

**⚠️ 免责声明**: 本工具仅供信息参考，不构成投资建议。加密货币投资存在风险，请谨慎决策。
