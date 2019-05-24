import logging

import allure
from airtest.core.api import *

using("src/pages/base_page.air")
from base_page import BasePage


class SecondPage(BasePage):
    def __init__(self, poco_driver):
        super().__init__(poco_driver)
        self.logger = logging.getLogger(__name__)

    @allure.step("检测是否为Second页面")
    def is_second_page(self):
        if self.p_title.wait_exists():
            self.logger.info("检测到控件：{}".format(self.p_title))
            return True
        else:
            self.logger.info("未检测到控件：{}".format(self.p_title))
            return False

    @allure.step("点击返回")
    def click_back(self):
        if self.p_btn_back.wait_exists():
            self.logger.info("检测到控件：{}".format(self.p_title))
        else:
            self.logger.info("未检测到控件：{}".format(self.p_title))
        self.p_btn_back.wait_click()


class AndroidSecondPage(SecondPage):
    def __init__(self, poco_driver):
        super().__init__(poco_driver)

        self.p_btn_back = {"name": "转到上一层级", 'type': "android.widget.ImageButton"}
        self.p_title = {"name": "com.app.demo:id/title_second", "text": "Second"}


class IOSSecondPage(SecondPage):
    def __init__(self, poco_driver):
        super().__init__(poco_driver)

        self.p_btn_back = {"name": "black", "type": "Button"}
        self.p_title = {"name": "Second", "type": "StaticText"}
