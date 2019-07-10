import logging
from importlib import import_module

import allure
from airtest.core.api import *
from poco.drivers.android.uiautomation import AndroidUiautomationPoco
from poco.drivers.ios import iosPoco
from tenacity import Retrying, wait_fixed, stop_after_attempt
from wda import WDAError

ANDROID_PLATFORM = "Android"
IOS_PLATFORM = "iOS"
ANDROID_PAGE_PREFIX = "Android"
ANDROID_PAGE_SUFFIX = "Page"
IOS_PAGE_PREFIX = "IOS"
IOS_PAGE_SUFFIX = "Page"


class App(object):
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

        pages_path = os.path.join(ST.PROJECT_ROOT, 'src/pages')
        packages = os.listdir(pages_path)
        for p in packages:
            absp = os.path.join(pages_path, p)
            using(absp)

    def __getattribute__(self, attr):
        """
        检测到获取page时，动态导入并初始化返回
        :param attr:
        :return:
        """
        sub_page = None
        if attr.endswith('page'):  # 检测是否获取的为page
            page = import_module(attr)
            assert page is not None, f"未从pages目录下获取到指定页面：{attr}"

            if attr == 'base_page':
                return getattr(page, 'BasePage')

            if self.client_platform == ANDROID_PLATFORM:  # 判断平台
                for item in page.__dict__:
                    if item.startswith(ANDROID_PAGE_PREFIX) and item.endswith(ANDROID_PAGE_SUFFIX):
                        sub_page = getattr(page, item)
            elif self.client_platform == IOS_PLATFORM:
                for item in page.__dict__:
                    if item.startswith(IOS_PAGE_PREFIX) and item.endswith(IOS_PAGE_SUFFIX):
                        sub_page = getattr(page, item)

            assert sub_page is not None, f'未从pages目录下获取到 {self.client_platform} 平台指定页面：{attr}'
            return sub_page(self.poco_phone_driver)
        else:
            # 非特殊属性直接返回
            return object.__getattribute__(self, attr)

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


class AndroidApp(App):
    def __init__(self, phone_tuple):
        super().__init__(phone_tuple)
        self.init_driver()
        self.set_system()

    @allure.step('初始化驱动')
    def init_driver(self):
        # 创建设备驱动
        self.device_phone = my_retry_connect("android://{0}:{1}/{2}".format(
            self.phone_ip, self.phone_port, self.phone_uuid))
        self.phone_dev = self.phone_uuid
        self.poco_phone_driver = AndroidUiautomationPoco(self.device_phone, poll_interval=1)
        # 关闭截图
        self.poco_phone_driver.screenshot_each_action = False

    @allure.step('设置系统')
    def set_system(self):
        # 授予权限
        # self.device_phone.shell("pm grant {} {}".format(self.app_name, "android.permission.ACCESS_FINE_LOCATION"))  # 授予位置权限
        # self.device_phone.shell("pm grant {} {}".format(self.app_name, "android.permission.WRITE_EXTERNAL_STORAGE"))  # 授予存储权限
        # 隐藏状态栏
        # self.device_phone.shell("settings put global policy_control immersive.status=*")  # 隐藏状态栏
        # self.device_phone.shell("settings put global policy_control immersive.navigation=*")  # 隐藏导航栏
        # self.device_phone.shell("settings put global policy_control immersive.full=*")  # 隐藏状态栏和导航栏
        pass


class IOSApp(App):

    def __init__(self, phone_tuple):
        super().__init__(phone_tuple)
        self.init_driver()
        self.set_system()

    @allure.step('初始化驱动')
    def init_driver(self):
        # 创建设备驱动
        self.device_phone = my_retry_connect("ios:///http://{0}:{1}".format(self.phone_ip, self.phone_port))
        self.phone_dev = "http://{0}:{1}".format(self.phone_ip, self.phone_port)
        self.poco_phone_driver = iosPoco(self.device_phone, poll_interval=1)
        # 关闭截图
        self.poco_phone_driver.screenshot_each_action = False

    @allure.step('设置系统')
    def set_system(self):
        pass


def my_before_sleep(retry_state):
    if retry_state.attempt_number < 1:
        loglevel = logging.INFO
    else:
        loglevel = logging.WARNING

    logging.log(
        loglevel,
        'Retrying %s: attempt %s ended with: %s',
        retry_state.fn,
        retry_state.attempt_number,
        retry_state.outcome,
    )


def my_retry_connect(uri=None, whether_retry=True, sleeps=10, max_attempts=3):
    """
    可重试 connect
    :param sleeps: 重试间隔时间
    :param uri: device uri
    :param whether_retry: not retry will set the max attempts to 1
    :param max_attempts: max retry times
    """
    logger = logging.getLogger(__name__)

    if not whether_retry:
        max_attempts = 1

    r = Retrying(wait=wait_fixed(sleeps), stop=stop_after_attempt(max_attempts), before_sleep=my_before_sleep, reraise=True)
    try:
        return r(connect_device, uri)
    except Exception as e:
        if isinstance(e, (WDAError,)):
            logger.info("Can't connect iphone, please check device or wda state!")
        logger.info("try connect device {} 3 times per wait 10 sec failed.".format(uri))
        raise e
    finally:
        logger.info("retry connect statistics: {}".format(str(r.statistics)))
