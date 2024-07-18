#!/usr/bin/env python
# -*- coding: utf-8 -*-

# for log
import logging

# for utils
import time
from typing import Tuple, Optional, Literal, List

# for selenium
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC  # noqa
import selenium.common.exceptions as Exceptions  # noqa


class SeleniumDriverHelper:
    """
    Tool class to afford convenience.
    """

    def __init__(self, driver: WebDriver):

        # 配置浏览器 driver
        self.browser = driver

        # 配置日志
        self.logger = logging.getLogger(self.__class__.__name__)

    def find_element_or_fail(
        self,
        by: str, query: str,
        ignore_failure: bool = False,
        label: str = ''
    ) -> Optional[WebElement]:
        """
        Finds a list of elements given query, if none of the items exists, throws an error

        Args:
            by (str): The method used to locate the element.
            query (str): The query string to locate the element.
            ignore_failure (bool): If False, an exception is raised if an element is not present.
            label (str): Description used for the element.

        Returns:
            WebElement: Web element or None if not found.
        """
        label = label or query
        self.logger.info(f"[dim cyan]Attempting to locate element '{label}'...[/]")
        try:
            element = self.browser.find_element(by, query)
            self.logger.info(f"[dim]'{label}' is located.[/]")
            return element

        except Exceptions.NoSuchElementException:
            if ignore_failure:
                self.logger.warning(f"[dim]Element '{label}' is not found.[/]")
                return None
            self.logger.error(f"[bold red]Element '{label}' is not found.[/]")
            raise

    def wait_until_appear(
        self,
        by: str, query: str,
        timeout_duration: int = 60, ignore_timeout: bool = False,
        label: str = ''
    ) -> Optional[WebElement]:
        """
        Waits until the specified web element appears on the page.

        This function continuously checks for the presence of a web element.
        It waits until the element is present on the page.
        Once the element appears, the function returns.

        Args:
            by (str): The method used to locate the element.
            query (str): The query string to locate the element.
            timeout_duration (int, optional): The total wait time before the timeout exception. Default: 60.
            ignore_timeout (bool): If True, no exception is raised if the element still not appeared after the timeout.
            label (str): Description used for the element.

        Returns:
            Optional[WebElement]: The web element if found, else None.
        """
        label = label or query
        self.logger.info(f"[dim cyan]Waiting for element '{label}' to appear.[/]")
        try:
            element = WebDriverWait(
                self.browser,
                timeout_duration
            ).until(
                EC.visibility_of_element_located((by, query))
            )
            self.logger.info(f"[dim]Element '{label}' appeared.[/]")
            return element
        except Exceptions.TimeoutException:
            if ignore_timeout:
                self.logger.warning("[bold yellow]Timeout reached but ignoring since ignore_timeout is True.[/]")
                return None
            self.logger.error(f"[bold red]Element '{label}' did not appear within {timeout_duration}s, something is wrong![/]")
            raise  # Re-raise the exception if ignore_timeout is False

    def wait_until_disappear(
        self,
        by: str, query: str,
        timeout_duration: int = 60, ignore_timeout: bool = False,
        label: str = ''
    ) -> Optional[bool]:
        """
        Waits until the specified web element disappears from the page.

        This function continuously checks for the presence of a web element.
        It waits until the element is no longer present on the page.
        Once the element has disappeared, the function returns.

        Args:
            by (str): The method used to locate the element.
            query (str): The query string to locate the element.
            timeout_duration (int, optional): The total wait time before the timeout exception. Default: 60.
            ignore_timeout (bool): If True, no exception is raised if the element remains visible after the timeout.
            label (str): Description used for the element.

        Returns:
            Optional[bool]: True if the element disappeared, False otherwise.
        """
        label = label or query
        self.logger.info(f"[dim cyan]Waiting for element '{label}' to disappear.[/]")
        try:
            WebDriverWait(
                self.browser,
                timeout_duration
            ).until_not(
                EC.visibility_of_element_located((by, query))
            )
            self.logger.info(f"[dim]Element '{label}' disappeared.[/]")
            return True
        except Exceptions.TimeoutException:
            if ignore_timeout:
                self.logger.warning("[bold yellow]Timeout reached but ignoring since ignore_timeout is True.[/]")
                return False
            self.logger.error(f"[bold red]Element '{query}' still here within {timeout_duration}s, something is wrong![/]")
            raise  # Re-raise the exception if ignore_timeout is False

    def wait_for_mutually_exclusive_elements(
        self,
        by: str, queries: List[str],
        timeout_duration: int = 60, ignore_timeout: bool = False,
        labels: List[str] = None
    ) -> Tuple[str, WebElement] | Tuple[None, None]:
        """
        Waits for one of two elements identified by a single locator strategy and two distinct queries.

        Args:
            by (str): The locator strategy, e.g., By.ID, By.XPATH.
            queries (List[str]): The query string list for locating an element.
            timeout_duration (int): How long to wait before giving up, in seconds.
            ignore_timeout (bool): If True, no exception is raised if neither element appeared within the timeout.
            labels (str): The labels for the corresponding queried element.

        Returns:
            Tuple[str, WebElement] | Tuple[None, None]: A tuple where the first element is the label or query of the element that was found,
            or None if neither was found, and the second element is the WebElement or None.
        """
        if labels is not None:
            assert len(labels) == len(queries), "Number of labels and queries must have the same size!"
            assert all([isinstance(label, str) for label in labels]), "Every label must be of type str!"
            assert all([len(label) != 0 for label in labels]), "Each label must not be an empty string!"
        else:
            labels = queries.copy()

        self.logger.info(f"[dim cyan]Starting to wait for any of the labels({labels}) to appear on the page.[/]")
        try:
            WebDriverWait(
                self.browser,
                timeout_duration
            ).until(
                EC.any_of(
                    *[EC.visibility_of_element_located((by, query)) for query in queries]
                )
            )
            self.logger.info("[dim]An element has been found. Determining which one it is.[/]")
            for query, label in zip(queries, labels):
                try:
                    element = self.browser.find_element(by, query)
                    self.logger.info(f"[dim]Element '{label}' found.[/]")
                    return label, element
                except Exceptions.NoSuchElementException:
                    self.logger.warning(f"[dim]Element '{label}' not found.[/]")

            raise RuntimeError("No elements were found after at least one was expected!")

        except Exceptions.TimeoutException:
            if ignore_timeout:
                self.logger.warning("[bold yellow]Timeout reached but ignoring since ignore_timeout is True.[/]")
                return None, None
            self.logger.error("[bold red]Timeout occurred. Neither element appeared within the specified time.[/]")
            raise  # Re-raise the exception if ignore_timeout is False

    def _click(
        self,
        element: WebElement,
        label: str = ''
    ) -> bool:
        self.logger.info(f"[dim cyan]Attempting to click '{label}'...[/]")
        if element:
            element.click()
            self.logger.info(f"[dim]Clicked '{label}' successfully[/]")
            return True
        self.logger.warning(f"[bold yellow]No element found for '{label}'![/]")
        return False

    def _input(
        self,
        element: WebElement,
        text: str,
        input_method: Literal["whole", "split_lines", "javascript"] = "whole",
        label: str = ''
    ) -> bool:
        self.logger.info(f"[dim cyan]Attempting to input '{label}'...[/]")
        if element:
            self.logger.info(f"[dim]Element found. Inputting '{label}'...[/]")
            match input_method:
                case 'whole':
                    # 全部输入，加快速度
                    element.send_keys(text)
                case 'split_lines':
                    # 分行输入，避免问题
                    split_text = text.split("\n")
                    for i, each_line in enumerate(split_text):
                        element.send_keys(each_line)
                        # element.send_keys(Keys.SHIFT + Keys.ENTER)
                        if i != len(split_text) - 1:
                            element.send_keys('\n')
                case 'javascript':
                    # 使用 JavaScript 直接设置 textarea 的值
                    self.logger.info('[dim]Sending message...[/]')
                    self.logger.info('[dim]Step.1 Click element.[/]')
                    element.click()
                    time.sleep(1)
                    self.logger.info('[dim]Step.2 Focus on element.[/]')
                    self.browser.execute_script("arguments[0].focus();", element)
                    time.sleep(1)
                    self.logger.info('[dim]Step.3 Fill in element.[/]')
                    self.browser.execute_script("arguments[0].value = arguments[1];", element, text)
                    # time.sleep(1)
                    # self.logger.info('Step.4 Add an additional ENTER.')
                    # element.send_keys(Keys.SHIFT + Keys.ENTER)
                    # element.send_keys('\n')

            self.logger.info(f"[dim]Input has been done with '{label}'![/]")
            return True

        self.logger.warning(f"[bold yellow]No element found for '{label}'![/]")
        return False

    def wait_until_appear_then_click(
        self,
        by: str, query: str,
        timeout_duration: int = 60, ignore_timeout: bool = False,
        label: str = ''
    ) -> bool:
        """
        Attempts to find and click an element based on specified locator `by` and `query`,
        logs the process using the provided `label`, and manages exceptions based on the `ignore_failure` flag.

        Args:
            by (str): The method used to locate the element (e.g., By.ID, By.XPATH).
            query (str): The query string to locate the element.
            timeout_duration (int, optional): The total wait time before the timeout exception. Default: 60.
            ignore_timeout (bool): If True, no exception is raised if the element still not appeared after the timeout.
            label (str): Description used for the element.

        Raises:
            NoSuchElementException: If `ignore_failure` is False and the element does not become clickable.
        """
        label = label or query
        element = self.wait_until_appear(by, query, timeout_duration, ignore_timeout, label=label)
        return self._click(element, label=label)

    def wait_until_appear_then_input(
        self,
        by: str, query: str,
        text: str,
        input_method: Literal["whole", "split_lines", "javascript"] = "whole",
        timeout_duration: int = 60, ignore_timeout: bool = False,
        label: str = ''
    ) -> bool:
        """
        Attempts to find and input into an element based on specified locator `by` and `query`,
        logs the process using the provided `label`, and manages exceptions based on the `ignore_failure` flag.

        Args:
            by (str): The method used to locate the element (e.g., By.ID, By.XPATH).
            query (str): The query string to locate the element.
            text (str): The text to input into the element.
            input_method (str): The method used to send keys.
            timeout_duration (int, optional): The total wait time before the timeout exception. Default: 60.
            ignore_timeout (bool): If True, no exception is raised if the element still not appeared after the timeout.
            label (str): Description used for inputting purposes.

        Raises:
            NoSuchElementException: If `ignore_failure` is False and the element does not become clickable.
        """
        label = label or query
        element = self.wait_until_appear(by, query, timeout_duration, ignore_timeout, label=label)
        return self._input(element, text, input_method, label=label)

    def find_then_click_or_fail(
        self,
        by: str, query: str,
        ignore_failure: bool = False,
        label: str = ''
    ) -> bool:
        label = label or query
        element = self.find_element_or_fail(by, query, ignore_failure=ignore_failure, label=label)
        return self._click(element, label=label)

    def find_then_input_or_fail(
        self,
        by: str, query: str,
        text: str,
        input_method: Literal["whole", "split_lines", "javascript"] = "whole",
        ignore_failure: bool = False,
        label: str = ''
    ) -> bool:
        label = label or query
        element = self.find_element_or_fail(by, query, ignore_failure=ignore_failure, label=label)
        return self._input(element, text, input_method, label=label)

    def check_element_stability(
        self,
        by: str, query: str,
        check_period: int,
        confirmation_time,
        ignore_timeout=False,
        label: str = ''
    ) -> Optional[WebElement]:
        """
        Periodically checks if the content of a web element, located by 'by' and 'query',
        remains unchanged for a 'confirmation_time' after initially detected as unchanged.

        Args:
            by (selenium.webdriver.common.by.By): The method used to locate the element.
            query (str): The query string to locate the element.
            check_period (int): The duration (in seconds) between checks for the element's content.
            confirmation_time (int): The duration (in seconds) the content of the element must remain unchanged to be confirmed stable.
            ignore_timeout (bool): If True, no exception is raised if the element did not meet stability requirements finally.
            label (str): Description used for the element.

        Returns:
            Optional[WebElement]: The web element if its content is confirmed stable.
        """
        label = label or query
        last_content = None
        stability_start_time = None
        self.logger.info(f"[dim cyan]Starting to wait for element '{label}' to be stable at least {confirmation_time}s.[/]")

        while True:
            try:
                # 等待并获取元素
                element = self.wait_until_appear(by=by, query=query, ignore_timeout=ignore_timeout, label=label)
                current_content = element.get_attribute('innerHTML')  # 获取元素内容

                # 检查元素内容是否变化
                if current_content != last_content:
                    # 如果内容变化，更新最后内容和稳定计时开始时间
                    last_content = current_content
                    stability_start_time = time.time()
                    self.logger.info(f"[dim]Element '{label}' content changed, resetting confirmation timer.[/]")

                # 如果元素内容稳定，并且当前时间超过了稳定起始时间加确认时间
                else:
                    stability_duration = time.time() - stability_start_time
                    if stability_start_time and (stability_duration >= confirmation_time):
                        # 在确认时间结束后再次检查内容是否真的没有变化
                        if element.get_attribute('innerHTML') == last_content:
                            self.logger.info(f"[dim]Element '{label}' content has been stable for at least {confirmation_time}s.[/]")
                            return element  # 元素内容稳定，返回元素
                        else:
                            # 如果内容在最后一刻发生变化，重置稳定计时
                            last_content = element.get_attribute('innerHTML')
                            stability_start_time = time.time()
                            self.logger.info(f"[dim]Element '{label}' content changed at the last moment, resetting confirmation timer.[/]")
                    else:
                        self.logger.info(f"[dim]The content not changed for {int(stability_duration)}s...[/]")

                # 等待下一个检查周期
                time.sleep(check_period)
            except Exceptions.TimeoutException:
                if ignore_timeout:
                    self.logger.warning("[bold yellow]Timeout reached but ignoring since ignore_timeout is True.[/]")
                    return None
                self.logger.error(f"[bold red]Element '{label}' did not meet stability requirements finally![/]")
                raise  # Re-raise the exception if ignore_timeout is False
