set DIR=%~dp0
set MINICONDA3=%DIR%miniconda38_64

call "%DIR%\Miniconda38_64.exe" /S /InstallationType=JustMe /AddToPath=0 /RegisterPython=0 /NoRegistry=1 /D=%MINICONDA3%
call "%MINICONDA3%\Scripts\activate.bat"
call pip install opencv-python
call pip install pandas
call pip install matplotlib
call pip install scipy
call pip install scikit-learn