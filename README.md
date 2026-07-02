# 🎫 Seat/Inventory Availability Monitor

**[🇬🇧 English](#-english) · [🇨🇳 中文](#-中文) · [🇯🇵 日本語](#-日本語)**

Polls a ticketing site's availability API and pings you on 📲 Telegram the
instant a sold-out section opens up. Notify-only — never buys anything for you.

---

## 🇬🇧 English

A personal-use tool that polls a ticketing (or similar inventory) site's
availability API and sends a 📲 Telegram alert the moment a specific
section/SKU goes from sold-out to available. Notify-only — it never adds
to cart or purchases anything; you still act on the alert yourself.

Built for a real event where the venue's public "seat map" endpoint only
exposed *price tier*, not actual per-section availability — the real
signal turned out to live in a separate per-section summary endpoint that
returns every section's remaining count in a single request. That's the
pattern this project is built around: find the lightweight endpoint that
gives you granular state in one call, poll it politely, and alert on state
transitions rather than every poll.

### ⚙️ How it works

1. `jsonp_parser` strips the JSONP callback wrapper (and any `/**/` comment
   prefix some APIs add) and returns plain JSON.
2. `area_filter` picks out sections with remaining count > 0, excluding any
   section matching an ignore-prefix (configurable).
3. `state_store` tracks which sections were already known-available, so
   alerts only fire on a 0 → >0 transition, not every poll.
4. `telegram_notifier` sends the alert. 🚨
5. `monitor` / `browser_monitor` are the two poll-loop implementations (see
   below).

### 🧭 Two run modes

Some sites sit behind a bot-detection layer that rejects plain HTTP
requests even with valid session cookies and matching headers.

- **`python main.py`** — plain `requests` session (`src/monitor.py`).
  Simple and lightweight. ⚡
- **`python main.py --browser`** — drives a real Playwright/Chromium
  browser and calls `fetch()` from inside the page's own JS context
  (`src/browser_monitor.py`), so requests come from an actual browser
  session rather than a script pretending to be one. 🌐 Keeps a visible
  browser window open for the whole monitoring session; you log in once
  when it starts, then the poll loop reuses that live session.

### 🚀 Setup

1. `pip install -r requirements.txt`
2. `playwright install chromium`
3. `cp config/config.yaml.example config/config.yaml` and fill in your
   target site's real endpoint URL, POST params, and headers (grab these
   from your browser's Network tab while browsing the site normally).
4. 🍪 Cookies (only needed for the non-`--browser` mode):
   - `python login_helper.py`, log in manually in the browser window that
     opens, press Enter in the terminal — cookies get saved to
     `config/cookies.json`.
   - Or export cookies manually from your browser's devtools into that
     same file (see `config/cookies.json.example` for the format).
5. 🤖 Telegram: create a bot via [@BotFather](https://t.me/BotFather), message
   it once, then hit `https://api.telegram.org/bot<token>/getUpdates` to
   find your chat_id. Fill both into `config/config.yaml`.
6. `python main.py --browser --dry-run` to fetch once and print current
   per-section counts without sending Telegram messages or writing state.
7. `python main.py --browser` to start monitoring for real. ✅

### 📝 Notes

- Polls every 3-5s with a randomized interval and only alerts on state
  transitions, not on every poll while a section stays available.
- ⚠️ Automated polling likely falls under most ticketing sites' bot /
  automated-access restrictions — this is meant for personal, low-volume
  use, not for reselling or high-volume automated purchasing. It also
  deliberately stops short of any add-to-cart/checkout automation.
- 🔒 `config/config.yaml` and `config/cookies.json` hold live session
  credentials once filled in — both are gitignored. Don't commit or share
  them.

---

## 🇨🇳 中文

一个个人使用的小工具，轮询票务（或类似库存）网站的余票查询接口，一旦某个
区域从"售罄"变成"有票"，立刻通过 📲 Telegram 推送提醒。**只负责通知，不负责下单**——
它不会自动加购物车或购买，看到提醒之后还是要你自己动手抢。

这个项目的起因是某次抢票时发现，场馆公开的"座位图"接口只返回**价位档次**，
并不返回每个分区真实的余票数量——真正有用的信号其实藏在另一个轻量级的
汇总接口里，一次请求就能拿到所有分区的剩余数量。这也是本项目的核心思路：
找到那个能一次性给出细粒度库存状态的轻量接口，礼貌地轮询它，只在状态发生
变化时提醒，而不是每次轮询都发消息。

### ⚙️ 工作原理

1. `jsonp_parser` 去掉 JSONP 回调包装（以及某些接口会加的 `/**/` 注释前缀），返回纯 JSON。
2. `area_filter` 筛选出剩余数量 > 0 的分区，同时排除匹配"忽略前缀"（可配置）的分区。
3. `state_store` 记录哪些分区之前已经是"有票"状态，这样只有在 0 → >0
   的状态变化时才会触发提醒，而不是每次轮询都发。
4. `telegram_notifier` 负责发送提醒消息。🚨
5. `monitor` / `browser_monitor` 是两种轮询循环的具体实现（见下文）。

### 🧭 两种运行模式

有些网站有反爬虫机制，即使带着合法的 session cookie 和匹配的请求头，
普通的 HTTP 请求也会被拒绝。

- **`python main.py`** — 用普通的 `requests` 会话请求（对应 `src/monitor.py`），
  简单轻量。⚡
- **`python main.py --browser`** — 启动真实的 Playwright/Chromium 浏览器，
  在页面自己的 JS 上下文里调用 `fetch()`（对应 `src/browser_monitor.py`），
  这样请求就是从一个真实浏览器会话发出的，而不是脚本伪装的。🌐 整个监控过程
  会一直保持浏览器窗口打开；启动时手动登录一次，之后轮询循环会复用这个登录状态。

### 🚀 安装步骤

1. `pip install -r requirements.txt`
2. `playwright install chromium`
3. `cp config/config.yaml.example config/config.yaml`，然后填入目标网站真实的
   接口地址、POST 参数和请求头（可以正常浏览网站时从浏览器的 Network 面板里抓取）。
4. 🍪 Cookies（只有非 `--browser` 模式才需要）：
   - 运行 `python login_helper.py`，在弹出的浏览器窗口里手动登录，然后回到终端按回车——
     cookies 会保存到 `config/cookies.json`。
   - 或者自己从浏览器开发者工具里导出 cookies，按同样格式写入这个文件
     （格式参考 `config/cookies.json.example`）。
5. 🤖 Telegram：通过 [@BotFather](https://t.me/BotFather) 创建一个机器人，给它发一条消息，
   然后访问 `https://api.telegram.org/bot<token>/getUpdates` 找到你的 chat_id。
   把两者都填进 `config/config.yaml`。
6. 先跑 `python main.py --browser --dry-run` 抓取一次并打印当前各分区的余票数量，
   不会发送 Telegram 消息，也不会写入状态文件。
7. 确认没问题后跑 `python main.py --browser` 正式开始监控。✅

### 📝 注意事项

- 轮询间隔是 3-5 秒的随机值，并且只在状态变化时提醒，不会在某个分区持续
  有票期间每次轮询都发消息。
- ⚠️ 自动化轮询很可能违反大多数票务网站关于机器人/自动化访问的限制条款——
  本项目仅面向个人的低频使用场景，不是为了黄牛倒卖或大规模自动化购票而做的，
  也刻意没有实现任何加购物车/结账相关的自动化。
- 🔒 一旦填好内容，`config/config.yaml` 和 `config/cookies.json`
  里就会包含真实的登录凭证——两者都已加入 `.gitignore`，请不要提交或分享出去。

---

## 🇯🇵 日本語

チケット（または類似の在庫）サイトの空席状況 API をポーリングし、特定の
区画/SKU が「完売」から「購入可能」に変わった瞬間に 📲 Telegram で通知する
個人用ツールです。**通知専用**——カートへの追加や購入は一切行いません。
通知を見た後、実際の操作は自分で行う必要があります。

ある実際のイベントで、会場が公開している「座席マップ」API は*価格帯*しか
返さず、各区画の実際の空席数は分からない、という問題に直面したことが
このプロジェクトの発端です。実は本当に使える情報は別の軽量な集計用
エンドポイントにあり、そこに1回リクエストするだけで全区画の残数がまとめて
取得できました。「1回の呼び出しで細かい在庫状態を返してくれる軽量な
エンドポイントを見つけ、礼儀正しくポーリングし、毎回ではなく状態が変化した
ときだけ通知する」——これが本プロジェクトの基本方針です。

### ⚙️ 仕組み

1. `jsonp_parser` が JSONP のコールバックラッパー（一部の API が付与する
   `/**/` コメント接頭辞も含む）を取り除き、素の JSON を返します。
2. `area_filter` が残数 > 0 の区画だけを抽出し、設定可能な無視プレフィックス
   に一致する区画は除外します。
3. `state_store` がすでに「購入可能」と分かっている区画を記録しているため、
   0 → >0 の状態変化があったときだけ通知が発火し、毎回のポーリングでは
   発火しません。
4. `telegram_notifier` が実際の通知を送信します。🚨
5. `monitor` / `browser_monitor` は2種類のポーリングループの実装です
   （詳細は下記）。

### 🧭 2つの実行モード

サイトによってはボット検出レイヤーがあり、有効なセッション Cookie や
一致するヘッダーを付けても、素の HTTP リクエストは拒否されることがあります。

- **`python main.py`** — 通常の `requests` セッションを使用
  （`src/monitor.py`）。シンプルで軽量です。⚡
- **`python main.py --browser`** — 実際の Playwright/Chromium ブラウザを
  起動し、ページ自身の JS コンテキスト内から `fetch()` を呼び出します
  （`src/browser_monitor.py`）。これによりリクエストはスクリプトが偽装した
  ものではなく、実際のブラウザセッションから発行されます。🌐
  監視セッション中はブラウザウィンドウが表示されたままになります。
  起動時に一度手動でログインすれば、以降のポーリングループはその
  ログイン済みセッションを再利用します。

### 🚀 セットアップ

1. `pip install -r requirements.txt`
2. `playwright install chromium`
3. `cp config/config.yaml.example config/config.yaml` を実行し、対象サイトの
   実際のエンドポイント URL・POST パラメータ・ヘッダーを記入します
   （通常通りサイトを閲覧しながらブラウザの Network タブから取得できます）。
4. 🍪 Cookie（`--browser` を使わないモードでのみ必要）：
   - `python login_helper.py` を実行し、開いたブラウザウィンドウで手動ログイン後、
     ターミナルで Enter キーを押すと `config/cookies.json` に Cookie が保存されます。
   - または、ブラウザの devtools から手動で Cookie をエクスポートし、同じ
     形式でこのファイルに書き込んでください（形式は `config/cookies.json.example` 参照）。
5. 🤖 Telegram：[@BotFather](https://t.me/BotFather) で Bot を作成し、一度メッセージを送った後、
   `https://api.telegram.org/bot<token>/getUpdates` にアクセスして chat_id を
   調べます。両方を `config/config.yaml` に記入してください。
6. `python main.py --browser --dry-run` を実行すると、1回だけ取得して現在の
   各区画の残数を表示します（Telegram 送信や状態ファイルへの書き込みは行いません）。
7. 問題なければ `python main.py --browser` で本番の監視を開始します。✅

### 📝 注意事項

- ポーリング間隔は3〜5秒のランダムな値で、状態が変化したときだけ通知します
  （ある区画が購入可能な状態を維持している間、毎回のポーリングでは通知しません）。
- ⚠️ 自動ポーリングは多くのチケットサイトのボット/自動アクセス制限に
  抵触する可能性があります——本プロジェクトはあくまで個人の低頻度な利用を
  想定したものであり、転売や大規模な自動購入を目的としたものではありません。
  カートへの追加や決済の自動化も意図的に実装していません。
- 🔒 入力後の `config/config.yaml` と `config/cookies.json` には実際の
  ログイン認証情報が含まれます——どちらも `.gitignore` に含まれているので、
  コミットしたり共有したりしないでください。
