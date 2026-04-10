@echo off
cd /d "%~dp0"

:: ========== 配置区域（直接填写完整文件名） ==========
set PACKAGE_NAME=NyaNyaMusic_v2.1.1-Bate.7z
set EXE_DATA=NyaNyaData_v2.1.exe
set EXE_MUSIC=NyaNyaMusic_v2.1.1.exe
:: ====================================================

if not exist release mkdir release

:: 添加 static 和 templates 文件夹
7z a -t7z -mx=9 release\%PACKAGE_NAME% static templates

:: 切换到 exe 所在目录
pushd temp\dist

:: 分开单独添加两个 exe 文件
7z a -t7z -mx=9 ..\..\release\%PACKAGE_NAME% %EXE_DATA%
7z a -t7z -mx=9 ..\..\release\%PACKAGE_NAME% %EXE_MUSIC%

popd

echo 打包完成，压缩包位于 release\%PACKAGE_NAME%





pause