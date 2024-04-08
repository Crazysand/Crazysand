from socket import *
from threading import Thread
import os
import logging
import mimetypes

"""
Content-Type是HTTP头部之一，用于指示资源的媒体类型（即MIME类型）。
MIME类型是一种标准化的方式来表示文档、文件或字节流的性质和格式。下面列出了一些常见的MIME类型及其用途：

文本类型：
    text/html：HTML格式的文档，用于网页。
    text/plain：纯文本，不含任何格式。
    text/css：层叠样式表（CSS）。
    text/javascript：JavaScript代码。
    
图像类型：
    image/jpeg：JPEG格式的图片。
    image/png：PNG格式的图片。
    image/gif：GIF格式的图片。
    image/svg+xml：SVG格式的矢量图。
    
应用程序类型：
    application/json：JSON格式的数据。
    application/xml：XML文档。有时也可以用text/xml。
    application/pdf：PDF格式的文档。
    application/msword：Microsoft Word文档。
    application/octet-stream：任意的二进制数据。
    
音视频类型：
    video/mp4：MP4格式的视频。
    audio/mpeg：MP3格式的音频。
    audio/ogg：OGG格式的音频或视频。
    
多用途类型：
    multipart/form-data：用于表单提交时包含文件上传。
    multipart/byteranges：状态码206（部分内容）响应中，表示响应体是文档的一部分或多个部分。
    这只是MIME类型的一小部分
"""

WEB_ROOT = 'C:\\Users\\20361\\Desktop\\'  # 静态文件存放目录
HOST = '0.0.0.0'
PORT = 80


def get_local_ipv4():
    # 创建UDP套接字
    sock = socket(AF_INET, SOCK_DGRAM)

    try:
        # 连接到公共的DNS服务器
        sock.connect(('8.8.8.8', 80))

        # 获取本地IP地址
        local_ip = sock.getsockname()[0]

        return local_ip
    except error:
        return None
    finally:
        sock.close()


def get_content_type(file_path):
    """
    根据文件路径返回其MIME类型
    """
    # 使用mimetypes猜测文件类型
    ctype, _ = mimetypes.guess_type(file_path)
    if ctype is None:
        ctype = 'application/octet-stream'  # 默认类型
    return ctype


def get_logger():
    """创建一个记录器，用于输出日志信息"""
    logger = logging.getLogger('example_logger')
    logger.setLevel(logging.DEBUG)
    # 创建一个处理器，用于将日志输出到控制台
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    # 创建一个格式化器，并设置到处理器上
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    return logger


class StaticWebServer:

    def __init__(self, host, port, web_root):
        self.host = host
        self.port = port
        self.web_root = web_root
        self.logger = get_logger()

    def start_server(self):
        """无限循环处理客户端请求"""
        print('服务已启动：' + WEB_ROOT + ' -> ' + f"http://{get_local_ipv4()}:{str(PORT)}/")
        # 创建服务端套接字对象
        server_socket = socket(AF_INET, SOCK_STREAM)
        # 端口复用
        server_socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        # 绑定地址和端口
        server_socket.bind((self.host, self.port))
        # 允许的客户端最大的同时连接数，超出的等待
        server_socket.listen(128)

        while True:
            # 客户端连接时，获取会话套接字和客户端地址
            session_socket, addr = server_socket.accept()
            # 多线程处理客户端请求
            Thread(target=self._handle_request, args=(session_socket, addr)).start()

    def _create_http_response(self, status_code, body, content_type):
        """
        构建HTTP响应字符串。

        HTTP响应的组成部分:
            状态行：包含HTTP版本、状态码和状态消息。例如，HTTP/1.1 200 OK 表示请求成功。
            响应头部：包含关于响应的元数据，如内容类型（Content-Type）和内容长度（Content-Length）。
            空行：头部和消息体之间必须有一个空行。
            消息体：实际的响应内容，比如HTML文件。
        """
        # HTTP状态消息
        status_messages = {
            200: "OK",
            404: "Not Found",
            500: "Internal Server Error",
            403: "Forbidden",
            400: "Bad Request",
            301: "Moved Permanently",
        }

        # 构建状态行
        status_line = f"HTTP/1.1 {status_code} {status_messages.get(status_code, 'Unknown')}\r\n"

        # 构建响应头部
        headers = f"Content-Type: {content_type}; charset=UTF-8\r\n"
        headers += f"Content-Length: {len(body)}\r\n"

        # 组合状态行、头部和消息体
        response = (status_line + headers + "\r\n").encode('utf-8') + body

        return response

    def _handle_request(self, session_socket, addr):
        """处理客户端请求"""
        # 接收并解码客户端信息
        request = session_socket.recv(1024).decode('utf-8')

        # 请求头
        lines = request.splitlines()
        # 若请求头无效，立刻返回
        if not lines:
            session_socket.close()
            return
        request_line = lines[0]
        # 获取请求方法、路径和HTTP版本
        method, path, _ = request_line.split()

        file_path = self.web_root + path

        try:
            # 文件路径存在并且不是文件夹
            if os.path.exists(file_path) and not os.path.isdir(file_path):
                self.logger.info(f'[{addr[0]}:{addr[1]}] {method} {path} - 200 OK')
                with open(file_path, 'rb') as file:
                    response_body = file.read()
                content_type = get_content_type(file_path)
                response = self._create_http_response(200, response_body, content_type)
            # 文件路径不存在或者是文件夹
            else:
                self.logger.warning(f'[{addr[0]}:{addr[1]}] {method} {path} - 404 Not Found')
                response_body = b"404 Not Found"
                response = self._create_http_response(404, response_body, 'text/plain')
        # 服务器内部错误
        except Exception as e:
            self.logger.error(f"Error processing request: {e}")
            response_body = b"500 Internal Server Error"
            response = self._create_http_response(500, response_body, 'text/plain')

        session_socket.sendall(response)
        # 关闭会话套接字
        session_socket.close()


if __name__ == '__main__':
    sws = StaticWebServer(HOST, PORT, WEB_ROOT)
    sws.start_server()
