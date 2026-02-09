"""
Telegram 发送工具 - 直接使用 Bot API
"""
import os
import sys
from telegram import Bot

# 配置
TOKEN = "8308151445:AAEhS3oZ880gcA3-16-FfHMglzvZ2NalwK0"
CHAT_ID = 8260462836

def send_message(text):
    """发送文本消息"""
    try:
        bot = Bot(token=TOKEN)
        bot.send_message(chat_id=CHAT_ID, text=text, parse_mode='Markdown')
        print(f"✅ 消息发送成功")
        return True
    except Exception as e:
        print(f"❌ 发送失败: {e}")
        return False

def send_image(image_path, caption=""):
    """发送图片"""
    try:
        bot = Bot(token=TOKEN)
        with open(image_path, 'rb') as photo:
            bot.send_photo(chat_id=CHAT_ID, photo=photo, caption=caption)
        print(f"✅ 图片发送成功: {image_path}")
        return True
    except Exception as e:
        print(f"❌ 图片发送失败: {image_path}")
        print(f"   错误: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "test":
            # 测试消息
            send_message("✅ **ComicHub 配置测试成功！**\n\n正在准备发送漫画图片...")
        elif sys.argv[1] == "image" and len(sys.argv) > 2:
            # 发送图片
            send_image(sys.argv[2])
    else:
        print("用法:")
        print("  python telegram_helper.py test           # 测试发送")
        print("  python telegram_helper.py image <图片路径>  # 发送图片")
