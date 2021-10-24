set PATH=%~dp0python-3.9.7-embed-amd64;%PATH%

rem %~dp0python-3.9.7-embed-amd64\python.exe %~dp0python-3.9.7-embed-amd64\get-pip.py --no-warn-script-location

rem call python -m pip install pythonnet

call python -m pip install --no-warn-script-location opencv-python
call python -m pip install --no-warn-script-location pandas
call python -m pip install --no-warn-script-location matplotlib
call python -m pip install --no-warn-script-location scipy
call python -m pip install --no-warn-script-location scikit-learn