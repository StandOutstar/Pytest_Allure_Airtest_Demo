
from collections import namedtuple
from functools import wraps

import allure
import pytest
import yaml
from logging import getLogger
from airtest.core.api import *
from airtest.core.helper import device_platform, ST

# 导入 common 包之前先设置 ST.PROJECT_ROOT，因为 using 依赖此路径
from src.utils.function import generate_random_num_str

ST.PROJECT_ROOT = os.environ['PROJECT_SPACE_ROOT']

using("src/common.air")
from common import TestAPP

ANDROID_PLATFORM = "Android"
IOS_PLATFORM = "iOS"
TESTCASEPATTERN = "https://demo.feie.work/projects/2/cases/{}"

Phone = namedtuple('Phone', ['platform', 'ip', 'port', 'uuid', 'package'])

logger = getLogger(__name__)
logger.info("get PROJECT_ROOT: {}".format(ST.PROJECT_ROOT))

CLIENT_CONFIGURATION_PATH = os.path.join(ST.PROJECT_ROOT, "configuration.yaml")
logger.info("CLIENT_CONFIGURATION_PATH : {}".format(CLIENT_CONFIGURATION_PATH))

# 读取配置
with open(CLIENT_CONFIGURATION_PATH, 'r', encoding='utf-8') as f:
    config = yaml.load(f, Loader=yaml.FullLoader)
    logger.info("get client configuration: \n {}".format(config))

# 把运行平台设置到环境中
os.environ['client_platform'] = config['client_platform']

phone_ip = config['client_ip']
phone_port = config['client_port']
app_name = config['app_name']
test_phones = config['phones']


@pytest.fixture(params=test_phones, scope="session")
def app_fixture(request):
    """
    相当于setupclass、teardownclas，提供公共资源，测试完毕释放资源
    """
    with allure.step("工程初始化和生成APP对象"):
        """
        setup code
        """
        logger.info("Session start test.")

        ST.THRESHOLD_STRICT = 0.6
        client_platform = os.getenv('client_platform')

        app = TestAPP(Phone(client_platform, phone_ip, phone_port, request.param, app_name))

        assert (app is not None)

        app.ensure_current_device()

        logger.info("current test platform: {}".format(device_platform()))
        logger.info("start app {0} in {1}:{2}".format(app.app_name, client_platform, G.DEVICE.uuid))

    def teardown_test():
        """
        teardown code
        """
        with allure.step("teardown session"):
            pass

        logger.info("Session stop test.")

    request.addfinalizer(teardown_test)  # 注册teardown, 这样即使setup出现异常，也可以最终调用到

    return app


allure_results_dir = os.path.join(ST.PROJECT_ROOT, 'allure-results')


def catch_error(func):
    """
    装饰器，获取cases异常，进行截图并attach, 将log传入allure
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        result = None
        try:
            result = func(*args, **kwargs)
        except Exception as e:
            file_name = '{}.png'.format(generate_random_num_str())
            file_path = os.path.join(allure_results_dir, file_name)
            device().snapshot(file_path)
            sleep(0.5)  # 避免截图操作慢时找不到图片
            if os.getenv('client_platform') == IOS_PLATFORM:
                allure.attach.file(file_path,
                                   name="current orientation {} and screen shot".format(device().orientation),
                                   attachment_type=allure.attachment_type.PNG)
            elif os.getenv('client_platform') == ANDROID_PLATFORM:
                allure.attach.file(file_path,
                                   name="current orientation {} and screen shot".format(
                                       device().display_info['orientation']),
                                   attachment_type=allure.attachment_type.PNG)
            logger.exception("Catch Exception\n")
            raise e
        return result

    wrapper.__name__ = 'catch_error'
    return wrapper
