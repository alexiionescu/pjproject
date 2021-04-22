@ECHO OFF
:: set environment variable with pjproject path
py -3 -m pip uninstall pjsua -y
SET PJ_PYTHON_PATH=%~dp0
cd %~dp0
copy setup-vc.py setup.py
py -3 -m pip install .