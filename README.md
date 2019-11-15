# Sample for Automated UI Test of Apps. 
![](/img/Xnip2019-05-10_11-00-55.jpg)
![](/img/Xnip2019-05-24_18-14-10.jpg)
![](/img/Xnip2019-05-10_11-14-51.jpg)
![](/img/Xnip2019-05-10_11-03-28.jpg)
![](/img/Xnip2019-05-10_11-06-46.jpg)
## 使用以下优秀工具: 
- pipenv
- pytest
- allure
- airtest
- jenkins

## 使用Jenkins插件:
- git
- Extended Choice Parameter
- Allure

## iOS 所需工具:
- Apple Configurator 2（可从App Store安装） 命令行工具 cfgutil

## 说明:
- run.sh 工作流程
- 使用 pipenv 管理虚拟环境，--skip-lock 应对 pipenv lock问题
- 在 config.py 中获取 Jenkins Job 参数，写入配置文件，安装APP，参数写入 allure environment 文件用以展示
- 使用 pytest 来组织管理和运行用例
- 使用 airtest 来操作APP页面
- 使用 allure 来记录信息和生成报告
- 采用 PageObject 组织页面，以复用代码和后期维护
- 使用魔法方法 __ __getattribute__ __ 实现简化控件获取使用和动态获取页面对象
    - 控件只需以字典方式定义，便可自动获取并实例化
    - 页面只需创建，便可自动获取并实例化
- 使用 命令行工具 cfgutil 来管理 iOS APP
- 屏幕截图存放在 data/report.xlsx 中

## 运行配置：
- phones 可定义多个，则会在每个设备上轮流运行用例
- iOS 要按照airtest的说明配置iOS-Tagent，和iproxy

## 注意：
- data 目录下存放着一个Android 示例应用
- 需测试 iOS 的话，应该在 Mac 机上部署，比如在 Macmini 上。
- 示例中没有使用git仓库，可自行配置
- 本地运行单个用例建议使用 pycharm，添加 pytest 并设置参数运行
![pycharm配置测试示例](/img/Xnip2019-05-08_14-33-11.jpg)
![Pycharm pytest 运行结果图](/img/Xnip2019-05-09_17-18-27.jpg)
- [Jenkins示例参数化配置](/img/Xnip2019-05-09_17-01-37.jpg)

## Jenkins中查看Allure Report:
![](/img/Xnip2019-07-10_19-40-53.jpg)
![](/img/Xnip2019-05-09_17-22-23.jpg)
![](/img/Xnip2019-05-09_17-07-08.jpg)
![](/img/Xnip2019-05-09_17-08-34.jpg)

## 截图表格
![](/img/Xnip2019-05-30_17-48-41.jpg)

## 建议：
- 深入学习编程技术
- 深入学习 自动化测试技术
- 深入学习 Pytest, Allure, Airtest 等框架


Todo:
- 丰富功能
  - [x] 异常捕获并截屏
  - [x] wait exists, click
  - [x] 绑定 wait exists, click
  - [x] 截图到Excel中
  - [x] 重试连接设备
  - [x] 绑定可重试图像操作
- 重构
  - [x] 动态获取页面
