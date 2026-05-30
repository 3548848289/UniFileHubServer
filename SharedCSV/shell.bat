@echo off
cd build || (
    echo ❌ 无法进入 build 文件夹，停止操作。
    exit /b 1
)

echo 进入 build 文件夹成功，开始清理和构建...
del /q *   REM 清空 build 目录内容（仅文件，不包括子目录，可加 /s /q）
cmake ..
make

cd ..
build\BoostAsioServer.exe
