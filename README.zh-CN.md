# 🎫 座位/库存余量监控工具

[English](README.md)

一个自用小工具：轮询票务（或类似库存类）网站的余量接口，一旦某个区块/SKU 从"售罄"变成"有货"，立刻发送 📲 Telegram 通知。**只负责通知**——不会自动加购物车、不会自动下单，看到通知之后要不要买，还是你自己动手。

这个项目最初是为了一场真实的演出写的：场馆公开的"座位图"接口只带**价位分区信息**，并不是真实的分区余票状态；真正的余票数据其实藏在另一个**按分区汇总**的接口里，一次请求就能拿到每个分区各自的剩余数量。这个项目的设计思路也是照着这个经验来的：找到那个能一次性给出细粒度状态的轻量接口，礼貌地轮询它，只在状态发生变化时提醒，而不是每次轮询都刷屏。

## ⚙️ 工作原理

1. `jsonp_parser` 负责剥掉 JSONP 的回调函数包装（以及某些接口会加的 `/**/` 注释前缀），还原成普通 JSON。
2. `area_filter` 从中挑出剩余数量 > 0 的分区，同时排除掉匹配"忽略前缀"规则的分区（可配置）。
3. `state_store` 记录哪些分区之前就已经"已知有货"，这样只有在 0 → 有货 这个**状态变化**的瞬间才会提醒，而不是每次轮询都提醒。
4. `telegram_notifier` 负责把提醒发出去。🚨
5. `monitor` / `browser_monitor` 是两种轮询循环的具体实现（见下文）。

## 🧭 两种运行模式

有些网站会有反机器人检测，即使带着有效的登录 cookies、请求头也伪装得很像,普通脚本请求还是会被拒绝。

- **`python main.py`** —— 用普通的 `requests` 会话（对应 `src/monitor.py`），简单轻量。⚡
- **`python main.py --browser`** —— 用 Playwright 驱动一个真实的 Chromium 浏览器，在**页面自己的 JS 环境里**调用 `fetch()`（对应 `src/browser_monitor.py`），这样请求真的是从一个真浏览器会话里发出去的，而不是脚本假装成浏览器。🌐 整个监控过程中会一直保持一个可见的浏览器窗口；启动时手动登录一次，之后轮询循环会一直复用这个真实会话。

## 🚀 使用步骤

1. `pip install -r requirements.txt`
2. `playwright install chromium`
3. `cp config/config.yaml.example config/config.yaml`，然后填入你目标网站真实的接口地址、POST 参数和请求头（在浏览器 Network 面板里正常浏览网站时抓一下就能拿到）。
4. 🍪 Cookies（只有非 `--browser` 模式才需要）：
   - 跑 `python login_helper.py`，在弹出的浏览器窗口里手动登录，回终端按回车——cookies 会自动存到 `config/cookies.json`。
   - 或者自己从浏览器 devtools 里手动导出 cookies，存成同样的文件格式（格式参考 `config/cookies.json.example`）。
5. 🤖 Telegram：通过 [@BotFather](https://t.me/BotFather) 创建一个 bot，给它发一条消息，然后访问 `https://api.telegram.org/bot<token>/getUpdates` 找到你的 chat_id。把这两个值填进 `config/config.yaml`。
6. `python main.py --browser --dry-run` 先跑一次，只打印当前各分区数量，不发 Telegram、不写状态文件——用来确认配置对不对。
7. `python main.py --browser` 正式开始监控。✅

## 📝 一些说明

- 轮询间隔是 3-5 秒随机，并且只在分区"状态发生变化"时提醒，不会每次轮询都提醒。
- ⚠️ 自动化轮询大概率会踩到大部分票务网站的"禁止机器人/自动化访问"条款——这个工具是给个人低频使用的，不是用来做转卖或者大规模自动化抢购的，而且刻意没有做任何自动加购/自动下单的功能。
- 🔒 `config/config.yaml` 和 `config/cookies.json` 一旦填入真实信息，就带有你的真实登录态——这两个文件都已经加入 `.gitignore`，不要提交或者分享出去。
