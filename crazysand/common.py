import requests
from PIL import Image
from fake_useragent import UserAgent
from uuid import uuid4
import re
import os
from mysql.connector import pooling
import threading

"""
def parse_key_value_string_to_dict(string):
    lines = string.split('\n')
    print('{')
    for line in lines:
        key = line.split(': ')[0]
        value = line.split(': ')[1]
        try:
            print(f'\t"{key}": {int(value)},')
        except ValueError:
            print(f'\t"{key}": "{value}",')
    print('}')
"""

'''
from email.mime.text import MIMEText
from email.utils import formataddr
import smtplib
def send_email(subject, to, body):
    """
    发送邮箱

    参数：
    - subject: str, 邮件标题
    - to: str, 收件人邮箱地址
    - body: str, 正文内容(html)
    """
    # 使用MIMEText创建电子邮件内容，指定内容类型为HTML和字符编码为UTF-8
    msg = MIMEText(body, "html", "utf-8")

    # 设置发件人信息，包括发件人名字和邮箱地址
    msg["From"] = formataddr(("上海长乐集团", "2036166178@qq.com"))

    # 设置收件人邮箱地址
    msg['To'] = to

    # 设置电子邮件主题
    msg['Subject'] = subject

    # 使用SMTP_SSL连接到指定的SMTP服务器，这里使用的是QQ邮箱的SMTP服务器
    server = smtplib.SMTP_SSL("smtp.qq.com")

    # 登录SMTP服务器，使用邮箱地址和授权码
    server.login("2036166178@qq.com", "narrjhvzoujpcabc")

    # 发送邮件，参数分别为发件人邮箱地址，收件人邮箱地址，以及要发送的消息（转换为字符串格式）
    server.sendmail("2036166178@qq.com", to, msg.as_string())

    # 断开与SMTP服务器的连接
    server.quit()
'''


def set_proxy(ip='127.0.0.1', port='10809'):
    """设置代理"""
    os.environ['HTTP_PROXY'] = f'http://{ip}:{port}'
    os.environ['HTTPS_PROXY'] = f'http://{ip}:{port}'


def change_to_script_parent_directory():
    """
    把工作路径更改为脚本所在的绝对父目录
    """
    # 获取当前脚本文件的绝对路径
    file_path = os.path.abspath(__file__)

    # 获取当前脚本文件所在的父级文件夹路径
    parent_directory = os.path.dirname(file_path)

    # 将当前工作目录更改为父级文件夹
    os.chdir(parent_directory)


def normalized_filename(string):
    """规范文件名"""
    pattern = r"[^a-zA-Z0-9\u4E00-\u9FA5]+"  # 匹配非汉字数字英文的字符
    return re.sub(pattern, "_", string)


def resize_image(original_image_path, output_image_path=None, target_width=None, target_height=None):
    """
    调整图像的大小（主要根据宽或高自动调节图像比例）

    参数:
    - original_image_path: str, 原始图像的文件路径。
    - output_image_path: str, 可选，调整大小后图像的保存路径。如果未提供，则覆盖原图。
    - target_width: int, 可选，目标图像的宽度。如果只提供了宽度，高度将按照原图的宽高比自动计算。
    - target_height: int, 可选，目标图像的高度。如果只提供了高度，宽度将按照原图的宽高比自动计算。

    如果同时提供了宽度和高度，则按照这两个参数调整图像尺寸，但这可能会导致图像的宽高比改变。
    如果没有提供任何宽度和高度参数，函数将不执行任何操作。
    """
    with Image.open(original_image_path) as img:
        w, h = img.size  # 获取原始图像的宽度和高度
        r = w / h  # 计算原始图像的宽高比

        # 根据输入参数调整图像尺寸
        if target_width and not target_height:
            # 只输入目标宽度：高度按比例缩放
            nw = target_width
            nh = int(nw / r)
        elif target_height and not target_width:
            # 只输入目标高度：宽度按比例缩放
            nh = target_height
            nw = int(nh * r)
        elif target_width and target_height:
            # 同时输入宽度和高度
            nw, nh = target_width, target_height
        else:
            # 无宽高输入，不执行操作
            return

        img_resized = img.resize((nw, nh))  # 调整图像大小
        if output_image_path:
            # 如果提供了输出路径，保存调整后的图像
            img_resized.save(output_image_path)
        else:
            # 如果未提供输出路径，覆盖原图
            img_resized.save(original_image_path)


class MySQLPoolSingleton:
    """
    连接 Mysql数据库(多线程flask环境，上锁，连接池，单例模式)
    """
    _instance = None  # 类变量，用于存储单例实例。
    _connection_pool = None  # 类变量，用于存储数据库连接池。
    _lock = threading.Lock()  # 用于线程锁，确保线程安全的单例实现。

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:  # 检查是否已存在实例
            with cls._lock:  # 使用线程锁
                if cls._instance is None:  # 再次检查以确保实例仍然不存在
                    # 如果不存在，则创建一个新的实例
                    cls._instance = super(MySQLPoolSingleton, cls).__new__(cls)
        return cls._instance  # 返回单例实例

    def __init__(self, pool_name, pool_size, host, database, user, password):
        if self._connection_pool is None:  # 检查连接池是否已被创建。
            # 创建新的连接池。
            self._connection_pool = pooling.MySQLConnectionPool(
                pool_name=pool_name,  # 连接池名称。
                pool_size=pool_size,  # 连接池大小。
                pool_reset_session=True,  # 重置会话。
                host=host,  # 数据库主机地址。
                database=database,  # 数据库名。
                user=user,  # 数据库用户名。
                password=password  # 数据库密码。
            )

    @property
    def connection(self):
        # 从连接池中获取一个新的连接。
        return self._connection_pool.get_connection()


class SourceRequest:

    @staticmethod
    def image(url, parent_path='./', name=None, suffix='.jpg'):
        if not name:
            name = str(uuid4())
        path = parent_path + name + suffix
        response = requests.get(url, headers={'User-Agent': UserAgent().random})
        with open(path, 'wb') as f:
            f.write(response.content)
        return path

    @staticmethod
    def audio(url, parent_path='./', name=None, suffix='.mp3'):
        if not name:
            name = str(uuid4())
        path = parent_path + name + suffix
        response = requests.get(url, headers={'User-Agent': UserAgent().random})
        with open(path, 'wb') as f:
            f.write(response.content)
        return path

    @staticmethod
    def video(url, parent_path='./', name=None, suffix='.mp4'):
        if not name:
            name = str(uuid4())
        path = parent_path + name + suffix
        response = requests.get(url, headers={'User-Agent': UserAgent().random})
        with open(path, 'wb') as f:
            f.write(response.content)
        return path

    @staticmethod
    def html(url, parent_path='./', name=None, suffix='html'):
        if not name:
            name = str(uuid4())
        path = parent_path + name + suffix
        response = requests.get(url, headers={'User-Agent': UserAgent().random})
        with open(path, 'w', encoding='utf-8') as f:
            f.write(response.text)
        return path
