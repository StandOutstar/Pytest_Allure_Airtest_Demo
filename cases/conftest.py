
from collections import namedtuple
from functools import wraps

import allure
import pytest
import xlsxwriter
import yaml
from logging import getLogger
from airtest.core.api import *
from airtest.core.helper import device_platform, ST

# 导入 common 包之前先设置 ST.PROJECT_ROOT，因为 using 依赖此路径
from src.utils.function import generate_random_num_str

ST.PROJECT_ROOT = os.environ['PROJECT_SPACE_ROOT']

using("src/common.air")
from common import AndroidApp, IOSApp

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


@allure.step("尝试唤醒当前设备：")
def wake_device(current_device):
    current_device.wake()


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

        try:
            app = None
            if client_platform == ANDROID_PLATFORM:
                app = AndroidApp(Phone(client_platform, phone_ip, phone_port, request.param, app_name))
            elif client_platform == IOS_PLATFORM:
                app = IOSApp(Phone(client_platform, phone_ip, phone_port, request.param, app_name))
            app.base_page.app_name = app.app_name
        except Exception as e:
            logger.error("create app fail: {}".format(e))
            allure.attach(body='',
                          name="create app fail: {}".format(e),
                          attachment_type=allure.attachment_type.TEXT)
            pytest.exit("create app fail: {}".format(e))

        assert (app is not None)

        app.ensure_current_device()

        logger.info("current test platform: {}".format(device_platform()))
        logger.info("start app {0} in {1}:{2}".format(app.app_name, client_platform, G.DEVICE.uuid))

        wake_device(G.DEVICE)

    def teardown_test():
        """
        teardown code
        """
        with allure.step("teardown session"):
            pass

        logger.info("Session stop test.")

    request.addfinalizer(teardown_test)  # 注册teardown, 这样即使setup出现异常，也可以最终调用到

    return app


class SnapShotWriter(object):
    def __init__(self):
        # 创建一个新Excel文件并添加一个工作表。
        excel_path = ST.PROJECT_ROOT + "/data/report.xlsx"
        self.workbook = xlsxwriter.Workbook(excel_path)
        self.current_worksheet = self.workbook.add_worksheet("default")
        self.sheets = {}

        self.android_img_cell_format = {'x_scale': 0.27, 'y_scale': 0.27, 'x_offset': 10, 'y_offset': 10}
        self.ios_img_cell_format = {'x_scale': 0.4, 'y_scale': 0.4, 'x_offset': 10, 'y_offset': 10}
        self.img_cell_format = {'x_scale': 0.4, 'y_scale': 0.4, 'x_offset': 10, 'y_offset': 10}

        if os.environ['client_platform'] == ANDROID_PLATFORM:
            self.img_cell_format = self.android_img_cell_format
        elif os.environ['client_platform'] == IOS_PLATFORM:
            self.img_cell_format = self.ios_img_cell_format

        self.merge_format = self.workbook.add_format({'bold': True, 'bg_color': '#C0C0C0', 'align': 'center'})

        self.first_column = 0
        self.first_row = 0
        self.merge_column_number = 4
        self.internal_column_number = 1
        self.internal_row_number = 1
        self.write_positions = {}

    def next(self):
        write_position = self.write_positions.get(self.current_worksheet.name, [self.first_row, self.first_column])

        self.write_positions[self.current_worksheet.name][0] = write_position[0]
        self.write_positions[self.current_worksheet.name][1] = write_position[1] \
                                                               + self.merge_column_number + 1 + self.internal_column_number

    def reset(self):
        self.write_positions.setdefault(self.current_worksheet.name, [self.first_row, self.first_column])
        self.write_positions[self.current_worksheet.name][0] = self.first_row
        self.write_positions[self.current_worksheet.name][1] = self.first_column

    def switch_sheet(self, name=None):
        """
        切换sheet
        :param name:
        """
        if name:
            self.current_worksheet = self.sheets[name]

    def add_worksheet(self, name=None):
        """
        添加工作表
        :param name:
        """
        if name and str(name) not in self.sheets.keys():
            worksheet = self.workbook.add_worksheet(str(name))
            self.sheets[str(name)] = worksheet
            self.current_worksheet = worksheet
            self.reset()
            return
        if str(name) in self.sheets.keys():
            self.current_worksheet = self.sheets[str(name)]
            return

    def insert_snapshot(self, name=None, path=None):
        """
        插入截屏，只需要知道名字和路径，位置由类处理
        :param name:
        :param path:
        """
        if name is None or path is None:
            logger.info("required parameter missed {} {}".format(name, path))
            return

        logger.info("insert cell {}, file path: {}".format(self.write_positions[self.current_worksheet.name], path))
        self.current_worksheet.merge_range(self.write_positions[self.current_worksheet.name][0],
                                           self.write_positions[self.current_worksheet.name][1],
                                           self.write_positions[self.current_worksheet.name][0],
                                           self.write_positions[self.current_worksheet.name][
                                               1] + self.merge_column_number, name,
                                           self.merge_format)
        self.current_worksheet.insert_image(
            self.write_positions[self.current_worksheet.name][0] + self.internal_row_number,
            self.write_positions[self.current_worksheet.name][1],
            path,
            self.img_cell_format)

    def snapshot_to_excel(self, name=None):
        """
        截屏并写入表格
        :param name:
        """
        file_name = '{}.png'.format(name)
        file_path = os.path.join(allure_results_dir, file_name)
        device().snapshot(file_path)

        logger.info("snapshot path: {}, name: {}".format(file_path, name))
        self.insert_snapshot(name, file_path)
        self.next()

    def close(self):
        self.workbook.close()


@pytest.fixture(scope="session")
def snapshot_writer():
    writer = SnapShotWriter()

    yield writer

    # 关闭文件
    writer.close()


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
