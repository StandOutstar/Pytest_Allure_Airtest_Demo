import os
import yaml
import subprocess
import time
import requests
from pathlib import Path
from logging import getLogger
from src.utils.analysis_ipa import analyze_ipa_with_plistlib
from src.utils.rw_xml import dict_to_xml_tree, out_xml

PROJECT_ROOT = os.environ["PROJECT_SPACE_ROOT"]  # 该环境变量运行时在run.sh中设置过

ALLURE_RESULT_XML_PATH = os.path.join(PROJECT_ROOT, "allure-results/environment.xml")
CLIENT_CONFIGURATION_PATH = os.path.join(PROJECT_ROOT, "configuration.yaml")

ANDROID_PLATFORM = "Android"
IOS_PLATFORM = "iOS"
BRANCH_DEBUG = "Debug"
BRANCH_RELEASES = "Releases"

ANDROID_DEBUG_PACKAGE_NAME = "com.app.demo"
ANDROID_RELEASES_PACKAGE_NAME = ""
IOS_DEBUG_PACKAGE_NAME = ""
IOS_RELEASES_PACKAGE_NAME = ""

logger = getLogger(__name__)

logger.info("set PROJECT_ROOT: {}".format(PROJECT_ROOT))
logger.info("set allure results path: {}".format(ALLURE_RESULT_XML_PATH))
logger.info("set client configuration file path: {}".format(CLIENT_CONFIGURATION_PATH))


def cp_file(src, dst):
    """拷贝路径文件到指定路径"""
    recode = subprocess.call("cp {} {}".format(src, dst), shell=True)
    if recode != 0:
        logger.info("cp file failed, src: {}, dst: {}".format(src, dst))


def download_file(src, dst):
    """从源地址下载文件写入到目标路径"""
    r = requests.get(src)
    if r.status_code != requests.codes.ok:
        logger.info("down load file failed, url: {}".format(src))
        logger.debug(r.content)
        return False
    else:
        with open(dst, "wb") as f:
            f.write(r.content)
        return True


def parse_android_appversion(device, app_name):
    """get android app version through adb dumpsys package"""
    version_string = subprocess.check_output("adb -s {} shell dumpsys package {} | grep versionName".format(device, app_name), shell=True)
    version = version_string.decode("utf-8").replace("\r\n", "").split("=")[1]
    logger.info("Get android versions: {} {} ".format(version, device))
    return version


def parse_ios_appversion(file_path):
    """parse ios app version from local file."""
    version = analyze_ipa_with_plistlib(file_path)
    logger.info("Get ios versions: {} {} ".format(version, file_path))
    return version


def get_parametr(client_info):
    """从环境中获取设备信息写入配置文件"""
    device_info = {
        'client_platform': os.environ["Client_Platform"].strip(),
        'client_ip': os.environ["Client_IP"].strip(),
        'client_port': os.environ["Client_Port"].strip(),
        'client_reinstall': os.environ["Client_ReInstall"].strip(),
        'app_name': os.environ["APP_Name"].strip(),
        'app_branch': os.environ["APP_Branch"].strip(),
        'phones': os.environ["Phones"].strip().split(','),
        'android_debug_app_localPath': os.environ["Android_Debug_APP_LocalPath"].strip(),
        'ios_debug_app_localPath': os.environ["iOS_Debug_APP_LocalPath"].strip(),
        'android_release_app_localPath': os.environ["Android_Release_APP_LocalPath"].strip(),
        'ios_release_app_localPath': os.environ["iOS_Release_APP_LocalPath"].strip(),
    }
    try:
        pass
    except KeyError:
        raise KeyError("please check parameters")

    with open(CLIENT_CONFIGURATION_PATH, 'w', encoding='utf-8') as f:
        yaml.dump(device_info, f)

    with open(CLIENT_CONFIGURATION_PATH, 'r', encoding='utf-8') as f:
        data = yaml.load(f, Loader=yaml.FullLoader)
        logger.info("input parameters: {}".format(data))

    client_info.update(device_info)


def write_to_configuration(client_info):
    with open(CLIENT_CONFIGURATION_PATH, 'w', encoding='utf-8') as f:
        yaml.dump(client_info, f)


def get_app_info(client_info):
    """获取设备信息，解析对应APP版本信息"""
    version = None
    app_name = None
    device = client_info["phones"][0]  # 目前只测试一个设备
    if client_info["client_platform"] == ANDROID_PLATFORM:

        if client_info['app_branch'] == BRANCH_DEBUG:
            version = parse_android_appversion(device, ANDROID_DEBUG_PACKAGE_NAME)
            app_name = ANDROID_DEBUG_PACKAGE_NAME
        elif client_info['app_branch'] == BRANCH_RELEASES:
            app_name = ANDROID_RELEASES_PACKAGE_NAME
            version = parse_android_appversion(device, ANDROID_RELEASES_PACKAGE_NAME)

    elif client_info["client_platform"] == IOS_PLATFORM:
        if client_info['app_branch'] == BRANCH_DEBUG:
            app_name = IOS_DEBUG_PACKAGE_NAME
            version = parse_ios_appversion(client_info["ios_debug_app_localPath"])
        elif client_info['app_branch'] == BRANCH_RELEASES:
            app_name = IOS_RELEASES_PACKAGE_NAME
            version = parse_ios_appversion(client_info["ios_release_app_localPath"])

    assert version, "获取APP版本version失败"
    assert app_name, "获取APP包名app_name失败"
    client_info.update(app_version=version, app_name=app_name)

    write_to_configuration(client_info)


def get_android_app(file_path):
    """从指定文件路径获取iOS APP"""
    apk_location = os.path.join(PROJECT_ROOT, "data/android_latest.apk")
    if os.path.isfile(apk_location):  # file可能不存在
        logger.info("apk file exists")
        os.remove(apk_location)
    if not os.path.exists(os.path.dirname(apk_location)):
        logger.info("文件目录路径不存在：{}".format(os.path.dirname(apk_location)))
        os.mkdir(os.path.dirname(apk_location))
    cp_file(file_path, apk_location)
    return apk_location


def get_ios_app(file_path):
    """从指定文件路径获取iOS APP"""
    ipa_location = os.path.join(PROJECT_ROOT, "data/ios_latest.ipa")
    if os.path.isfile(ipa_location):  # file可能不存在
        logger.info("ipa file exists")
        os.remove(ipa_location)
    if not os.path.exists(os.path.dirname(ipa_location)):
        os.mkdir(os.path.dirname(ipa_location))
    cp_file(file_path, ipa_location)
    return ipa_location


def install_android_app(device_ids, path):
    """向指定Android设备安装指定位置APP"""
    # 路径校验
    logger.info("install file path: {}".format(path))
    p = Path(path)
    if not p.is_file():
        raise ValueError("please check file exists: {}.".format(path))
    if p.suffix != ".apk":
        raise ValueError("please check file whether a apk.")

    # 安装apk
    time.sleep(3)
    for device_id in device_ids:
        subprocess.call("adb -s {} install {}".format(device_id, path), shell=True)


def uninstall_android_app(device_ids, app_name):
    """卸载Android APP"""
    for device_id in device_ids:
        subprocess.call("adb -s {} uninstall {}".format(device_id, app_name), shell=True)


def install_ios_app(device_ids, path):
    """向指定设备安装指定位置APP"""
    # 路径校验
    p = Path(path)
    if not p.is_file():
        raise ValueError("please check file exists: {}".format(path))
    if p.suffix != ".ipa":
        raise ValueError("please check file whether a ipa.")

    # 安装ipa
    for device_id in device_ids:
        p = subprocess.Popen("cfgutil -e {} install-app {}".format(device_id, path), shell=True, stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT)
        while p.poll() is None:
            line = p.stdout.readline().decode("utf-8")
            line = line.strip()
            if line:
                logger.debug('cfgutil install output: [{}]'.format(line))
        if p.returncode == 0:
            logger.info('cfgutil install success')
            time.sleep(60)
            logger.debug("cfgutil install should be done")
        else:
            logger.info('cfgutil install failed')


def uninstall_ios_app(device_ids, app_name):
    """卸载APP"""
    for device_id in device_ids:
        p = subprocess.Popen("cfgutil -e {} remove-app {}".format(device_id, app_name), shell=True,
                             stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        while p.poll() is None:
            line = p.stdout.readline().decode("utf-8")
            line = line.strip()
            if line:
                logger.debug('cfgutil uninstall output: [{}]'.format(line))
        if p.returncode == 0:
            logger.info('cfgutil uninstall success: {}'.format(device_id))
        else:
            logger.info('cfgutil uninstall failed: {}'.format(device_id))


def install_client_app(client_info):
    """通过设备信息安装APP"""
    if client_info["client_reinstall"] == "false":
        return

    device_ids = client_info["phones"]
    file_uri = None
    if client_info["client_platform"] == ANDROID_PLATFORM:
        if client_info['app_branch'] == BRANCH_DEBUG:
            file_uri = client_info['android_debug_app_localPath']
        elif client_info['app_branch'] == BRANCH_RELEASES:
            file_uri = client_info['android_release_app_localPath']

        assert file_uri, "未获取到安装文件路径"
        local_path = get_android_app(file_uri)
        install_android_app(device_ids, local_path)

    elif client_info["client_platform"] == IOS_PLATFORM:
        if client_info['app_branch'] == BRANCH_DEBUG:
            file_uri = client_info['ios_debug_app_localPath']
        elif client_info['app_branch'] == BRANCH_RELEASES:
            file_uri = client_info['ios_release_app_localPath']

        assert file_uri, "未获取到安装文件路径"
        local_path = get_ios_app(file_uri)
        install_ios_app(device_ids, local_path)


def uninstall_client_app(client_info):
    """通过设备信息卸载APP"""
    device_id = client_info['phones']
    app_name = None
    if client_info["client_platform"] == ANDROID_PLATFORM:
        if client_info['app_branch'] == BRANCH_DEBUG:
            app_name = ANDROID_DEBUG_PACKAGE_NAME
        elif client_info['app_branch'] == BRANCH_RELEASES:
            app_name = ANDROID_RELEASES_PACKAGE_NAME

        assert app_name, "未获取到应用包名"
        uninstall_android_app(device_id, app_name)

    elif client_info["client_platform"] == IOS_PLATFORM:
        if client_info['app_branch'] == BRANCH_DEBUG:
            app_name = IOS_DEBUG_PACKAGE_NAME
        elif client_info['app_branch'] == BRANCH_RELEASES:
            app_name = IOS_RELEASES_PACKAGE_NAME

        assert app_name, "未获取到应用包名"
        uninstall_ios_app(device_id, app_name)


def write_appinfo_xml(client_info):
    """读取版本信息，写入allure-results中的environment.xml"""
    platform = client_info['client_platform']
    phones = client_info['phones']
    version = client_info['app_version']
    branch = client_info['app_branch']

    app_name = None
    app_local_path = None
    if client_info["client_platform"] == ANDROID_PLATFORM:
        if client_info['app_branch'] == BRANCH_DEBUG:
            app_name = ANDROID_DEBUG_PACKAGE_NAME
            app_local_path = client_info['android_debug_app_localPath']
        elif client_info['app_branch'] == BRANCH_RELEASES:
            app_name = ANDROID_RELEASES_PACKAGE_NAME
            app_local_path = client_info['android_release_app_localPath']

    elif client_info["client_platform"] == IOS_PLATFORM:
        if client_info['app_branch'] == BRANCH_DEBUG:
            app_name = IOS_DEBUG_PACKAGE_NAME
            app_local_path = client_info['ios_debug_app_localPath']
        elif client_info['app_branch'] == BRANCH_RELEASES:
            app_name = IOS_RELEASES_PACKAGE_NAME
            app_local_path = client_info['ios_release_app_localPath']

    d = {
        0: {'key': 'test platform', 'value': platform},
        1: {'key': 'test app name', 'value': app_name},
        2: {'key': 'test app version', 'value': version},
        3: {'key': 'test app branch', 'value': branch},
        4: {'key': 'test app local path', 'value': app_local_path},
        5: {'key': 'test phones', 'value': "|".join(phones)},
    }

    tree = dict_to_xml_tree(d, "environment", "parameter")
    out_xml(tree, ALLURE_RESULT_XML_PATH)


def main():
    """
    1. 获取安装APP 
    2. 信息写入xml
    """

    client_info = {}
    get_parametr(client_info)

    if client_info["client_reinstall"] == "true":
        uninstall_client_app(client_info)
        install_client_app(client_info)

    get_app_info(client_info)
    write_appinfo_xml(client_info)


if __name__ == '__main__':
    main()
