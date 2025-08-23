#!/bin/bash

# 启动 FIleHistory
cd ./FIleHistory
./appFIleHistory &
disown
cd ..

# 启动 SharedCSV
cd ./SharedCSV
./run.sh &
disown
cd ..

# 启动 SharedFile
cd ./SharedFile
./appSharedFile &
disown
cd ..

# 启动 UserInfo
cd ./UserInfo
./appUserInfo &
disown
cd ..

# 保持脚本前台不退出
wait
