#!/bin/bash
pkill -f appFIleHistory
pkill -f appSharedFile
pkill -f appUserInfo
pkill -f run.sh
pkill -f BoostAsioServer
echo "所有服务已停止"
