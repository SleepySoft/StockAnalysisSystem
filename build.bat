echo off

if "X%1" == "X" (
	echo build
	goto build
) else if "%1" == "-b" (
	echo build
	goto build
) else if "%1" == "-c" (
	echo clean
	goto clean
	
) else if "%1" == "-p" (
	echo pack library
	goto pack_library
) else if "%1" == "-u" (
	echo upload library
	goto upload_library
	
) else if "%1" == "-i" (
	echo install library
	goto install_library
) else if "%1" == "-r" (
	echo uninstall library
	goto uninstall_library
	
) else if "%1" == "-e" (
	echo setup_env
	goto setup_env
) else if "%1" == "-ve" (
	echo setup_venv
	goto setup_venv
) else if "%1" == "-s" (
	echo setup_virtual_env
	goto setup_virtual_env
) else if "%1" == "-d" (
	echo delete_virtual_env
	goto delete_virtual_env
) else if "%1" == "-build_in_virtual_env" (
	echo build_in_virtual_env
	goto build_in_virtual_env
) else goto help

goto end

:help
	echo -b or no param : Build
	echo -c             : Clean Build
	echo -p             : Pack library in dist/
	echo -u             : Upload library in dist/ to pypi
	echo -r             : Remove  library from current python enviroment
	echo -e             : Setup current env
	echo -s             : Re-setup virtual enviroment
	echo -d             : Delete virtual enviroment
	goto end

:delete_virtual_env
	pipenv --rm
	goto end


:setup_virtual_env
	Rem pipenv run %0 -ve
	pipenv install -r requirements.txt --skip-lock
	pipenv install -e git+https://github.com/pyinstaller/pyinstaller.git@develop#egg=PyInstaller
	goto end

:setup_venv
	Rem Use 5.12.0 to match another lib's dependency. But it does not have to.
	Rem pip install pyqt5==5.12.0
	Rem pip install pyqtwebengine==5.12.0
	Rem pip install bs4
	Rem pip install lxml
	Rem pip install requests
	Rem pip install pandas
	Rem pip install pymongo
	Rem pip install openpyxl
	Rem pip install tushare
	Rem pip install pylab-sdk
	Rem pip install matplotlib
	Rem pip install requests_html
	Rem pip install PyExecJS
	
	pip install -r requirements.txt

	pip uninstall pyinstaller
	pip install https://github.com/pyinstaller/pyinstaller/archive/develop.zip
	
	goto end

:setup_env
	pip install -r requirements.txt

	pip uninstall pyinstaller
	pip install --user https://github.com/pyinstaller/pyinstaller/archive/develop.zip
	
	goto end


:build
	Rem pipenv run %0 -build_in_virtual_env
	Rem pyi-makespec -w --hidden-import pandas --hidden-import pyqtgraph --icon="res/logo.ico" main.py
	
	Rem del main.spec
	rmdir /s /q dist
	rmdir /s /q build
	
	Rem pyi-makespec --icon="res/logo.ico" main.py
	Rem pipenv run pyinstaller main.spec
	pyinstaller --hidden-import pyqtgraph --icon="res/logo.ico" main.py
	
	rmdir /s/q "StockAnalysisSystem/plugin/Analyzer/__pycache__"
	rmdir /s/q "StockAnalysisSystem/plugin/Collector/__pycache__"
	rmdir /s/q "StockAnalysisSystem/plugin/Extension/__pycache__"

	Rem Copy plug-in
	xcopy "StockAnalysisSystem/plugin" "dist/main/plugin" /e /i /h /s
	
	xcopy "README.md" "dist\main\"
	xcopy "Data\sAsUtility.db" "dist\main\Data\"
	
	Rem Avoid exception on old platform
	del "dist\main\Qt5Bluetooth.dll"
	
	ren dist\main StockAnalysisSystem
	
	goto end
	
	
	
	goto end
	
:pack_library:
	rmdir /s /q StockAnalysisSystem.egg-info
	python setup.py clean --all
	python setup.py sdist
	goto end

:upload_library
	pip install --user twine
	twine upload ./dist/*
	goto end

:install_library
	pip install StockAnalysisSystem
	goto end
	
:uninstall_library
	pip uninstall StockAnalysisSystem
	goto end
	
:build_in_virtual_env
	del main.spec
	rmdir /s /q dist
	rmdir /s /q build
	
	pyi-makespec --hidden-import pandas --hidden-import pyqtgraph --icon="res/logo.ico" main.py
	Rem pyi-makespec -w --hidden-import pandas --hidden-import pyqtgraph --icon="res/logo.ico" main.py

	pyinstaller main.spec
	
	rmdir /s/q "StockAnalysisSystem/plugin/Analyzer/__pycache__"
	rmdir /s/q "StockAnalysisSystem/plugin/Collector/__pycache__"
	rmdir /s/q "StockAnalysisSystem/plugin/Extension/__pycache__"

	Rem Copy plug-in
	xcopy "StockAnalysisSystem/plugin" "dist/main/plugin" /e /i /h /s
	
	xcopy "README.md" "dist\main\"
	xcopy "Data\sAsUtility.db" "dist\main\Data\"
	
	Rem Avoid exception on old platform
	del "dist\main\Qt5Bluetooth.dll"
	
	ren dist\main StockAnalysisSystem
	
	goto end

:clean
	del main.spec
	rmdir /s /q dist
	rmdir /s /q build
	python setup.py clean --all
	rmdir /s /q StockAnalysisSystem.egg-info
	goto end

:end
	echo End...
	pause






