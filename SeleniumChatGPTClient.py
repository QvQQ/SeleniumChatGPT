#!/usr/bin/env python3
# -*- coding=utf-8 -*-
import json

import requests
from box import Box
from rich import print as rprint
from typing import Literal


class SeleniumChatGPTClient:
    """
    A client to interact with SeleniumChatGPT server API.
    """

    def __init__(self, base_url: str = 'http://localhost:15001', timeout: int = 300):
        """
        Initialize the client with the base URL of the server.

        :param base_url: The base URL of the server, e.g. "http://localhost:15001".
        :param timeout: Timeout for requests (in seconds).
        """
        self._base_url = base_url
        self._timeout = timeout

    def _handle_response(self, response: requests.Response) -> Box:
        """
        Handle server response. If the response indicates an error, raise an exception.

        :param response: Server's response.
        :return: JSON data from the response.
        """
        try:
            data = response.json()
        except json.decoder.JSONDecodeError:
            rprint(f"response.text = {response.text}")
            raise

        if response.status_code >= 400:
            rprint(data)
            raise RuntimeError(f"Error {data['code']}: {data['message']}")

        rprint(f"[green]Message: {data['message']}[/]")
        return Box(data)

    def shutdown(self):
        """
        Close the server.
        """
        try:
            response = requests.post(f"{self._base_url}/shutdown", timeout=self._timeout)
            self._handle_response(response)
        except requests.RequestException as e:
            rprint(f"[red]Request Error: {e}[/]")
            raise

    def start_client(
        self,
        email, password,
        login_type: Literal['OpenAI', 'Microsoft'],
        capsolver_client_key=None,
        headless=False,
        user_data_dir=None
    ):

        data = {
            "email": email,
            "password": password,
            "login_type": login_type,
            "capsolver_client_key": capsolver_client_key,
            "headless": headless,
            "user_data_dir": user_data_dir
        }
        try:
            response = requests.post(f"{self._base_url}/start_client", json=data, timeout=self._timeout)
            self._handle_response(response)
        except requests.RequestException as e:
            rprint(f"[red]Request Error: {e}[/]")
            raise

    def chat(self, question: str) -> str:
        """
        Chat with SeleniumChatGPT client on the server.

        :param question: Text to send to the client.
        :return: Answer from the response.
        """
        try:
            response = requests.post(f"{self._base_url}/chat", json={"question": question}, timeout=self._timeout)
            data = self._handle_response(response)
            return data.data.answer
        except requests.RequestException as e:
            rprint(f"[red]Request Error: {e}[/]")
            raise

    def switch_model(self, target_model: str):
        try:
            response = requests.post(f"{self._base_url}/switch_model", json={"target_model": target_model}, timeout=self._timeout)
            self._handle_response(response)
        except requests.RequestException as e:
            rprint(f"[red]Request Error: {e}[/]")
            raise

    def switch_temporary_mode(self, temporary: bool):
        try:
            response = requests.post(f"{self._base_url}/switch_temporary_mode", json={"temporary": temporary}, timeout=self._timeout)
            self._handle_response(response)
        except requests.RequestException as e:
            rprint(f"[red]Request Error: {e}[/]")
            raise

    def new_chat(self):
        try:
            response = requests.post(f"{self._base_url}/new_chat", timeout=self._timeout)
            self._handle_response(response)
        except requests.RequestException as e:
            rprint(f"[red]Request Error: {e}[/]")
            raise

    def regenerate(self):
        try:
            response = requests.post(f"{self._base_url}/regenerate", timeout=self._timeout)
            self._handle_response(response)
        except requests.RequestException as e:
            rprint(f"[red]Request Error: {e}[/]")
            raise


if __name__ == '__main__':

    client = SeleniumChatGPTClient(base_url='http://localhost:15001', timeout=300)

    client.start_client(
        email='mjxhkpnchpr@outlook.com',
        password='sRXc9T7YV5Q',  # noqa
        login_type='OpenAI',
        capsolver_client_key=None,
        headless=False,
        user_data_dir='./user_data'
    )

    print('\nSwitch to temporary mode.')
    client.switch_temporary_mode(True)

    print('\nQuestion: Hello!')
    client.chat('Hello!')

    # print('\nShutdown the server.')
    # client.shutdown()

    print('\nQuestion: Hello again!')
    client.chat('Hello again!')

    print('\nQuestion: What can you do for me?')
    client.chat('What can you do for me?')

    print('\nRegenerate')
    client.regenerate()

    print('\nNew Chat')
    client.new_chat()

    print('\nSwitch to temporary mode.')
    client.switch_temporary_mode(True)

    print('\nQuestion: Hello again! Please answer me with many many emojis!')
    client.chat('Hello again! Please answer me with many many emojis!')

