# 快速设置指南 🚀

## 第一步：获取必要的凭证

### 1. Nansen API Key

1. 访问 https://app.nansen.ai/api?tab=api
2. 登录您的 Nansen 账户
3. 复制您的 API Key

### 2. 创建 Telegram Bot

1. 在 Telegram 中搜索 [@BotFather](https://t.me/botfather)
2. 发送 `/newbot` 命令
3. 按提示输入 bot 名称和用户名
4. 保存 BotFather 返回的 **Bot Token**

### 3. 获取 Telegram Chat ID

**如果发送到个人聊天：**
1. 在 Telegram 搜索 [@userinfobot](https://t.me/userinfobot)
2. 给它发送任意消息
3. 它会回复您的 Chat ID（纯数字）

**如果发送到频道：**
1. 创建一个 Telegram 频道
2. 将您的 bot 添加为频道管理员
3. 使用频道用户名（如 `@your_channel`）或数字 ID

## 第二步：配置项目

### 1. 克隆/下载代码
```bash
cd f:\antigravity\nansen
```

### 2. 安装依赖
```bash
pip install -r requirements.txt
```

### 3. 配置环境变量

复制 `.env.example` 为 `.env`:
```bash
copy .env.example .env
```

编辑 `.env` 文件，填入您的凭证：
```env
NANSEN_API_KEY=nansen_xxxxxxxxxxxxx
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
TELEGRAM_CHAT_ID=123456789
REPORT_INTERVAL_HOURS=2
```

## 第三步：测试运行

### 测试 bot 连接
```bash
python bot.py
```

如果成功，您会看到：
```
🤖 Bot 启动中...
📡 监控链: ETH, BASE, SOL, BSC
⏰报告间隔: 每 2 小时
```

### 在 Telegram 中测试

1. 在 Telegram 搜索您的 bot
2. 发送 `/start` 命令
3. 发送 `/report` 命令测试报告生成

## 第四步：部署到 GitHub Actions（可选）

### 1. 推送代码到 GitHub
```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/yourusername/nansen-bot.git
git push -u origin main
```

### 2. 设置 GitHub Secrets

在 GitHub 仓库页面：
1. 点击 **Settings** → **Secrets and variables** → **Actions**
2. 添加以下 secrets：
   - `NANSEN_API_KEY`
   - `TELEGRAM_BOT_TOKEN`
   - `TELEGRAM_CHAT_ID`

### 3. 启用 GitHub Actions

1. 进入仓库的 **Actions** 标签
2. 启用 workflows
3. 工作流会自动每 2 小时运行一次

### 4. 手动触发（测试）

在 Actions 页面：
1. 选择 "Smart Money Monitor Bot" workflow
2. 点击 "Run workflow"
3. 查看运行结果

## 故障排查

### 问题 1：`ModuleNotFoundError: No module named 'telegram'`
**解决方案：**
```bash
pip install python-telegram-bot
```

### 问题 2：Bot 无法发送消息
**检查清单：**
- [ ] Bot Token 是否正确？
- [ ] Chat ID 是否正确？
- [ ] 如果是频道，bot 是否已添加为管理员？
- [ ] 是否先给 bot 发送过 `/start` 消息？

### 问题 3：API 返回错误
**检查清单：**
- [ ] Nansen API Key 是否有效？
- [ ] API 额度是否充足？
- [ ] 网络连接是否正常？

## 下一步

现在您可以：
- ✅ 让 bot 持续运行，每 2 小时发送报告
- ✅ 使用 `/report` 随时查看最新数据
- ✅ 根据需要调整监控间隔和参数

享受智能资金监控！🎉
