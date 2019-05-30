import logging
import allure
import pytest
from airtest.core.api import *

from cases.conftest import catch_error

logger = logging.getLogger(__name__)
epic = os.getenv('client_platform')
feature = 'app'
story = 'all'


@allure.epic(epic)
@allure.feature(feature)
@allure.story(story)
class TestDemo(object):
    @pytest.fixture(scope="function")
    def app(self, request, app_fixture, snapshot_writer):
        app_ins = app_fixture

        @allure.step
        def setup_func():
            """
            用例前置
            """
            # 创建sheet，不存在会创建，已存在就切换为当前sheet，默认sheet 为 default，
            snapshot_writer.add_worksheet(feature)

            app_ins.start_phone_app()
            sleep(2)

        @allure.step
        def teardown_func():
            """
            用例后置
            """
            app_ins.stop_phone_app()
            sleep(2)

        request.addfinalizer(teardown_func)  # 注册teardown, 这样即使setup出现异常，也可以最终调用到
        setup_func()
        return app_ins

    @allure.severity(allure.severity_level.BLOCKER)
    @catch_error
    def test_home_to_second(self, app, snapshot_writer):
        """
        测试home to second
        """
        app.home_page.click_next()
        sleep(2)
        assert app.second_page.is_second_page(), "确认进入second页失败"

        snapshot_writer.snapshot_to_excel("second页")

        app.second_page.click_back()
        sleep(2)
        assert app.home_page.is_home_page(), "确认退出到home页失败"

        snapshot_writer.snapshot_to_excel("home页")
