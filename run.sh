echo "运行虚拟环境检查和安装"
pipenv --venv
if [[ "$?" -ne 0 ]]; then
    echo "no virtualenv found, create venv and install package"
    pipenv install --skip-lock --python 3.6
else
    echo "virtualenv found, try install package"
    pipenv install --skip-lock
fi

echo "授予adb执行权限"
export VENV_HOME_DIR=$(pipenv --venv)
source $VENV_HOME_DIR/bin/activate
chmod +x $VENV_HOME_DIR/lib/python3.6/site-packages/airtest/core/android/static/adb/mac/adb

echo "设置工程根路径"
export PROJECT_SPACE_ROOT=$(pwd)

echo "清理报告碎片文件"
python3 ./allure-results/clear_results.py

echo "删除上次报告"
rm -rf ./allure-report/*

echo "运行配置"
python3 config.py

echo "运行测试"
python3 -m pytest --reruns 1 ./cases --alluredir=./allure-results/

echo "执行完毕"
exit 0
