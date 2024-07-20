#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import shutil
import time
from typing import Literal, Optional

# for selenium
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By

# for log
import logging

# from extension config file lock
from filelock import Timeout, FileLock

# for selenium helper
from SeleniumDriverHelper import SeleniumDriverHelper

# for copy assistant answer into clipboard
import pyperclip

# for retry
import tenacity


# ------------------------------------------------------------------------------------
class SeleniumChatGPT:

    # !!! data-testid 可能会变化 !!!
    # 聊天页面 ############################################################
    ## 顶部右侧的登录按钮
    xpath_chat__login_button = '//button[not(@data-testid) and ./div[text()="Log in"]]'
    ## Welcome 弹出框界面的登录按钮
    xpath_chat__welcome_login_button = '//button[@data-testid="welcome-login-button" and ./div[text()="Log in"]]'

    ## 底部输入框
    xpath_chat__prompt_textarea = '//textarea[@id="prompt-textarea"]'
    ## 输入框右边的发送按钮
    # xpath_chat__send_button_enabled  = '//button[contains(@data-testid, "send-button") and not(@disabled)]'
    xpath_chat__send_button_enabled  = "//textarea[@id='prompt-textarea']/ancestor::div[1]/following-sibling::button[not(@disabled) and ./*[local-name()='svg']/*[local-name()='path']][1]"
    # xpath_chat__send_button_disabled = '//button[contains(@data-testid, "send-button") and @disabled]'
    xpath_chat__send_button_disabled  = "//textarea[@id='prompt-textarea']/ancestor::div[1]/following-sibling::button[@disabled and ./*[local-name()='svg']/*[local-name()='path']][1]"
    ## 输入框右边的停止生成按钮
    # xpath_chat__stop_button = '//button[contains(@data-testid, "stop-button")]'
    xpath_chat__stop_button = "//textarea[@id='prompt-textarea']/ancestor::div[1]/following-sibling::button[not(@disabled) and ./*[local-name()='svg']/*[local-name()='rect']][1]"
    ## 生成出现错误时的 Regenerate 按钮
    xpath_chat__error_regenerate_button = '//button[div[text()="Regenerate"]]'
    ## 滚动到底部按钮
    xpath_chat__scroll_to_bottom_button = "//button[contains(@class, 'cursor-pointer') and contains(@class, 'absolute')]"

    ## 所有会话消息的 div 列表（包含用户消息）
    xpath_chat__conversation_turn_divs = "//div[starts-with(@class, 'react-scroll-to-bottom--css')]//div[starts-with(@data-testid, 'conversation-turn-')]"

    ## 最后一条会话消息 (assistant) 的 外部 div (包含空、错误、正常三种)
    xpath_chat__conversation_last_assistant_turn_outer_div = "//div[starts-with(@class, 'react-scroll-to-bottom--css')]//div[starts-with(@data-testid, 'conversation-turn-') and @data-scroll-anchor='true' and //div[@data-message-author-role='assistant']]"
    ## 最后一条会话消息 (assistant) 的 内部 div (正常消息)
    xpath_chat__conversation_last_assistant_turn_inner_div = xpath_chat__conversation_last_assistant_turn_outer_div + "//div[contains(@class, 'markdown')]"
    ## 最后一条会话消息 (assistant) 的 内部 div (错误消息)
    xpath_chat__conversation_error_message_p = xpath_chat__conversation_last_assistant_turn_outer_div + "//div[contains(@class, 'border-token-surface-error')]//p"

    ## 指定会话消息 (assistant) 的 外部 div (包含空、错误、正常三种)
    xpath_chat__conversation_specified_assistant_turn_outer_div = "//div[starts-with(@class, 'react-scroll-to-bottom--css')]//div[@data-testid='conversation-turn-{turn}' and @data-scroll-anchor='true' and //div[@data-message-author-role='assistant']]"
    ## 指定会话消息 (assistant) 的 内部 div (正常消息)
    xpath_chat__conversation_specified_assistant_turn_inner_div = xpath_chat__conversation_specified_assistant_turn_outer_div + "//div[contains(@class, 'markdown')]"
    ## 指定会话消息 (assistant) 的 内部 div (错误消息)
    xpath_chat__conversation_specified_error_message_p = xpath_chat__conversation_specified_assistant_turn_outer_div + "//div[contains(@class, 'border-token-surface-error')]//p"

    ## 最后一条会话消息 (assistant) 底部的四个按钮
    xpath_chat__conversation_last_assistant_turn_action_buttons = xpath_chat__conversation_last_assistant_turn_outer_div + "//div[count(span)=4]/span"
    ## 最后一条会话消息 (assistant) 底部的复制按钮 (假定在第 2 个)
    xpath_chat__conversation_last_assistant_turn_copy_button = xpath_chat__conversation_last_assistant_turn_action_buttons + "[2]"
    ## 最后一条会话消息 (assistant) 底部的重新生成按钮 (假定在第 3 个)
    xpath_chat__conversation_last_assistant_turn_regenerate_button = xpath_chat__conversation_last_assistant_turn_action_buttons + "[3]"


    ## 模型选择菜单
    xpath_chat__model_menu_div = "//div[@aria-haspopup='menu' and starts-with(@id, 'radix-:')]"
    ## 模型选择菜单中的模型名
    xpath_chat__model_menuitem_div = "//div[@role='menu' and @data-state='open']//div[@role='menuitem']//div[text()='{}']"
    xpath_chat__model_menuitem_divs = "//div[@role='menu' and @data-state='open']//div[@role='menuitem']//div[not(@class) and text()]"
    ## 模型选择菜单中的临时会话开关
    xpath_chat__model_temporary_div = "//div[@role='menu' and @data-state='open']//div[@role='menuitem']//button[@role='switch' and @aria-label='Temporary']"

    ## 开启新会话按钮 (假定是模型选择菜单的下一个兄弟节点)
    xpath_chat__new_chat_div = xpath_chat__model_menu_div + '/following-sibling::*[1]//button'

    # 登录页面 ############################################################
    ## 欢迎标识
    xpath_login__welcome_label = '//h1[text()="Welcome back"]'
    ## 输入框
    xpath_login__email_input = '//input[@name="email"]'
    xpath_login__password_input = '//input[@name="password"]'
    ## '继续' 按钮
    xpath_login__continue_button = '//button[text()="Continue"]'
    ## 微软登录按钮
    xpath_login__microsoft_login_button = '//button[span[text()="Continue with Microsoft Account"]]'

    # 微软登录页面 #########################################################
    ## 输入框
    xpath_microsoft_login__email_input = '//input[@name="loginfmt" and @type="email" and @id="i0116"]'
    xpath_microsoft_login__password_input = '//input[@name="passwd" and @type="password"]'
    ## 'Next' 按钮
    xpath_microsoft_login__next_button = '//button[text()="Next"]'
    ## 'Sign in' 按钮
    xpath_microsoft_login__signin_button = '//button[text()="Sign in"]'
    ## 维持登录提示
    xpath_microsoft_login__StaySignedIn_label = '//div[@role="heading" and text()="Stay signed in?"]'
    ## 不再提示
    xpath_microsoft_login__DontShowAgain_checkbox = '//input[@name="DontShowAgain" and @type="checkbox"]'
    ## 'Yes' 按钮
    xpath_microsoft_login__yes_button = '//button[text()="Yes"]'

    # 登录错误页面 #########################################################
    xpath_failed_login__message_label = '//div[text()="Oops!"]/following-sibling::div[1]'
    xpath_cloudflare__verification_div = '//div[@id=challenge-stage]'

    def __init__(
        self,
        email: str, password: str,
        login_type: Literal['OpenAI', 'Microsoft'],
        capsolver_client_key: Optional[str] = None,
        headless: bool = False,
        user_data_dir: Optional[str] = None,
    ):
        # 设置 logger
        self._logger = logging.getLogger(self.__class__.__name__)

        # console 宽度
        self._console_width = 104

        # chrome启动参数
        options = uc.ChromeOptions()

        # 用户数据路径
        if user_data_dir:
            profile_name = 'Profile_1'
            user_data_dir = os.path.abspath(user_data_dir)
            self._logger.info(f"[cyan]Using user_data_dir: {user_data_dir} with profile '{profile_name}'[/]")

            options.add_argument(f'--user-data-dir={user_data_dir}')
            options.add_argument(f"--profile-directory={profile_name}")

            # 尝试删除除了 {user-data-dir}/{profile-directory} 外的其他所有文件/目录
            self._delete_except_profile(user_data_dir, profile_name)
            self._logger.info(f"[cyan]Deleted all files except profile '{profile_name}'.[/]")

        # 禁用保存密码的提示框
        options.add_experimental_option("prefs", {
            "credentials_enable_service": False,
            "profile.password_manager_enabled": False
        })

        # 禁用共享内存（这个选项用于解决在运行Chrome时，由于/dev/shm（共享内存）空间不足而导致的问题。）
        options.add_argument('--disable-dev-shm-usage')

        # 禁用信息栏
        options.add_argument("--disable-infobars")

        # 禁用自动填充
        options.add_argument("--disable-autofill")

        # 设置窗口大小
        options.add_argument("--window-size=640,660")

        # 设置窗口初始位置
        options.add_argument("--window-position=0,0")

        # 检查是否存在http_proxy环境变量
        http_proxy = os.getenv('http_proxy') or os.getenv('HTTP_PROXY')
        if http_proxy:
            self._logger.info(f"[cyan]Using proxy {http_proxy}[/]")
            options.add_argument(f'--proxy-server={http_proxy}')

        # 加载 CapSolver 插件
        self._load_capsolver_extension(options, capsolver_client_key)

        # 以 app 方式访问 about:blank
        options.add_argument('--app=http://example.com')

        # 开始加载 undetected chrome
        self._logger.info('[cyan]Loading undetected Chrome...')

        # 检查是否已有 Patcher
        # patched_driver = uc.Patcher().executable_path  # 自动 patch
        patched_driver = '/usr/bin/chromedriver'  # 手动指定 chromedriver 路径

        if not os.path.exists(patched_driver):
            self._logger.warning('No patched driver found!')
            patched_driver = None
        else:
            self._logger.info(f'Found patched driver: {patched_driver}')

        # 实例化 driver
        try:
            self._browser = uc.Chrome(
                driver_executable_path=patched_driver,  # 如果不指定 executable_path 的位置，那么就会重复进行 Patch
                options=options,
                headless=headless,
                log_level=logging.WARNING
            )
            self._logger.info('[cyan]Loaded Undetected chrome![/]')

        except Exception as e:
            self._logger.critical(f"[bold red]Error while loading Chrome: {repr(e)}[/bold red]")
            raise e

        # 设置页面加载超时
        self._browser.set_page_load_timeout(120)
        self._logger.info('[cyan]Page load timeout set to 120.[/]')

        # 无头模式下也可以调整窗口大小和位置
        # self._browser.set_window_position(0, 0)  # 设置窗口位置
        # self._logger.info('[cyan]Window position set to (0, 0).[/]')

        # self._browser.set_window_size(640, 660)  # 设置窗口大小
        # self._logger.info('[cyan]Window size set to (640, 660)[/]')

        # 设置已看过 (deprecated)
        # self.browser.execute_script(
        #     f"window.localStorage.setItem('oai/apps/hasSeenOnboarding/chat', {datetime.today().strftime('%Y-%m-%d')});"
        # )

        # 配置 Helper
        self._helper = SeleniumDriverHelper(self._browser)

        # 登录过程
        self._login(email, password, login_type=login_type)
        self._logger.info('[bold green]ChatGPT is ready to interact![/]')

    def _delete_except_profile(self, directory, profile):
        """
        删除除了用户 Profile 目录外的其他文件/目录，防止因为浏览器意外退出造成的 user_data_dir 损坏而无法启动。
        """
        # 遍历指定目录下的所有文件和目录
        for item in os.listdir(directory):
            item_path = os.path.join(directory, item)
            # 如果是目录并且不是 'Profile_1'，则删除该目录及其内容
            if os.path.isdir(item_path) and item != profile:
                shutil.rmtree(item_path)
            # 如果是文件或符号链接，则删除该文件或符号链接
            elif os.path.isfile(item_path) or os.path.islink(item_path):
                os.remove(item_path)

    def _load_capsolver_extension(self, options, capsolver_client_key=None):
        if capsolver_client_key is not None:
            # 获取插件及插件配置文件路径
            extension_directory = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'CapSolver.Browser.Extension-chrome')
            extension_config_path = os.path.join(extension_directory, 'assets', 'config.js')

            self._logger.info(f'Extension directory: {extension_directory}')
            self._logger.info(f'Extension config path: {extension_config_path}')

            # 替换插件的 api_key
            self._replace_api_key(extension_config_path, capsolver_client_key)

            # 加载 chrome 插件
            options.add_argument(f'--load-extension={extension_directory}')
        else:
            self._logger.warning(f"No 'capsolver_client_key' found! No extension will be loaded!")

    def _replace_api_key(self, config_path, new_api_key):

        # 在程序运行目录创建锁文件
        lock_path = os.path.abspath(".file_lock")
    
        # 创建一个文件锁
        lock = FileLock(lock_path, timeout=1)
    
        try:
            with lock:
                with open(config_path, 'r', encoding='utf-8') as file:
                    content = file.read()
    
                current_api_key_match = re.search(r"apiKey:\s*'(.+?)',", content)
                if current_api_key_match:
                    current_api_key = current_api_key_match.group(1)
                    if current_api_key != new_api_key:
                        new_content = re.sub(r"apiKey:\s*'.+?',", f"apiKey: '{new_api_key}',", content)
                        with open(config_path, 'w', encoding='utf-8') as file:
                            file.write(new_content)
    
                        self._logger.info("[bold green]API key has been successfully replaced.[/]")
                    else:
                        self._logger.info("[bold]The new API key is the same as the current one. No replacement made.[/]")
                else:
                    self._logger.error("[bold red]No existing API key found in the file.[/]")
    
        except Timeout:
            # 如果锁被其他进程占用，则记录警告信息
            self._logger.warning("[bold red]Lock acquisition failed. Another instance might be modifying the file.[/]")
            # 直接pass，不进行后续操作
            pass
        except FileNotFoundError:
            self._logger.error(f"[bold red]The file was not found: {config_path}[/]")
            raise
        except Exception as e:
            self._logger.error(f"[bold red]An error occurred: {e}[/]")
            raise

    @tenacity.retry(
        stop=tenacity.stop_after_attempt(5),
        wait=tenacity.wait_fixed(30),
        retry=tenacity.retry_if_exception_message(match='Oops')
    )
    def _login(self, email, password, login_type):

        # 进入 ChatGPT 页面
        self._logger.info("[bold]Entering [green]ChatGPT[/] website...[/]")
        self._browser.get(url='https://chatgpt.com')

        # 检查登录状态
        self._logger.info("Checking login status...")
        # 有两种登录按钮，一种是 Welcome 的弹出框内的，只有之前登录过又退出才会出现，优先查找点击；
        # 一种是右上的，不处在登录态就会出现（但只有在有 Welcome 的登录按钮时，才会出现data-testid属性）
        if not self._helper.find_then_click_or_fail(By.XPATH, self.xpath_chat__welcome_login_button, ignore_failure=True, label='WelcomeLogin') and \
           not self._helper.find_then_click_or_fail(By.XPATH, self.xpath_chat__login_button, ignore_failure=True, label='Login'):
            # 不需要登录
            self._logger.info("[bold green]Already logged in![/]")
            return

        # 需要登录
        self._logger.info("[bold]Login required. Initiating login process...[/]")

        # 等待登录页面加载完成
        self._helper.wait_until_appear(By.XPATH, self.xpath_login__welcome_label, label='WelcomeBackLabel')

        # 根据登录类型选择不同平台账号登录
        match login_type:
            case 'OpenAI':
                self._login_via_openai(email, password)
            case 'Microsoft':
                self._login_via_microsoft(email, password)
            case _:
                self._logger.error(f"[bold red]Invalid login type: {login_type}.[/]")
                raise ValueError(f"Invalid login type: {login_type}.")

        # 等待会话界面出现（或 cf 的验证）
        max_tries = 10
        for loop_count in range(max_tries):  # 最多循环 max_tries 次
            # 非首次尝试时，进行提醒
            if loop_count != 0:
                self._logger.warning(f"[bold yellow]Loop count {loop_count} times![/]")

            # 多重等待条件
            match self._helper.wait_for_mutually_exclusive_elements(
                by=By.XPATH,
                queries=[
                    self.xpath_microsoft_login__StaySignedIn_label,
                    self.xpath_failed_login__message_label,
                    self.xpath_cloudflare__verification_div,
                    self.xpath_chat__prompt_textarea
                ],
                labels=[
                    'StaySignedIn',
                    'OopsError',
                    'CloudFlareVerification',
                    'PromptTextarea'
                ]
            ):
                case ('StaySignedIn', _) if login_type == 'Microsoft':
                    # 情景一：提示保持登录状态 (仅在微软登录时出现)
                    self._logger.info("Current situation is 'StaySignedIn' stage.")
                    # 查找 "DontShowAgain" checkbox 并点击
                    self._helper.find_then_click_or_fail(By.XPATH, self.xpath_microsoft_login__DontShowAgain_checkbox, label="DontShowAgain")
                    # 查找并点击 "Yes" 按钮
                    self._helper.find_then_click_or_fail(By.XPATH, self.xpath_microsoft_login__yes_button, label="Yes")
                    # 重新判断当前页面（正常情况下应当会跳转到 PromptTextarea）
                    self._logger.info("[bold][blue]Microsoft[/] login process completed.[/]")
                    continue
                case ('OopsError', _):
                    # 情景二：发生了 Oops 错误
                    self._logger.error("Current situation is 'OopsError' stage.")
                    # 保存证据
                    self._logger.warning("Oops! Re-logging in...")
                    self._helper.save_debug_screenshot(f'{login_type}-OopsError')
                    # 抛出异常，被 tenacity 捕获重试
                    raise RuntimeError('Oops')
                case ('CloudFlareVerification', _):
                    # 情景三：需要 CloudFlare 验证
                    self._logger.warning("Current situation is 'CloudFlareVerification' stage.")
                    # 查找并点击 Verification 按钮
                    self._helper.find_then_click_or_fail(By.XPATH, self.xpath_cloudflare__verification_div, label="CloudFlareVerification")
                    # 重新判断当前页面（正常情况下应当会跳转到 PromptTextarea）
                    self._logger.info("[bold][yellow]CloudFlare Verification[/] process completed.[/]")
                    continue
                case ('PromptTextarea', _):
                    # 情景四：直接进入了对话界面
                    self._logger.info("Current situation is 'PromptTextarea' stage.")
                    self._logger.info("[bold]Skipping...[/]")
                    break
                case (None, None):
                    # 四种情景都不存在，抛出异常
                    self._logger.error("Could not find any specified label while trying to login!")
                    self._helper.save_debug_screenshot('NoLabelFound')
                    raise RuntimeError("Label not found!")
        else:
            # 最大尝试次数尝试完毕，仍然没有成功登录到会话界面
            self._logger.error(f"[bold red]Max retries meet! Could not find any specified label while trying to login![/]")
            self._helper.save_debug_screenshot('MaxLoginRetriesMeet')
            raise RuntimeError("Login failed. Max retries meet.")

        self._logger.info("[bold green]Successfully logged in![/]")

    def _login_via_openai(self, email, password):
        self._logger.info("[bold]Logging in via [green]OpenAI[/] account...[/]")

        # 先输入 email 点击 continue
        self._helper.wait_until_appear_then_input(By.XPATH, self.xpath_login__email_input, text=email, label='Email')
        self._helper.find_then_click_or_fail(By.XPATH, self.xpath_login__continue_button, label='Continue')

        # 再输入 password 点击 continue
        self._helper.wait_until_appear_then_input(By.XPATH, self.xpath_login__password_input, text=password, label='Password')
        self._helper.find_then_click_or_fail(By.XPATH, self.xpath_login__continue_button, label='Continue')

        self._logger.info('[bold][green]OpenAI[/] login process completed.[/]')

    def _login_via_microsoft(self, email, password):
        self._logger.info("[bold]Logging in via [blue]Microsoft[/] account...[/]")

        # 最先点击 'Continue with Microsoft Account' 按钮
        self._helper.find_then_click_or_fail(By.XPATH, self.xpath_login__microsoft_login_button, label='Continue with Microsoft Account')

        # 先输入 email，点击 Next
        self._helper.wait_until_appear_then_input(By.XPATH, self.xpath_microsoft_login__email_input, text=email, label='Email')
        self._helper.find_then_click_or_fail(By.XPATH, self.xpath_microsoft_login__next_button, label='Next')

        # 再输入 password，点击 Sign in
        self._helper.wait_until_appear_then_input(By.XPATH, self.xpath_microsoft_login__password_input, text=password, label='Password')
        self._helper.find_then_click_or_fail(By.XPATH, self.xpath_microsoft_login__signin_button, label='Sign in')

        # 还剩下一个检查是否有 Stay Signed In 的提示，放在上面

        self._logger.info('[bold][blue]Microsoft[/] login process is about to complete.[/]')

    def switch_model(self, target_model: str):
        """
        Switch the model for ChatGPT+ users.

        Args:
            target_model: str = The name of the model, either GPT-3.5 or GPT-4

        Returns:
            None
        """
        # 点击模型选择
        self._logger.info('[bold]Obtaining available models...[/]')
        self._helper.wait_until_appear_then_click(By.XPATH, self.xpath_chat__model_menu_div, label='Model Menu')
        self._helper.wait_until_appear(By.XPATH, self.xpath_chat__model_menuitem_divs, label='Model Menu Item')
        # 获取所有模型的 div
        models = self._browser.find_elements(By.XPATH, self.xpath_chat__model_menuitem_divs)
        # 提取所有模型名称（直接用.text的话会获取子div中的文本）
        MODEL_NAMES = [self._browser.execute_script("return arguments[0].childNodes[0].nodeValue;", x) for x in models]
        assert target_model in MODEL_NAMES, f"Invalid model name: {target_model}, should be one of the following: {MODEL_NAMES}"

        self._logger.info(f"Available models: {MODEL_NAMES}")
        self._logger.info(f"[bold]Switching model to '{target_model}'...[/]")

        # 点击模型，进行切换
        self._helper.find_then_click_or_fail(By.XPATH, self.xpath_chat__model_menuitem_div.format(target_model), label=target_model)

        self._logger.info(f"[bold]Model changed to '{target_model}'.[/]")

    def switch_temporary_mode(self, temporary: bool):
        # 先获取当前的状态
        self._logger.info(f"Checking if 'Temporary Mode' is on or not...")
        self._helper.wait_until_appear_then_click(By.XPATH, self.xpath_chat__model_menu_div, label='Model Menu')
        element = self._helper.wait_until_appear(By.XPATH, self.xpath_chat__model_temporary_div, label='Temporary Mode')
        value_map = {True: True, False: False, 'true': True, 'false': False, '': None, None: None}
        is_temporary = value_map[element.get_attribute('aria-checked')]
        self._logger.info(f"[dim]element.get_attribute('aria-checked'): {is_temporary}[/]")

        # 是否有该属性值
        if is_temporary is None:
            self._logger.error(f"[bold red]Please check the attributes of 'self.xpath_chat__model_temporary_div', the original 'aria-checked' is no longer valid.[/]")
            self._helper.save_debug_screenshot('TemporaryMode')
            raise RuntimeError(f"The attributes of 'self.xpath_chat__model_temporary_div' not found!")

        # 输出当前状态
        value_map = {True: '[bold green]ON[/]', False: '[bold red]OFF[/]'}
        self._logger.info(f"[bold]Current value: {value_map[is_temporary]}")

        # 判断是否需要切换
        target_mode = value_map[temporary]
        if is_temporary == temporary:
            # 再次点击模型菜单，收回菜单
            self._helper.wait_until_appear_then_click(By.XPATH, self.xpath_chat__model_menu_div, label='Model Menu')
            self._logger.info(f"[cyan]The 'Temporary Mode' already set to {target_mode}. Skipping...[/]")
            return
        else:
            self._logger.info(f"Attempting to trigger 'Temporary Mode' to {target_mode}...")
            element.click()
            self._logger.info(f"[bold]The 'Temporary Mode' set to {target_mode} successfully![/]")

    def new_chat(self):
        """
        Function to close the current thread and start a new one
        """
        self._logger.info(f"[bold]Attempting to start a 'New Chat'...[/bold]")
        self._helper.find_then_click_or_fail(By.XPATH, self.xpath_chat__new_chat_div, label='NewChat')
        self._helper.wait_until_appear(By.XPATH, self.xpath_chat__prompt_textarea, label='PromptTextarea')
        self._logger.info(f"[bold]The 'New Chat' already started![/]")

    def regenerate(self):
        """
        Regenerate a new response in current thread.
        """
        self._logger.info(f"[bold]Attempting to regenerate the answer...[/]")

        # 点击最后一条 assistant 消息底部的重新生成按钮
        self._helper.find_then_click_or_fail(By.XPATH, self.xpath_chat__conversation_last_assistant_turn_regenerate_button, label='LastTurnRegenerateButton')

        # !!! 也存在没出现中止生成按钮，直接出现了红框错误消息的情况（需要同步等待） !!!
        # 等待中止生成按钮出现（代表开始生成）
        # self._helper.wait_until_appear(By.XPATH, self.xpath_chat__stop_button, label='StopButton')
        label, element = self._helper.wait_for_mutually_exclusive_elements(
            by=By.XPATH,
            queries=[self.xpath_chat__stop_button, self.xpath_chat__conversation_error_message_p],
            labels=['StopButton', 'ConversationErrorMessage']
        )
        if label == 'ConversationErrorMessage':
            # 出问题咧，红色边框消息
            self._logger.error(element.get_attribute('outerHTML'))
            self._helper.save_debug_screenshot('ConversationErrorMessage-1')
            raise RuntimeError(f"Error occurred while generating response!")

        # 等待中止生成按钮消失（代表生成结束）
        self._helper.wait_until_disappear(By.XPATH, self.xpath_chat__stop_button, timeout_duration=180, label='StopButton')

        # 点击到达底部按钮
        self._helper.find_then_click_or_fail(By.XPATH, self.xpath_chat__scroll_to_bottom_button, ignore_failure=True, label='ScrollToBottomButton')

        # 等待气泡中的内容稳定
        self._helper.check_element_stability(By.XPATH, self.xpath_chat__conversation_last_assistant_turn_outer_div, check_period=1, confirmation_time=5, label='LastMessage')

        # 查看是否有错误消息
        if error_message_p := self._helper.find_element_or_fail(By.XPATH, self.xpath_chat__conversation_error_message_p, ignore_failure=True, label='ConversationErrorMessage'):
            # 有了红色边框的错误消息
            self._logger.error(error_message_p.get_attribute('outerHTML'))
            self._helper.save_debug_screenshot('ConversationErrorMessage-2')
            raise RuntimeError(f"Error occurred while generating response!")

        # 如果没有错误消息，那么查看是否有重新生成按钮（的确存在无报错但生成失败的情况）
        if regenerate_button := self._helper.find_element_or_fail(By.XPATH, self.xpath_chat__error_regenerate_button, ignore_failure=True, label='RegenerateButton'):
            # 没有红框，但还是生成错误
            self._logger.error(f"[bold red]'RegenerateButton' found. Something is wrong![/]")
            self._helper.save_debug_screenshot('RegenerateButton')
            raise RuntimeError(f"Error occurred while generating response!")

        # 生成没问题，等待答案出现（也的确存在已经出现了 assistant 的聊天气泡但其内容为空的情况，此时 answer 由于等待的是内部的 markdown 部分，还没有出现，所以不存在）
        answer_div = self._helper.wait_until_appear(By.XPATH, self.xpath_chat__conversation_last_assistant_turn_inner_div, label='Answer')

        # 等待不如早点重开
        # self._helper.find_element_or_fail(By.XPATH, self.xpath_chat__conversation_last_assistant_turn_inner_div, label='Answer')

        # 点击复制按钮（不直接使用`answer_div.text`获取是因为，这样获取到的会将 bullet points 的序号丢掉）
        # answer = answer_div.text
        answer = self._copy_answer_to_clipboard()

        self._logger.info(f"[bold green]Answer is ready![/]")
        self._logger.info(f"[cyan]{'-' * (self._console_width - 27)}[/]")
        self._logger.info(f"[cyan]{answer}[/]")
        self._logger.info(f"[cyan]{'-' * (self._console_width - 27)}[/]")

        return answer

    def chat(self, question: str) -> str:
        """
        Sends a question and retrieves the answer from the ChatGPT system.

        This function interacts with the ChatGPT.
        It takes the question as input and sends it to the system.
        The question may contain multiple lines separated by '\n'.
        In this case, the function simulates pressing SHIFT+ENTER for each line.

        After sending the question, the function waits for the answer.
        Once the response is ready, the response is returned.

        Args:
            question (str): The interaction text.

        Returns:
            str: The generated answer.
        """
        self._logger.info(f"[bold]Attempting to ask the question:[/]")
        self._logger.info(f"[yellow]{'-' * (self._console_width - 27)}[/]")
        self._logger.info(f"[yellow]{question}[/]")
        self._logger.info(f"[yellow]{'-' * (self._console_width - 27)}[/]")

        # 先确保页面加载完毕，确实存在 PromptTextarea
        self._helper.wait_until_appear(By.XPATH, self.xpath_chat__prompt_textarea, label='PromptTextarea')

        # 获取当前 assistant message 的 turn 数，与后面作比较，确保的确生成了新答案
        if last_turn_div := self._helper.find_element_or_fail(By.XPATH, self.xpath_chat__conversation_last_assistant_turn_outer_div, ignore_failure=True, label='TurnsOfAssistantMessage'):
            # 之前有过对话，turn 存在
            data_testid = last_turn_div.get_attribute('data-testid')
            assert isinstance(data_testid, str) and data_testid.startswith('conversation-turn-'), f'Invalid data testid: {data_testid}, should start with "conversation-turn-"!'
            last_turn = int(data_testid.split('-')[-1])
            self._logger.info(f"Last conversation turns: {last_turn}")
        else:
            last_turn = 1  # system prompt
            self._logger.info(f"Last conversation turn not found! Assuming 'last_turn' = {last_turn} ...")

        # 应当出现的 turn
        expected_turn = last_turn + 2

        # 向文本框输入内容
        self._helper.find_then_input_or_fail(
            by=By.XPATH,
            query=self.xpath_chat__prompt_textarea,
            text=question,
            input_method='copy_paste',
            label='PromptTextarea',
        )

        # 确定发送按钮在可点击状态，然后再点击
        self._helper.wait_until_disappear(By.XPATH, self.xpath_chat__send_button_disabled, label='SendButtonDisabled')
        self._helper.wait_until_appear_then_click(By.XPATH, self.xpath_chat__send_button_enabled, label='SendButtonEnabled')

        # 直接等待 specified turn 出现（代表开始生成，无论是报错还是正常消息），或是 Regenerate 按钮，这三种情况
        max_tries = 10
        for loop_count in range(max_tries):  # 最多循环 max_tries 次
            # 非首次尝试时，进行提醒
            if loop_count != 0:
                self._logger.warning(f"[bold yellow]Loop count {loop_count} times![/]")

            match self._helper.wait_for_mutually_exclusive_elements(
                by=By.XPATH,
                queries=[
                    self.xpath_chat__conversation_specified_assistant_turn_inner_div.format(turn=expected_turn),
                    self.xpath_chat__conversation_specified_error_message_p.format(turn=expected_turn),
                    self.xpath_chat__error_regenerate_button
                ],
                labels=[
                    'NormalMessage',
                    'ErrorMessage',
                    'RegenerateButton'
                ]
            ):
                case ('NormalMessage', _):
                    # 情景一：开始正常生成消息
                    self._logger.info("Current situation is 'NormalMessage' stage.")
                    # 点击到达底部按钮
                    self._helper.find_then_click_or_fail(By.XPATH, self.xpath_chat__scroll_to_bottom_button, ignore_failure=True, label='ScrollToBottomButton')
                    break
                case ('ErrorMessage', error_message_p):
                    # 情景二：出现了红框错误消息
                    self._logger.info("Current situation is 'ErrorMessage' stage.")
                    self._logger.error(error_message_p.get_attribute('outerHTML'))
                    self._helper.save_debug_screenshot('ConversationErrorMessage-2')
                    raise RuntimeError(f"Error occurred while generating response!")

                case ('RegenerateButton', _):
                    # 情景三：未出现上面两个消息，没有聊天气泡出现，直接出现了 重新生成 按钮
                    self._logger.info("Current situation is 'RegenerateButton' stage.")
                    self._logger.warning("'RegenerateButton' found. Something is wrong!")
                    self._helper.save_debug_screenshot('RegenerateButton')
                    # raise RuntimeError(f"Error occurred while generating response!")
                    self._logger.warning('[bold yellow]Regenerating...[/]')
                    continue
        else:
            # 最大尝试次数尝试完毕，仍然没有成功生成消息
            self._logger.error(f"[bold red]Max retries meet! Could not generate normal response![/]")
            self._helper.save_debug_screenshot('MaxRegenerateRetriesMeet')
            raise RuntimeError("Regenerate failed. Max retries meet.")

        # 等待中止生成按钮消失（代表生成结束）
        self._helper.wait_until_disappear(By.XPATH, self.xpath_chat__stop_button, timeout_duration=180, label='StopButton')

        # 查看是否有错误消息
        if error_message_p := self._helper.find_element_or_fail(By.XPATH, self.xpath_chat__conversation_error_message_p, ignore_failure=True, label='ConversationErrorMessage'):
            # 有了红色边框的错误消息
            self._logger.error(error_message_p.get_attribute('outerHTML'))
            self._helper.save_debug_screenshot('ConversationErrorMessage-2')
            raise RuntimeError(f"Error occurred while generating response!")

        # 如果没有错误消息，那么查看是否有重新生成按钮（的确存在无报错但生成失败的情况）
        if regenerate_button := self._helper.find_element_or_fail(By.XPATH, self.xpath_chat__error_regenerate_button, ignore_failure=True, label='RegenerateButton'):
            # 没有红框，但还是生成错误
            self._logger.error(f"[bold red]'RegenerateButton' found. Something is wrong![/]")
            self._helper.save_debug_screenshot('RegenerateButton')
            raise RuntimeError(f"Error occurred while generating response!")

        # 生成没问题，等待答案出现
        answer_div = self._helper.wait_until_appear(By.XPATH, self.xpath_chat__conversation_specified_assistant_turn_inner_div.format(turn=expected_turn), label='Answer')

        # 点击到达底部按钮
        self._helper.find_then_click_or_fail(By.XPATH, self.xpath_chat__scroll_to_bottom_button, ignore_failure=True, label='ScrollToBottomButton')

        # 点击复制按钮（不直接使用`answer_div.text`获取是因为，这样获取到的会将 bullet points 的序号丢掉）
        # answer = answer_div.text
        answer = self._copy_answer_to_clipboard()

        self._logger.info(f"[bold green]Answer is ready![/]")
        self._logger.info(f"[blue]{'-' * (self._console_width - 27)}[/]")
        self._logger.info(f"[blue]{answer}[/]")
        self._logger.info(f"[blue]{'-' * (self._console_width - 27)}[/]")

        return answer

    def _copy_answer_to_clipboard(self):
        pyperclip.copy('')  # 清空剪贴板
        self._helper.find_then_click_or_fail(By.XPATH, self.xpath_chat__conversation_last_assistant_turn_copy_button, label='CopyButton')
        while (answer := pyperclip.paste()) == '':
            self._logger.info("Waiting for answer to be copied to clipboard...")
            time.sleep(1)

        return answer

    def quit(self) -> bool:
        self._logger.info("[bold]Quitting SeleniumChatGPT...[/]")
        try:
            self._browser.quit()
        except Exception as e:
            self._logger.error(f"[bold red]Failed to quit SeleniumChatGPT: {repr(e)}![/]")
            return False
        self._logger.info("[bold green]Successfully quit SeleniumChatGPT![/]")
        return True


if __name__ == '__main__':

    gpt = SeleniumChatGPT(
        email='',
        password='',
        login_type='OpenAI',
        capsolver_client_key=None,
        headless=False,
        user_data_dir='./user_data'
    )

    print('Question: Hello!')
    time.sleep(3)
    gpt.switch_temporary_mode(True)
    gpt.chat('Hello!')

    print('Question: What can you do for me?')
    time.sleep(3)
    gpt.switch_temporary_mode(True)
    gpt.chat('What can you do for me?')

    print('Regenerate')
    time.sleep(3)
    gpt.regenerate()

    print('New Chat')
    time.sleep(3)
    gpt.new_chat()
    gpt.switch_temporary_mode(True)
    gpt.chat('Hello again! Please answer me with many many emojis!')

    while True:
        time.sleep(10)
