#!/bin/bash

# 尝试进入 build 文件夹
if cd ./build; then
    echo "进入 build 文件夹成功，开始清理和构建..."

    # 清空 build 目录内容
    rm -rf *

    # 重新生成构建文件
    cmake ..

    # 构建项目
    make

    cd ..
    # 运行程序
    ./build/BoostAsioServer
else
    echo "❌ 无法进入 build 文件夹，停止操作。"
    exit 1
fi
