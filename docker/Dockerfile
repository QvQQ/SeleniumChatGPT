
# 使用 Selenium 的官方基础镜像
FROM selenium/standalone-chromium:latest

# 作者信息
LABEL author="QvQQ"
LABEL github="https://github.com/QvQQ"
LABEL version="1.0"

# 定义一个用于接收构建平台的 ARG
ARG TARGETPLATFORM

# 设置工作目录
WORKDIR /home/seluser/

# 切换到 root
USER seluser

# 更换镜像源
# RUN sudo sed -i \
#     -e 's|http://ports.ubuntu.com/ubuntu-ports|https://mirrors.tuna.tsinghua.edu.cn/ubuntu-ports|g' \
#     -e 's|http://archive.ubuntu.com/ubuntu|https://mirrors.tuna.tsinghua.edu.cn/ubuntu|g' \
#     -e 's|http://deb.debian.org/debian|https://mirrors.tuna.tsinghua.edu.cn/debian|g' \
#     /etc/apt/sources.list

# 安装语言包、设置 locale 为中文
#RUN sudo apt-get update \
#    && sudo apt-get install -y locales \
#    && echo "zh_CN.UTF-8 UTF-8" | sudo tee -a /etc/locale.gen \
#    && sudo locale-gen zh_CN.UTF-8 \
#    && sudo update-locale LANG=zh_CN.UTF-8

# ENV LANG=zh_CN.UTF-8
# ENV LANGUAGE=zh_CN:zh
# ENV LC_ALL=zh_CN.UTF-8
ENV PATH="${PATH}:/home/seluser/.local/bin"

# 安装 pip 并安装 python 依赖
#RUN sudo chown -R seluser:seluser /home/seluser/.local \
# RUN     curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py \
    # && python3 get-pip.py \
    # && rm get-pip.py \
# RUN sudo apt install -y python3-pip \
#     && pip config set global.index-url 'https://pypi.tuna.tsinghua.edu.cn/simple' \
#     && pip install --no-cache-dir -r /home/seluser/requirements.txt

RUN sudo apt-get update \
    && sudo apt-get install -y expect xclip python3-venv \
    && sudo rm -rf /var/lib/apt/lists/* \
    && sudo apt autoremove -y

# 更改 superviosr 的运行命令
RUN sudo sed -i \
    -e '\|command=bash -c "/opt/bin/start-selenium-standalone.sh;|a environment=TERM="xterm-256color"' \
    -e 's|command=bash -c "/opt/bin/start-selenium-standalone.sh;|command=bash -ic "sudo -E unbuffer /home/seluser/venv/bin/python3 SeleniumChatGPTServer.py;|' \
    /etc/supervisor/conf.d/selenium.conf

# 创建虚拟环境并安装依赖项
COPY ./requirements.txt /home/seluser/

RUN python3 -m venv /home/seluser/venv \
    && . /home/seluser/venv/bin/activate \
    && pip config set global.index-url 'https://pypi.tuna.tsinghua.edu.cn/simple' \
    && pip install --no-cache-dir -r /home/seluser/requirements.txt

# 使用 sed 命令删除指定行
RUN sudo sed -i \
    -e '/options.add_argument("--window-size=1920,1080")/d' \
    -e '/options.add_argument("--start-maximized")/d' \
    /home/seluser/venv/lib/python3.12/site-packages/undetected_chromedriver/__init__.py

# 运行 undetected_chromedriver 的 Patcher 自动下载 Chromedriver
RUN sudo /home/seluser/venv/bin/python3 -c "from undetected_chromedriver import Patcher; import logging; logging.basicConfig(level='DEBUG'); Patcher(executable_path='/usr/bin/chromedriver').auto()"

# 复制程序文件到工作目录 (较后放这个，因为如果文件内容变动，那么从COPY之后的层都会重新构建)
RUN mkdir -p /home/seluser/debug
COPY ./SeleniumChatGPT.py ./SeleniumChatGPTServer.py ./SeleniumDriverHelper.py /home/seluser/
#COPY ./CapSolver.Browser.Extension-chrome /home/seluser/CapSolver.Browser.Extension-chrome

# 运行 Python 脚本
CMD ["/opt/bin/entry_point.sh"]

