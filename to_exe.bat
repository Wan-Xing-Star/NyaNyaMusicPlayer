pyinstaller --onefile --windowed --icon="%CD%\static\img\main.ico" --name=NyaNyaMusic_v2.1.1 --specpath="%CD%\temp\spec" --workpath="%CD%\temp\build" --distpath="%CD%\temp\dist" Player_main.py

pyinstaller --onefile --icon="%CD%\static\img\main.ico" --add-data "%CD%\static;static" --add-data "%CD%\templates;templates" --name=NyaNyaData_v2.1 --specpath="%CD%\temp\spec" --workpath="%CD%\temp\build" --distpath="%CD%\temp\dist" NyaData.py
pause