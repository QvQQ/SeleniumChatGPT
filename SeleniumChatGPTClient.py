#!/usr/bin/env python3
# -*- coding=utf-8 -*-
import requests
from box import Box
from typing import Literal, Optional
from rich.console import Console


class SeleniumChatGPTClient:
    """
    A client to interact with SeleniumChatGPT server API.
    """

    def __init__(
        self,
        email: str, password: str,
        login_type: Literal['OpenAI', 'Microsoft'],
        capsolver_client_key: Optional[str] = None,
        headless: bool = False,
        user_data_dir: Optional[str] = None,
        base_url: str = 'http://localhost:15001',
        timeout: int = 300,
        console: Console = None
    ):
        """
        Initialize the client with the base URL of the server.

        :param base_url: The base URL of the server, e.g. "http://localhost:15001".
        :param timeout: Timeout for requests (in seconds).
        :param console: The console instance used to log.
        """
        self._email, self._password = email, password
        self._login_type = login_type
        self._capsolver_client_key = capsolver_client_key
        self._headless = headless
        self._user_data_dir = user_data_dir

        self._base_url = base_url
        self._timeout = timeout
        self._console = console or Console()

    def _handle_response(self, response: requests.Response) -> Box:
        """
        Handle server response. If the response indicates an error, raise an exception.

        :param response: Server's response.
        :return: JSON data from the response.
        """
        try:
            response.raise_for_status()
            data = response.json()

        except requests.exceptions.HTTPError as http_err:
            if response.status_code in [400, 404]:
                data = http_err.response.json()
                self._console.log(f"Error {data['code']}: {data['message']}")
            else:
                self._console.log(f"[bold yellow]!!! Error occurred !!![/] [bold red]{repr(http_err)}[/]")
            raise

        except requests.exceptions.JSONDecodeError:
            self._console.log(f"response.text = {response.text}")
            raise

        self._console.log(f"[green]Message: {data['message']}[/]")
        return Box(data)

    def shutdown(self):
        """
        Close the server.
        """
        try:
            response = requests.post(f"{self._base_url}/shutdown", timeout=self._timeout)
        except requests.RequestException as e:
            self._console.log(f"[red]Request Error: {repr(e)}[/]")
            raise
        else:
            self._handle_response(response)

    def start_client(self):
        data = {
            "email": self._email,
            "password": self._password,
            "login_type": self._login_type,
            "capsolver_client_key": self._capsolver_client_key,
            "headless": self._headless,
            "user_data_dir": self._user_data_dir
        }
        try:
            self._console.log(f"[bold white]Starting SeleniumChatGPT Client...[/]")
            response = requests.post(f"{self._base_url}/start_client", json=data, timeout=self._timeout)
        except requests.RequestException as e:
            self._console.log(f"[red]Request Error: {repr(e)}[/]")
            raise
        else:
            self._handle_response(response)

    def chat(self, question: str) -> str:
        """
        Chat with SeleniumChatGPT client on the server.

        :param question: Text to send to the client.
        :return: Answer from the response.
        """
        try:
            response = requests.post(f"{self._base_url}/chat", json={"question": question}, timeout=self._timeout)
        except requests.RequestException as e:
            self._console.log(f"[red]Request Error: {repr(e)}[/]")
            raise
        else:
            data = self._handle_response(response)
            return data.data.answer

    def reset_to_specified_mode(self, model: Literal['GPT-4o', 'GPT-4o mini', 'GPT-4'], temporary_mode: bool = True):
        try:
            response = requests.post(f"{self._base_url}/reset_to_specified_mode", json={"model": model, "temporary_mode": temporary_mode}, timeout=self._timeout)
        except requests.RequestException as e:
            self._console.log(f"[red]Request Error: {repr(e)}[/]")
            raise
        else:
            self._handle_response(response)

    def switch_model(self, target_model: Literal['GPT-4o', 'GPT-4o mini', 'GPT-4']):
        try:
            response = requests.post(f"{self._base_url}/switch_model", json={"target_model": target_model}, timeout=self._timeout)
        except requests.RequestException as e:
            self._console.log(f"[red]Request Error: {repr(e)}[/]")
            raise
        else:
            self._handle_response(response)

    def switch_temporary_mode(self, temporary: bool):
        try:
            response = requests.post(f"{self._base_url}/switch_temporary_mode", json={"temporary": temporary}, timeout=self._timeout)
        except requests.RequestException as e:
            self._console.log(f"[red]Request Error: {repr(e)}[/]")
            raise
        else:
            self._handle_response(response)

    def new_chat(self):
        try:
            response = requests.post(f"{self._base_url}/new_chat", timeout=self._timeout)
        except requests.RequestException as e:
            self._console.log(f"[red]Request Error: {repr(e)}[/]")
            raise
        else:
            self._handle_response(response)

    def regenerate(self) -> str:
        try:
            response = requests.post(f"{self._base_url}/regenerate", timeout=self._timeout)
        except requests.RequestException as e:
            self._console.log(f"[red]Request Error: {repr(e)}[/]")
            raise
        else:
            data = self._handle_response(response)
            return data.data.answer


if __name__ == '__main__':

    # read configuration
    config = Box.from_yaml(filename='./client_config.yaml')

    console = Console()
    client = SeleniumChatGPTClient(
        email=config.email,
        password=config.password,
        login_type=config.login_type,
        capsolver_client_key=config.capsolver_client_key,
        headless=config.headless,
        user_data_dir=config.user_data_dir,
        base_url=config.base_url,
        timeout=300,
        console=console
    )

    client.start_client()
    client.new_chat()
    client.switch_model('GPT-4o')
    client.switch_temporary_mode(True)
    # client.reset_to_specified_mode(model='GPT-4o', temporary_mode=True)

    # for REPL
    from rich.console import Console
    from rich.panel import Panel
    from rich.markdown import Markdown

    from prompt_toolkit import PromptSession
    from prompt_toolkit.history import InMemoryHistory
    from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
    from prompt_toolkit.completion import WordCompleter
    from prompt_toolkit.styles import Style
    from prompt_toolkit.shortcuts import CompleteStyle
    from prompt_toolkit.formatted_text import HTML

    # 定义命令的自动补全选项
    command_completer = WordCompleter([
        '/help', '/shutdown', '/new_chat', '/regenerate', '/switch_model', '/switch_temporary_mode', '/reset_to_specified_mode',
    ], ignore_case=True, match_middle=True, sentence=True)

    # 创建一个带有内存历史记录的会话
    session = PromptSession(history=InMemoryHistory())

    # 定义样式
    style = Style.from_dict({
        'prompt': '#FFFFFF bold',
    })

    console.print(
        Panel.fit(
            "🤖 [bold blue]Welcome to the SeleniumChatGPT REPL![/bold blue] 🎉🎈✨",
            border_style="bold blue"
        )
    )

    try:
        while True:
            command: str = session.prompt(
                HTML("<prompt>Message ChatGPT</prompt> 💬🌟: "),
                completer=command_completer,
                complete_style=CompleteStyle.COLUMN,
                auto_suggest=AutoSuggestFromHistory(),
                style=style
            )

            if command.startswith('/'):
                if command == "/shutdown":
                    client.shutdown()
                    console.print(
                        Panel.fit(
                            "[bold red]🔌 Server shutdown. Goodbye! 🥺👋💔[/]",
                            border_style="bold red"
                        )
                    )
                    console.print()
                    break

                elif command == "/new_chat":
                    client.new_chat()
                    console.print(
                        Panel.fit(
                            "[bold yellow]🆕 Started a new chat session. Let's begin! 🚀💬[/]",
                            border_style="bold yellow"
                        )
                    )

                elif command == "/regenerate":
                    answer = client.regenerate()
                    console.print(
                        Panel.fit(
                            "[bold cyan]🔄 Regenerated the last response. Here we go again! 🎉🔁[/]",
                            border_style="bold cyan"
                        )
                    )
                    console.print(
                        Panel.fit(
                            Markdown(answer),
                            title="[bold green]New Answer[/] 🤖✨",
                            title_align='left',
                            border_style="bold green"
                        )
                    )

                elif command == "/help":
                    console.print(
                        Panel.fit(
                            "[bold blue]/help[/] - Show this help message\n"
                            "[bold blue]/shutdown[/] - Shutdown the server\n"
                            "[bold blue]/new_chat[/] - Start a new chat session\n"
                            "[bold blue]/regenerate[/] - Regenerate the last response\n"
                            "[bold blue]/switch_model <model>[/] - Switch the model\n"
                            "[bold blue]/switch_temporary_mode <true/false>[/] - Switch temporary mode\n"
                            "[bold blue]/reset_to_specified_mode <model> <true/false>[/] - Reset to specified mode",
                            title="Commands",
                            padding=(1, 4)
                        )
                    )

                elif command.startswith("/switch_model "):
                    model = command.split(' ', 1)[-1]
                    if model not in ['GPT-4o', 'GPT-4o mini', 'GPT-4']:
                        console.print(
                            Panel.fit(
                                f"[bold red]❗ Model [bold white]{model}[/] is not supported! 😮💨[/]",
                                border_style="bold red"
                            )
                        )
                        continue
                    client.switch_model(model)  # noqa
                    console.print(
                        Panel.fit(
                            f"[bold green]🔄 Switched to model: [bold white]{model}[/]. Model changed! 🦾🤖[/]",
                            border_style="bold green"
                        )
                    )

                elif command.startswith("/switch_temporary_mode "):
                    temporary_mode = command.split(' ')[1].lower() == 'true'
                    client.switch_temporary_mode(temporary_mode)
                    console.print(
                        Panel.fit(
                            f"[bold green]🔄 Switched temporary mode to: {'[green]ON[/]' if temporary_mode else '[red]OFF[/]'}. Mode toggled! 🔀🕹 [/]",
                            border_style="bold green"
                        )
                    )

                elif command.startswith("/reset_to_specified_mode "):
                    params = command.split(' ', 1)[1].rsplit(' ', 1)
                    if len(params) == 2:
                        model, temporary_mode = params
                    else:
                        console.print(
                            Panel.fit(
                                f"[bold red]❗ Parameter [bold white]{params}[/] is not valid! 😮💨[/]",
                                border_style="bold red"
                            )
                        )
                        continue
                    if model not in ['GPT-4o', 'GPT-4o mini', 'GPT-4']:
                        console.print(
                            Panel.fit(
                                f"[bold red]❗ Model [bold white]{model}[/] is not supported! 😮💨[/]",
                                border_style="bold red"
                            )
                        )
                        continue
                    temporary_mode = (temporary_mode.lower() == 'true')
                    client.reset_to_specified_mode(model=model, temporary_mode=temporary_mode)
                    console.print(
                        Panel.fit(
                            f"[bold green]Reset to [bold white]{model}[/] model with temporary mode {'[green]ON[/]' if temporary_mode else '[red]OFF[/]'}. Mode toggled! 🔀🕹 [/]",
                            border_style="bold green"
                        )
                    )
                else:
                    console.print(
                        Panel.fit(
                            "[bold red]❓ Unknown command. Type '/help' for options. 🤷❓[/]",
                            border_style="bold red"
                        )
                    )
            else:
                if command != '':
                    # Treat any non-command input as a chat message
                    answer = client.chat(command)
                    console.print(
                        Panel.fit(
                            Markdown(command, style='yellow'),
                            title="[bold yellow]Question[/] 💬",
                            title_align='left',
                            border_style="bold yellow"
                        )
                    )
                    console.print(
                        Panel.fit(
                            Markdown(answer),
                            title="[bold green]Answer[/] 🤖✨",
                            title_align='left',
                            border_style="bold green"
                        )
                    )

    except (EOFError, KeyboardInterrupt):
        console.print()
        console.print(
            Panel.fit(
                "[bold red]🛑 KeyboardInterrupt detected. Exiting the program... 😢👋💔[/]",
                border_style="bold red"
            )
        )
