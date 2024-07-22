#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import signal
# import subprocess
import time
from typing import Optional

# for logging
import logging
from rich.console import Console
from rich.logging import RichHandler

# others
from box import Box
from flask import Flask, request, jsonify
from SeleniumChatGPT import SeleniumChatGPT

app = Flask(__name__)
app.config['TEARDOWN'] = False
app.config['LAST_REQUEST_TIME'] = time.time()
app.config['MAX_IDLE_SECONDS'] = 3600

client: Optional[SeleniumChatGPT] = None

# ------------------------------------------------------------------------------------
# 创建一个Rich的Console对象
console = Console(width=104)

# 配置日志，使用RichHandler
logging.basicConfig(
    level="INFO",  # 设置日志级别
    format="%(message)s",  # 设置日志格式
    datefmt="%x %X",  # 设置时间格式
    handlers=[RichHandler(console=console, rich_tracebacks=True, markup=True, show_path=False)]  # 使用RichHandler
)

# ------------------------------------------------------------------------------------
# 配置 Flask 的日志输出，防止与 RichHandler 冲突
werkzeug_logger = logging.getLogger('werkzeug')

# 移除所有现有的处理器（如果有的话）
werkzeug_logger.handlers = []

# 创建一个纯文本格式的日志处理器
plain_text_handler = logging.StreamHandler()
plain_text_handler.setFormatter(logging.Formatter(fmt="%(message)s"))

# 添加新的处理器到 logger
werkzeug_logger.addHandler(plain_text_handler)

# 确保 werkzeug logger 不会向上传播日志
werkzeug_logger.propagate = False

# 禁用 werkzeug 的日志
# logging.getLogger('werkzeug').disabled = True


# ------------------------------------------------------------------------------------
# 关掉自己
@app.route('/shutdown', methods=['POST'])
def shutdown():
    global client

    if client and client.quit():  # noqa
        console.log("[bold green][Flask][/] [bold yellow]Client reset![/]")
        client = None
    else:
        # 退出浏览器失败了，只能关掉自己了
        console.log("[bold green][Flask][/] [bold red]Client reset failed![/]")
        # subprocess.Popen(f'sleep 2; kill -2 {os.getpid()}', shell=True)  # Popen 非阻塞，run 阻塞
        app.config['TEARDOWN'] = True

    return jsonify({"code": 200, "message": "Closed.", "data": {}}), 200


@app.teardown_request
def teardown_request_func(error=None):
    if app.config['TEARDOWN']:
        console.log("[bold green][Flask][/] [bold red]Shutting down the server...[/]")
        os.kill(os.getpid(), signal.SIGINT)


# ------------------------------------------------------------------------------------
# 处理错误
def handle_error(e: BaseException):
    console.log(f"[bold green][Flask][/] [bold red]Error Message: {repr(e)}[/]")
    shutdown()
    return jsonify({"code": 400, "message": repr(e), "data": {}}), 400


# ------------------------------------------------------------------------------------
# 更新上次请求时间
@app.after_request
def after_request_func(response):
    app.config['LAST_REQUEST_TIME'] = time.time()
    return response


def refresh_if_needed() -> None:
    if time.time() - app.config['LAST_REQUEST_TIME'] > app.config['MAX_IDLE_SECONDS']:
        if client:
            console.log(f"[bold green][Flask][/] [bold]Last request time: {time.strftime('%x %X', time.localtime(app.config['LAST_REQUEST_TIME']))}.[/]")
            console.log(f"[bold green][Flask][/] [bold yellow]Refreshing...[/]")
            client.refresh_page()


# ------------------------------------------------------------------------------------
@app.route('/start_client', methods=['POST'])
def start_client():
    global client

    if client:
        refresh_if_needed()
        return jsonify({"code": 201, "message": "Client already exists!", "data": {}}), 201

    try:
        # 解析传入参数
        data = Box(request.get_json(), frozen_box=True)

        # 创建 client
        client = SeleniumChatGPT(
            email=data.email,
            password=data.password,
            login_type=data.login_type,
            capsolver_client_key=data.capsolver_client_key,
            headless=data.headless,
            user_data_dir=data.user_data_dir,
        )
        return jsonify({"code": 200, "message": f"Client created.", "data": {}}), 200

    except Exception as e:
        return handle_error(e)


@app.route('/reset_to_specified_mode', methods=['POST'])
def reset_to_specified_mode():

    if not client:
        return jsonify({"code": 404, "message": "Client not found", "data": {}}), 404

    try:
        # 解析传入参数
        data = Box(request.get_json(), frozen_box=True)

        # 跳转页面到特定模型和临时模式
        client.reset_to_specified_mode(model=data.model, temporary_mode=data.temporary_mode)
        return jsonify({"code": 200, "message": f"Model reset to {data.model} with temporary mode {'ON' if data.temporary_mode else 'OFF'}.", "data": {}}), 200

    except Exception as e:
        return handle_error(e)


@app.route('/switch_model', methods=['POST'])
def switch_model():

    if not client:
        return jsonify({"code": 404, "message": "Client not found", "data": {}}), 404

    try:
        # 解析传入参数
        data = Box(request.get_json(), frozen_box=True)

        # 切换模型
        client.switch_model(data.target_model)
        return jsonify({"code": 200, "message": f"Model switched to {data.target_model}", "data": {}}), 200

    except Exception as e:
        return handle_error(e)


@app.route('/switch_temporary_mode', methods=['POST'])
def switch_temporary_mode():

    if not client:
        return jsonify({"code": 404, "message": "Client not found", "data": {}}), 404

    try:
        # 解析传入参数
        data = Box(request.get_json(), frozen_box=True)

        # 切换模型
        client.switch_temporary_mode(data.temporary)
        return jsonify({"code": 200, "message": f"The 'Temporary Mode' switched to {data.temporary}", "data": {}}), 200

    except Exception as e:
        return handle_error(e)


@app.route('/new_chat', methods=['POST'])
def new_chat():

    if not client:
        return jsonify({"code": 404, "message": "Client not found", "data": {}}), 404

    try:
        # 刷新页面（如果需要的话）
        refresh_if_needed()

        # 重置会话，开启新会话
        client.new_chat()
        return jsonify({"code": 200, "message": f"The 'New Chat' started.", "data": {}}), 200

    except Exception as e:
        return handle_error(e)


@app.route('/regenerate', methods=['POST'])
def regenerate():

    if not client:
        return jsonify({"code": 404, "message": "Client not found", "data": {}}), 404

    try:
        # 交互获得重新生成后的答案
        answer = client.regenerate()
        return jsonify({"code": 200, "message": f"Regenerate completed.", "data": {"answer": answer}}), 200

    except Exception as e:
        return handle_error(e)


@app.route('/chat', methods=['POST'])
def chat():

    if not client:
        return jsonify({"code": 404, "message": "Client not found", "data": {}}), 404

    try:
        # 解析传入参数
        data = Box(request.get_json(), frozen_box=True)

        # 交互获得 answer
        answer = client.chat(data.question)
        return jsonify({"code": 200, "message": f"Chat completed.", "data": {"answer": answer}}), 200

    except Exception as e:
        return handle_error(e)


if __name__ == '__main__':

    # 在使用 docker run 命令启动容器时，可以使用 -e 标志传递环境变量。
    # 从环境变量获取端口号，默认使用 5000 端口
    port = int(os.getenv('PORT', 15001))
    display = os.getenv('DISPLAY', ':99')
    http_proxy = os.getenv('http_proxy') or os.getenv('HTTP_PROXY')

    console.log(f'[bold green][Flask][/] [bold]PORT = {port}[/]')
    console.log(f'[bold green][Flask][/] [bold]DISPLAY = {display}[/]')
    console.log(f'[bold green][Flask][/] [bold]HTTP_PROXY = {http_proxy}[/]')

    app.run(host='0.0.0.0', port=15001, threaded=False)
