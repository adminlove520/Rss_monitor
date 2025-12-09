import sqlite3
import feedparser
import yaml
import requests
import time
import os
import argparse
from datetime import datetime
import dingtalkchatbot.chatbot as cb

# 加载配置文件
def load_config():
    # 从文件加载配置
    config = {}
    try:
        with open('config.yaml', 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f) or {}
    except FileNotFoundError:
        print("未找到config.yaml文件，将使用环境变量配置")
    except Exception as e:
        print(f"加载config.yaml文件出错: {str(e)}")
    
    # 初始化push配置
    push_config = config.get('push', {})
    
    # 钉钉推送配置 - 环境变量优先级高于配置文件
    if 'dingding' not in push_config:
        push_config['dingding'] = {}
    
    push_config['dingding']['webhook'] = os.environ.get('DINGDING_WEBHOOK', push_config['dingding'].get('webhook', ''))
    push_config['dingding']['secret_key'] = os.environ.get('DINGDING_SECRET', push_config['dingding'].get('secret_key', ''))
    push_config['dingding']['switch'] = os.environ.get('DINGDING_SWITCH', push_config['dingding'].get('switch', 'OFF'))
    
    # 飞书推送配置 - 环境变量优先级高于配置文件
    if 'feishu' not in push_config:
        push_config['feishu'] = {}
    
    push_config['feishu']['webhook'] = os.environ.get('FEISHU_WEBHOOK', push_config['feishu'].get('webhook', ''))
    push_config['feishu']['switch'] = os.environ.get('FEISHU_SWITCH', push_config['feishu'].get('switch', 'OFF'))
    
    # Server酱推送配置 - 环境变量优先级高于配置文件
    if 'server_chan' not in push_config:
        push_config['server_chan'] = {}
    
    push_config['server_chan']['sckey'] = os.environ.get('SERVER_SCKEY', push_config['server_chan'].get('sckey', ''))
    push_config['server_chan']['switch'] = os.environ.get('SERVER_CHAN_SWITCH', push_config['server_chan'].get('switch', 'OFF'))
    
    # PushPlus推送配置 - 环境变量优先级高于配置文件
    if 'pushplus' not in push_config:
        push_config['pushplus'] = {}
    
    push_config['pushplus']['token'] = os.environ.get('PUSHPLUS_TOKEN', push_config['pushplus'].get('token', ''))
    push_config['pushplus']['switch'] = os.environ.get('PUSHPLUS_SWITCH', push_config['pushplus'].get('switch', 'OFF'))
    
    # Telegram Bot推送配置 - 环境变量优先级高于配置文件
    if 'tg_bot' not in push_config:
        push_config['tg_bot'] = {}
    
    push_config['tg_bot']['token'] = os.environ.get('TELEGRAM_TOKEN', push_config['tg_bot'].get('token', ''))
    push_config['tg_bot']['group_id'] = os.environ.get('TELEGRAM_GROUP_ID', push_config['tg_bot'].get('group_id', ''))
    push_config['tg_bot']['switch'] = os.environ.get('TELEGRAM_SWITCH', push_config['tg_bot'].get('switch', 'OFF'))
    
    # 添加夜间休眠配置
    config['night_sleep'] = {
        'switch': os.environ.get('NIGHT_SLEEP_SWITCH', config.get('night_sleep', {}).get('switch', 'ON'))
    }
    
    config['push'] = push_config
    return config

# 判断是否应该进行夜间休眠
def should_sleep():
    # 加载配置
    config = load_config()
    # 检查是否开启夜间休眠功能
    sleep_switch = os.environ.get('NIGHT_SLEEP_SWITCH', config.get('night_sleep', {}).get('switch', 'ON'))
    if sleep_switch != 'ON':
        return False
    
    # 判断当前时间（北京时间）是否在0-7点之间
    # 获取当前UTC时间，转换为北京时间（UTC+8）
    now_utc = datetime.utcnow()
    # 转换为北京时间
    now_bj = now_utc.hour + 8
    # 处理跨天情况
    if now_bj >= 24:
        now_bj -= 24
    
    return now_bj < 7

# 初始化数据库
def init_database():
    conn = sqlite3.connect('articles.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        link TEXT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    conn.commit()
    return conn

# 获取数据并检查更新
def check_for_updates(feed_url, site_name, cursor, conn):
    print(f"{site_name} 监控中... ")
    data_list = []
    file_data = feedparser.parse(feed_url)
    data = file_data.entries
    if data:
        data_title = data[0].get('title')
        data_link = data[0].get('link')
        data_list.append(data_title)
        data_list.append(data_link)

        # 查询数据库中是否存在相同链接的文章
        cursor.execute("SELECT * FROM items WHERE link = ?", (data_link,))
        result = cursor.fetchone()
        if result is None:
            # 未找到相同链接的文章，进行推送
            push_message(f"{site_name}今日更新", f"title: {data_title}\n链接: {data_link}")

            # 存储到数据库 with a timestamp
            cursor.execute("INSERT INTO items (title, link, timestamp) VALUES (?, ?, CURRENT_TIMESTAMP)", (data_title, data_link))
            conn.commit()
    return data_list

# 推送函数
def push_message(title, content):
    config = load_config()
    push_config = config.get('push', {})
    
    # 钉钉推送
    if 'dingding' in push_config and push_config['dingding'].get('switch', '') == "ON":
        send_dingding_msg(push_config['dingding'].get('webhook'), push_config['dingding'].get('secret_key'), title,
                          content)

    # 飞书推送
    if 'feishu' in push_config and push_config['feishu'].get('switch', '') == "ON":
        send_feishu_msg(push_config['feishu'].get('webhook'), title, content)

    # Server酱推送
    if 'server_chan' in push_config and push_config['server_chan'].get('switch', '') == "ON":
        send_server_chan_msg(push_config['server_chan'].get('sckey'), title, content)

    # PushPlus推送
    if 'pushplus' in push_config and push_config['pushplus'].get('switch', '') == "ON":
        send_pushplus_msg(push_config['pushplus'].get('token'), title, content)

    # Telegram Bot推送
    if 'tg_bot' in push_config and push_config['tg_bot'].get('switch', '') == "ON":
        send_tg_bot_msg(push_config['tg_bot'].get('token'), push_config['tg_bot'].get('group_id'), title, content)

# 飞书推送
def send_feishu_msg(webhook, title, content):
    feishu(title, content, webhook)

# Server酱推送
def send_server_chan_msg(sckey, title, content):
    server(title, content, sckey)

# PushPlus推送
def send_pushplus_msg(token, title, content):
    pushplus(title, content, token)

# Telegram Bot推送
def send_tg_bot_msg(token, group_id, title, content):
    tgbot(title, content, token, group_id)

# 钉钉推送
def dingding(text, msg, webhook, secretKey):
    try:
        ding = cb.DingtalkChatbot(webhook, secret=secretKey)
        ding.send_text(msg='{}\r\n{}'.format(text, msg), is_at_all=False)
    except Exception as e:
        print(f"钉钉推送失败: {str(e)}")

# 飞书推送
def feishu(text, msg, webhook):
    try:
        headers = {
            "Content-Type": "application/json;charset=utf-8"
        }
        data = {
            "msg_type": "text",
            "content": {
                "text": '{}\n{}'.format(text, msg)
            }
        }
        response = requests.post(webhook, json=data, headers=headers, timeout=10)
        response.raise_for_status()
    except Exception as e:
        print(f"飞书推送失败: {str(e)}")

# 钉钉推送
def send_dingding_msg(webhook, secret_key, title, content):
    dingding(title, content, webhook, secret_key)

# Server酱推送
def server(text, msg, sckey):
    try:
        uri = 'https://sc.ftqq.com/{}.send?text={}&desp={}'.format(sckey, text, msg)  # 将 xxxx 换成自己的server SCKEY
        requests.get(uri, timeout=10)
    except Exception as e:
        pass


# PushPlus推送
def pushplus(text, msg, token):
    try:
        uri = 'https://www.pushplus.plus/send?token={}&title={}&content={}'.format(token, text, msg)  # 将 xxxx 换成自己的pushplus的 token
        requests.get(uri, timeout=10)
    except Exception as e:
        pass


# Telegram Bot推送
def tgbot(text, msg, token, group_id):
    import telegram
    try:
        bot = telegram.Bot(token='{}'.format(token))  # Your Telegram Bot Token
        bot.send_message(chat_id=group_id, text='{}\r\n{}'.format(text, msg))
    except Exception as e:
        pass

# 主函数
def main():
    banner = '''
    +-------------------------------------------+
                   安全社区推送监控
    使用说明：
    1. 修改config.yaml中的推送配置以及开关
    2. 修改rss.yaml中需要增加删除的社区
    3. 可自行去除或增加新的推送渠道代码到本脚本中
                      2023.10.10
                   Powered By：Pings
    +-------------------------------------------+
                     开始监控...
    '''

    print(banner)
    
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='安全社区文章监控脚本')
    parser.add_argument('--once', action='store_true', help='只执行一次，适合GitHub Action运行')
    args = parser.parse_args()
    
    conn = init_database()
    cursor = conn.cursor()
    rss_config = {}

    try:
        with open('rss.yaml', 'r', encoding='utf-8') as file:
            rss_config = yaml.load(file, Loader=yaml.FullLoader)
    except Exception as e:
        print(f"加载rss.yaml文件出错: {str(e)}")
        conn.close()
        return

    # 发送启动通知消息
    push_message("安全社区文章监控已启动!", f"启动时间：{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())}")

    try:
        if args.once:
            # 单次执行模式，适合GitHub Action
            print("使用单次执行模式")
            for website, config in rss_config.items():
                website_name = config.get("website_name")
                rss_url = config.get("rss_url")
                check_for_updates(rss_url, website_name, cursor, conn)
        else:
            # 循环执行模式，适合本地运行
            while True:
                try:
                    # 检查是否需要夜间休眠
                    if should_sleep():
                        sleep_hours = 7 - datetime.now().hour
                        print(f"当前时间在0-7点之间，将休眠{sleep_hours}小时")
                        time.sleep(sleep_hours * 3600)
                        continue
                    
                    for website, config in rss_config.items():
                        website_name = config.get("website_name")
                        rss_url = config.get("rss_url")
                        check_for_updates(rss_url, website_name, cursor, conn)

                    # 每二小时执行一次
                    time.sleep(10800)

                except Exception as e:
                    print("发生异常：", str(e))
                    time.sleep(60)  # 出现异常，等待1分钟继续执行
    except Exception as e:
        print("主程序发生异常：", str(e))
    finally:
        conn.close()
        print("监控程序已结束")

if __name__ == "__main__":
    main()