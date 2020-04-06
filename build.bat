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
	echo -e             : Setup cuurent env
	echo -s             : Re-setup virtual enviroment
	echo -d             : Delete virtual enviroment
	goto end

:delete_virtual_env
	pipenv --rm
	goto end


:setup_virtual_env
	pipenv install
	pipenv run %0 -ve
	
	goto end

:setup_venv
	Rem Use 5.12.0 to match another lib's dependency. But it does not have to.
	pip install pyqt5==5.12.0
	pip install pyqtwebengine==5.12.0
	pip install bs4
	pip install lxml
	pip install requests
	pip install pandas
	pip install pymongo
	pip install openpyxl
	pip install tushare
	pip install matplotlib
	pip install mpl_finance

	pip uninstall pyinstaller
	pip install https://github.com/pyinstaller/pyinstaller/archive/develop.zip
	
	goto end

:setup_env
	Rem Use 5.12.0 to match another lib's dependency. But it does not have to.
	pip install --user pyqt5==5.12.0
	pip install --user pyqtwebengine==5.12.0
	pip install --user bs4
	pip install --user lxml
	pip install --user requests
	pip install --user pandas
	pip install --user pymongo
	pip install --user openpyxl
	pip install --user tushare
	pip install --user matplotlib
	pip install --user mpl_finance
	
	Rem Note that mpl_finance will be deprecated and the new lib named mplfinance whose api is way different from mpl_finance
	Rem pip install --user --upgrade mplfinance --proxy=

	pip uninstall pyinstaller
	pip install https://github.com/pyinstaller/pyinstaller/archive/develop.zip
	
	goto end


:build
	pipenv run %0 -build_in_virtual_env
	goto end

:build_in_virtual_env
	del main.spec
	rmdir /s /q dist
	rmdir /s /q build
	
	pyi-makespec --hidden-import pandas --icon="res/logo.ico" main.py
	Rem pyi-makespec -w --hidden-import pandas --icon="res/logo.ico" main.py

	pyinstaller main.spec
	
	rmdir /s/q "Analyzer/__pycache__"
	rmdir /s/q "Collector/__pycache__"
	rmdir /s/q "Extension/__pycache__"

	Rem Copy plug-in
	xcopy "Analyzer" "dist/main/Analyzer" /e /i /h /s
	xcopy "Collector" "dist/main/Collector" /e /i /h /s
	xcopy "Extension" "dist/main/Extension" /e /i /h /s
	
	xcopy "README.md" "dist\main\"

	Rem Copy empty sqlite db to data path
	Rem xcopy "res\sAsUtility.db.empty" "dist\main\Data\"
	Rem ren "dist\main\Data\sAsUtility.db.empty" "sAsUtility.db"
	
	Rem Copy export mongodb and sqlite db to offline_data path
	xcopy "Data\sAsUtility.db" "dist\main\Data\"
	Rem xcopy "res\StockAnalysisSystem.zip.*" "dist\offline_data\"
	
	goto end


:clean
	del main.spec
	rmdir /s /q dist
	rmdir /s /q build
	goto end

:end
	echo End...
	pause






