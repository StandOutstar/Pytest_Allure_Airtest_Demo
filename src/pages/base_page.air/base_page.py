import logging


class BasePage(object):
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
            return _proxy

        elif attr.startswith('a_'):  # template img 属性前缀 a 用以区别 poco 属性
            _template = _dict[attr]
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
        return poco_ins

    def get_poco_driver(self):
        return self.__driver_poco

