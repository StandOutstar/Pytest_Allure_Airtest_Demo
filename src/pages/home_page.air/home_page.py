import logging

import allure
from airtest.core.api import *

using("src/pages/base_page.air")
from base_page import BasePage


class HomePage(BasePage):
    def __init__(self, poco_driver):
        super().__init__(poco_driver)
        self.logger = logging.getLogger(__name__)

    @allure.step("检测是否为Home页面")
    def is_home_page(self):
        if self.p_title.wait_exists():
            self.logger.info("检测到控件：{}".format(self.p_title))
            return True
        else:
            self.logger.info("未检测到控件：{}".format(self.p_title))
            return False

    @allure.step("点击下一步")
    def click_next(self):
        if self.p_btn_next.wait_exists():
            self.logger.info("检测到控件：{}".format(self.p_title))
        else:
            self.logger.info("未检测到控件：{}".format(self.p_title))
        self.p_btn_next.wait_click()


class AndroidHomePage(HomePage):
    def __init__(self, poco_driver):
        super().__init__(poco_driver)

        self.p_btn_next = {"name": "com.app.demo:id/btn_next"}
        self.p_title = {"text": "Home"}


class IOSHomePage(HomePage):
    def __init__(self, poco_driver):
        super().__init__(poco_driver)

        self.p_btn_next = {"name": "Next", "type": "Button"}
        self.p_title = {"name": "Home", "type": "StaticText"}
