# 🌟 SeleniumChatGPT - ChatGPT Automation Client 🚀

[![Docker Pulls](https://img.shields.io/docker/pulls/leviosa/selenium-gpt)](https://hub.docker.com/r/leviosa/selenium-gpt)  
[![License](https://img.shields.io/github/license/qvqq/SeleniumChatGPT)](LICENSE)


### 🌟 项目特性

- 🐳 **Docker 镜像支持**：一行命令即可拉取并运行！  
- 🌐 **noVNC 支持**：可在浏览器中查看具体的模拟过程！  
- 🔒 **支持 OpenAI 和 Microsoft 账号登录**。  
- ⚙️ **支持代理配置**：可自由设置代理地址。  
- 🧠 **功能切换**：支持切换模型、获取回复、重新生成、切换 Temporary 模式。  
- 📊 **美观的命令行界面**：操作流畅且直观。  
- ✅ **安全无风险**：个人项目，已使用半年，无风险。  
- 🔓 **绕过 CloudFlare 验证**：使用 `undetected-chromedriver` 通过 OpenAI 的前端验证。

🎥 **演示视频**：  

https://github.com/user-attachments/assets/37ac580b-955e-4586-899b-ba092c046726


📸 **使用效果示例**：  

<img width="1368" alt="Xnip2024-09-27_15-26-49" src="https://github.com/user-attachments/assets/f13a0b53-d092-4fa4-b842-f973e0b4c046">


---

### 🚀 使用方法

1. **克隆仓库并安装依赖**  
   ```bash
   git clone https://github.com/QvQQ/SeleniumChatGPT.git
   cd SeleniumChatGPT
   pip install -r requirements.txt
   ```

2. **修改 client_config.yaml**  
   将 `client_config_template.yaml` 复制为 `client_config.yaml`，并根据需要修改：
   ```bash
   cp client_config_template.yaml client_config.yaml
   ```
   配置文件示例：
   ```yaml
   # docker 容器的地址，如果是本地
   # e.g. http://127.0.0.1:15001
   base_url: ''

   # 登录方式。微软账号选'Microsoft'，OpenAI账号选'OpenAI'
   login_type: 'Microsoft'

   # 账号对应的邮箱及密码
   email: ''
   password: ''

   # 用来解决 CloudFlare 验证的服务，目前未用到
   capsolver_client_key: null

   # 浏览器是否是 headless 模式。建议选 false，否则可能弹出 CloudFlare 验证
   headless: false

   # Chrome 的用户数据目录的名字
   user_data_dir: 'user_data_dir'
   ```

3. **修改 Docker 设置**  
   根据需要修改 `docker-compose.yml` 文件，后端默认监听 `15001` 端口，代理设置可选。

   (Optional) 如果你在 Linux 系统上运行，并希望直接显示浏览器窗口，可以使用 `xhost` 配置主机运行权限，允许 Docker 容器访问主机的 X 服务器。运行以下命令：
   ```bash
   DISPLAY=:0 xhost +
   ```
   然后修改 `docker-compose.yml` 文件中的 `DISPLAY` 变量为 `:0`（或你当前的显示设置）：
   ```yaml
   environment:
     DISPLAY: ":0"
   ```
   并在 `volumes` 中添加以下内容：
   ```yaml
   vomumes:
     - /tmp/.X11-unix:/tmp/.X11-unix
   ```

5. **启动服务**  
   使用 Docker Compose 启动服务：
   ```bash
   docker-compose up
   ```

6. **使用 noVNC**  
   在浏览器中访问 `http://127.0.0.1:7900/?autoconnect=1&resize=scale&password=secret`（默认密码：`secret`）。

7. **开始体验！**  
   运行 `SeleniumChatGPTClient.py` 查看模拟过程，享受自动化的 ChatGPT 体验！

---

🛠️ **License**: MIT  
👨‍💻 **Contributions**: Welcome! Feel free to open issues or pull requests.
