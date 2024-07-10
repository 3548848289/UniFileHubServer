cmake_minimum_required(VERSION 3.10)

# 项目名称
project(BoostAsioServer)

# 设置C++标准
set(CMAKE_CXX_STANDARD 11)
set(CMAKE_CXX_STANDARD_REQUIRED True)

# 包含头文件目录
include_directories(${PROJECT_SOURCE_DIR}/include)

# 查找Boost库（确保已安装）
find_package(Boost 1.66 REQUIRED COMPONENTS system)

# 源文件列表
set(SOURCES
    ${PROJECT_SOURCE_DIR}/src/main.cpp
    ${PROJECT_SOURCE_DIR}/src/server.cpp
    ${PROJECT_SOURCE_DIR}/src/client_handler.cpp
    ${PROJECT_SOURCE_DIR}/src/MessageHandler.cpp
)

# 添加可执行文件
add_executable(${PROJECT_NAME} ${SOURCES})

# 链接Boost库
target_link_libraries(${PROJECT_NAME} Boost::system)
