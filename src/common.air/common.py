import logging

import allure
from airtest.core.api import *
from poco.drivers.android.uiautomation import AndroidUiautomationPoco
from poco.drivers.ios import iosPoco

using("src/pages/home_page.air")
using("src/pages/second_page.air")

from home_page import AndroidHomePage, IOSHomePage
from second_page import AndroidSecondPage, IOSSecondPage

ANDROID_PLATFORM = "Android"
IOS_PLATFORM = "iOS"


class TestAPP(object):
    def __init__(self, phone_tuple):
        self.logger = logging.getLogger(__name__)

        self.client_platform = phone_tuple.platform
        self.app_name = phone_tuple.package
        self.phone_ip = phone_tuple.ip
        self.phone_port = phone_tuple.port
        self.phone_uuid = phone_tuple.uuid

        self.device_phone = None
        self.poco_phone_driver = None
        self.phone_dev = None

        self.home_page = None
        self.second_page = None

        # 根据平台初始化
        if phone_tuple.platform == ANDROID_PLATFORM:
            self.init_android_app()
        elif phone_tuple.platform == IOS_PLATFORM:
            self.init_ios_app()

    def init_android_app(self):
        # 创建设备驱动
        self.device_phone = connect_device("android://{0}:{1}/{2}".format(
            self.phone_ip, self.phone_port, self.phone_uuid))
        self.phone_dev = self.phone_uuid
        self.poco_phone_driver = AndroidUiautomationPoco(self.device_phone, poll_interval=1)
        # 关闭截图
        self.poco_phone_driver.screenshot_each_action = False

        # 初始化页面
        self.home_page = AndroidHomePage(self.poco_phone_driver)
        self.second_page = AndroidSecondPage(self.poco_phone_driver)

    def init_ios_app(self):
        # 创建设备驱动
        self.device_phone = connect_device("ios:///http://{0}:{1}".format(self.phone_ip, self.phone_port))
        self.phone_dev = "http://{0}:{1}".format(self.phone_ip, self.phone_port)
        self.poco_phone_driver = iosPoco(self.device_phone, poll_interval=1)
        # 关闭截图
        self.poco_phone_driver.screenshot_each_action = False

        # 初始化页面
        self.home_page = IOSHomePage(self.poco_phone_driver)
        self.second_page = IOSSecondPage(self.poco_phone_driver)

    def ensure_current_device(self):
        if device().uuid != self.phone_dev:
            set_current(self.phone_dev)

    @allure.step('点击home键')
    def home(self):
        """点击手机home键"""
        home()

    @allure.step('启动phoneAPP')
    def start_phone_app(self):
        """启动phoneAPP"""
        self.ensure_current_device()
        start_app(self.app_name)
        self.logger.info('start phone app.')

    @allure.step('关闭phoneAPP')
    def stop_phone_app(self):
        """关闭phoneAPP"""
        self.ensure_current_device()
        stop_app(self.app_name)
        self.logger.info('stop phone app.')