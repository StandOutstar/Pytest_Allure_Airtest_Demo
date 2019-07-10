import logging
import types

import allure
from tenacity import Retrying, stop_after_attempt, wait_fixed, RetryError, retry_if_result, retry_if_exception_type

from airtest.core.api import touch, ST
from airtest.core.cv import loop_find
from poco.exceptions import PocoTargetTimeout
from airtest.core.error import TargetNotFoundError

Logger = logging.getLogger(__name__)


class BasePage(object):
    app_name = ''

    def __init__(self, poco_driver):
        self.__driver_poco = poco_driver
        self.logger = logging.getLogger(__name__)

    def poco(self, poco_pos):
        """
        通过参数返回实例
        :param poco_pos: poco 控件参数
        :return: poco 控件实例
        """
        if 'p0' in poco_pos and 'p1' in poco_pos and 'p2' in poco_pos:
            return self.__driver_poco(poco_pos['p0']).child(poco_pos['p1']).child(poco_pos['p2']).child(poco_pos['name'])
        elif 'p0' in poco_pos and 'p1' in poco_pos:
            return self.__driver_poco(poco_pos['p0']).child(poco_pos['p1']).child(poco_pos['name'])
        elif 'p0' in poco_pos:
            return self.__driver_poco(poco_pos['p0']).child(poco_pos['name'])
        else:
            return self.__driver_poco(**poco_pos)

    def __getattribute__(self, attr):
        """
        自定义实例属性获取方法，可以在此处动态绑定方法以简化操作控件。
        """
        _dict = object.__getattribute__(self, '__dict__')
        if attr.startswith('p_'):  # poco 属性前缀 p 用以区别 air 属性
            _proxy = self.poco(_dict[attr])
            if len(_proxy) > 1:  # 含有多个相同元素，每个都需要绑定方法
                for i, p in enumerate(_proxy):
                    _proxy[i].wait_click = types.MethodType(wait_click, _proxy[i])
                    _proxy[i].wait_exists = types.MethodType(wait_exists, _proxy[i])
            else:
                _proxy.wait_click = types.MethodType(wait_click, _proxy)
                _proxy.wait_exists = types.MethodType(wait_exists, _proxy)
            return _proxy

        elif attr.startswith('a_'):  # template img 属性前缀 a 用以区别 poco 属性
            _template = _dict[attr]
            _template.retry_air_touch = types.MethodType(retry_air_touch, _template)
            _template.retry_air_exists = types.MethodType(retry_air_exists, _template)
            return _template

        # 非特殊属性直接返回
        return object.__getattribute__(self, attr)

    def get_poco(self, pos):
        """
        直接获取控件实例，动态控件用此方法。
        :param pos: poco 控件参数
        :return: poco 控件实例
        """
        poco_ins = self.__driver_poco(**pos)
        if len(poco_ins) > 1:  # 含有多个相同元素，每个都需要绑定方法
            for i, p in enumerate(poco_ins):
                poco_ins[i].wait_click = types.MethodType(wait_click, poco_ins[i])
                poco_ins[i].wait_exists = types.MethodType(wait_exists, poco_ins[i])
        else:
            poco_ins.wait_click = types.MethodType(wait_click, poco_ins)
            poco_ins.wait_exists = types.MethodType(wait_exists, poco_ins)
        return poco_ins

    def get_poco_driver(self):
        return self.__driver_poco


@allure.step("等待点击控件, 参数：")
def wait_click(self, timeout=5, **kwargs):
    """
    等待点击控件
    :param self:
    :param timeout: 等待时长
    :param kwargs:
    """
    try:
        self.wait_for_appearance(timeout=timeout)
        self.click(**kwargs)
        Logger.info("poco click {}".format(str(self)))
        allure.attach(body='',
                      name="poco click {}".format(self),
                      attachment_type=allure.attachment_type.TEXT)
    except PocoTargetTimeout as e:
        Logger.info("poco not find: {}".format(str(self)))
        allure.attach(body='',
                      name="poco not find {}".format(self),
                      attachment_type=allure.attachment_type.TEXT)
        raise e


@allure.step("等待检测控件, 参数：")
def wait_exists(self, timeout=5):
    """
    等待检测控件
    :param self:
    :param timeout: 等待时长
    :return:
    """
    try:
        self.wait_for_appearance(timeout=timeout)
        if self.exists():
            Logger.info("poco exists {}".format(str(self)))
            allure.attach(body='',
                          name="poco exists {}".format(self),
                          attachment_type=allure.attachment_type.TEXT)
            return True
        else:
            Logger.info("poco not find: {}".format(str(self)))
            allure.attach(body='',
                          name="poco not find {}".format(self),
                          attachment_type=allure.attachment_type.TEXT)
            return False
    except PocoTargetTimeout:
        logging.info("poco not find: {}".format(str(self)))
        allure.attach(body='',
                      name="poco not find {}".format(self),
                      attachment_type=allure.attachment_type.TEXT)
        return False


@allure.step("重试间隔操作打印数据")
def my_before_sleep(retry_state):
    log_level = logging.DEBUG
    logging.log(
        log_level,
        'Retrying %s: attempt %s ended with: %s',
        retry_state.fn,
        retry_state.attempt_number,
        retry_state.outcome,
    )


@allure.step("重试点击图像, 参数：")
def retry_air_touch(self, whether_retry=True, sleeps=2, max_attempts=2, **kwargs):
    """
    可重试 touch
    Args:
        self: img Template
        whether_retry: whether to retry
        sleeps: time between retry
        max_attempts: max retry times
    """
    with allure.step("点击UI图像: {}".format(str(self))):

        if not whether_retry:
            max_attempts = 1

        r = Retrying(retry=retry_if_exception_type(TargetNotFoundError),
                     wait=wait_fixed(sleeps),
                     stop=stop_after_attempt(max_attempts),
                     before_sleep=my_before_sleep,
                     reraise=True)

        res = None
        try:
            res = r(touch, self, **kwargs)
        except Exception as e:
            res = False
            raise e
        finally:
            logging.info("aircv touch img result: {} on size: {}".format(False if res is False else res, G.DEVICE.get_current_resolution()))
            logging.debug("retry aircv touch statistics: {}".format(str(r.statistics)))
            allure.attach.file(self.filepath,
                               name="aircv touch img result: {}, on size: {}".format(False if res is False else res, G.DEVICE.get_current_resolution()),
                               attachment_type=allure.attachment_type.PNG)


@allure.step("重试检测图像, 参数：")
def retry_air_exists(self, whether_retry=True, sleeps=1.5, max_attempts=3, threshold=None):
    """
    可重试 exists
    Args:
        threshold:
        self: Img Template
        whether_retry: whether to retry
        sleeps: time between retry
        max_attempts: max retry times

    Returns: pos or False

    """
    with allure.step("检测UI图像: {}".format(str(self))):
        if not whether_retry:
            max_attempts = 1

        def retry_exists():
            try:
                logging.debug("img template threshold: {}".format(self.threshold))
                pos = loop_find(self, timeout=ST.FIND_TIMEOUT_TMP, threshold=threshold)
            except TargetNotFoundError:
                return False
            else:
                return pos

        def need_retry(value):
            """
            value为False时需要重试
            Args:
                value: function的返回值，自动填入

            Returns:

            """
            logging.debug("need retry aircv exists?: {}".format(value is False))
            return value is False

        r = Retrying(retry=retry_if_result(need_retry),
                     stop=stop_after_attempt(max_attempts),
                     wait=wait_fixed(sleeps),
                     before_sleep=my_before_sleep)
        res = None
        try:
            res = r(r, retry_exists)
        except RetryError:
            res = False
        finally:
            logging.info("aircv find {}: {}".format(str(self), False if res is False else res))
            logging.debug("retry aircv exists statistics: {}".format(str(r.statistics)))
            allure.attach.file(self.filepath,
                               name="aircv find img result: {}, img:".format(False if res is False else res),
                               attachment_type=allure.attachment_type.PNG)
            return res

