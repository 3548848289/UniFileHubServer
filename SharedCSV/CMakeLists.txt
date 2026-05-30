# cmake_minimum_required(VERSION 3.10)

# 项目名称
# project(BoostAsioServer)

# 设置C++标准
# set(CMAKE_CXX_STANDARD 17)
# set(CMAKE_CXX_STANDARD_REQUIRED True)

# 包含头文件目录
# include_directories(${PROJECT_SOURCE_DIR}/include)

# 查找Boost库（确保已安装）
# find_package(Boost 1.66 REQUIRED COMPONENTS system)

# 查找jsoncpp库
# find_package(jsoncpp REQUIRED)

# 源文件列表
# set(SOURCES
#     ${PROJECT_SOURCE_DIR}/src/main.cpp
#     ${PROJECT_SOURCE_DIR}/src/server.cpp
#     ${PROJECT_SOURCE_DIR}/src/client_handler.cpp
#     ${PROJECT_SOURCE_DIR}/src/message_handler.cpp
#     ${PROJECT_SOURCE_DIR}/src/json_handler.cpp
# )

# 添加可执行文件
# add_executable(${PROJECT_NAME} ${SOURCES})

# 链接Boost库和jsoncpp库
# target_link_libraries(${PROJECT_NAME} Boost::system jsoncpp_lib)

if (MSVC)
    # /utf-8: 使用 UTF-8 编码编译源文件
    add_compile_options(/utf-8)
    add_definitions(-D_WIN32_WINNT=0x0601)  # Windows 7+ API

endif()


cmake_minimum_required(VERSION 3.10)
project(BoostAsioServer)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED True)

# 指定 Boost 路径
set(BOOST_ROOT "D:/CxxProgram/Library/Boost")
find_package(Boost 1.66 REQUIRED COMPONENTS system)
include_directories(${Boost_INCLUDE_DIRS})
link_directories(${Boost_LIBRARY_DIRS})

# 指定 jsoncpp 路径
set(JSONCPP_INCLUDE_DIR "D:/CxxProgram/Library/jsoncpp-master/include")
set(JSONCPP_LIBRARY "D:/CxxProgram/Library/jsoncpp-master/build/lib/Release/jsoncpp.lib")
include_directories(${JSONCPP_INCLUDE_DIR})

include_directories(
    ${PROJECT_SOURCE_DIR}/include
)
set(SOURCES
    ${PROJECT_SOURCE_DIR}/src/main.cpp
    ${PROJECT_SOURCE_DIR}/src/server.cpp
    ${PROJECT_SOURCE_DIR}/src/client_handler.cpp
    ${PROJECT_SOURCE_DIR}/src/message_handler.cpp
    ${PROJECT_SOURCE_DIR}/src/json_handler.cpp
)

add_executable(${PROJECT_NAME} ${SOURCES})
target_link_libraries(${PROJECT_NAME} ${Boost_SYSTEM_LIBRARY} ${JSONCPP_LIBRARY})
