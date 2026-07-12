# UniFileHub Server

> UniFileHub 后端服务，提供用户系统、个人网盘、文件共享、文件历史、剪贴板同步以及前端静态资源代理能力。

---

## 项目简介

UniFileHub Server 是 UniFileHub 的后端服务仓库，用于提供云端 API、数据存储和 Web 静态资源服务。

本仓库采用多服务组合方式运行，包含用户认证、个人网盘、文件共享、文件历史、剪贴板同步、Nginx 静态资源服务以及 MariaDB / MySQL 数据库。Docker 镜像会将这些服务打包到一个容器中，方便在服务器或离线环境中快速部署。

---

## 后端服务组成

| 模块 | 默认端口 | 说明 |
| --- | --- | --- |
| Nginx / Web | 80 | 前端静态资源服务与 API 反向代理 |
| SharedFile | 5000 | 文件共享与上传服务 |
| UserInfo | 5001 | 用户注册、登录、头像与用户信息服务 |
| FIleHistory | 5002 | 文件历史与备份记录服务 |
| PersonalDrive | 5005 | 个人网盘、文件上传下载、目录与文件管理服务 |
| ClipboardSync | 5006 | 剪贴板历史与云端同步服务 |
| MariaDB / MySQL | 3306 | 后端数据库，兼容 MySQL 协议 |

Docker 容器启动时会自动初始化数据库、创建必要的数据表，并启动所有后端服务。

---

## 目录说明

```text
UniFileHub-Server/
├── ClipboardSync/        # 剪贴板同步服务
├── FIleHistory/          # 文件历史服务
├── myServer/             # 启动、停止与 Docker 容器入口脚本
├── nginx/                # Nginx 配置
├── PersonalDrive/        # 个人网盘服务
├── SharedFile/           # 文件共享服务
├── UserInfo/             # 用户系统服务
├── web/                  # Web 静态资源
├── Dockerfile            # Docker 镜像构建文件
└── README.md             # 项目说明
```

---

## 脚本用法

### Docker 容器启动脚本

容器启动后会自动执行：

```bash
/app/myServer/docker_start_all.sh
```

该脚本会完成以下操作：

- 初始化 MariaDB 数据目录
- 创建默认数据库和应用用户
- 初始化 UserInfo、PersonalDrive、ClipboardSync 数据表
- 启动 Nginx
- 启动 SharedFile、UserInfo、FIleHistory、PersonalDrive、ClipboardSync 服务

### Ubuntu 本地启动

在仓库根目录执行：

```bash
chmod +x ./myServer/ubuntu_start_all.sh ./myServer/ubuntu_stop_all.sh
./myServer/ubuntu_start_all.sh
```

停止服务：

```bash
./myServer/ubuntu_stop_all.sh
```

日志目录：

```bash
./myServer/logs
```

PID 目录：

```bash
./myServer/pids
```

### Windows 本地启动

在仓库根目录执行：

```bat
myServer\win_start_all.bat
```

静默启动：

```bat
myServer\win_start_all_silent.bat
```

停止服务：

```bat
myServer\win_stop_all_silent.bat
```

---

## Docker 镜像打包

### 构建镜像

在仓库根目录执行：

```bash
docker build -t unifilehubserver:v2.0 .
```

### 导出离线镜像包

```bash
docker save unifilehubserver:v2.0 | gzip > UniFileHubServer.tar.gz
```

### 导入离线镜像包

在目标服务器执行：

```bash
docker load -i UniFileHubServer.tar.gz
```

查看镜像是否导入成功：

```bash
docker images
```

---

## Docker 部署

### 直接运行

修正后的 Docker 运行命令如下：

```bash
sudo docker run -d \
  --name unifilehub \
  -p 80:80 \
  -p 8080:80 \
  -p 3306:3306 \
  -p 5000:5000 \
  -p 5001:5001 \
  -p 5002:5002 \
  -p 5005:5005 \
  -p 5006:5006 \
  -v unifilehub_mysql:/var/lib/mysql \
  unifilehubserver:v2.0
```

端口说明：

| 映射 | 说明 |
| --- | --- |
| `80:80` | 通过服务器 80 端口访问 Web 服务 |
| `8080:80` | 通过服务器 8080 端口访问同一个 Web 服务，可按需删除 |
| `3306:3306` | MariaDB / MySQL 数据库端口 |
| `5000:5000` | SharedFile 服务端口 |
| `5001:5001` | UserInfo 服务端口 |
| `5002:5002` | FIleHistory 服务端口 |
| `5005:5005` | PersonalDrive 服务端口 |
| `5006:5006` | ClipboardSync 服务端口 |

数据卷说明：

| 数据卷 | 容器路径 | 说明 |
| --- | --- | --- |
| `unifilehub_mysql` | `/var/lib/mysql` | 持久化数据库数据 |

### 使用环境变量运行

如需自定义数据库账号、数据库名称和密钥，可以使用：

```bash
sudo docker run -d \
  --name unifilehub \
  -p 80:80 \
  -p 8080:80 \
  -p 3306:3306 \
  -p 5000:5000 \
  -p 5001:5001 \
  -p 5002:5002 \
  -p 5005:5005 \
  -p 5006:5006 \
  -v unifilehub_mysql:/var/lib/mysql \
  -e MYSQL_ROOT_PASSWORD=Mysql20039248 \
  -e MYSQL_DATABASE=SmartDesk \
  -e MYSQL_APP_USER=smartdesk \
  -e MYSQL_APP_PASSWORD=smartdesk \
  -e SECRET_KEY=change-me \
  -e JWT_SECRET_KEY=change-me-too \
  unifilehubserver:v2.0
```

---

## 常用维护命令

### 查看容器状态

```bash
sudo docker ps
```

### 查看日志

```bash
sudo docker logs -f unifilehub
```

### 停止服务

```bash
sudo docker stop unifilehub
```

### 启动已有容器

```bash
sudo docker start unifilehub
```

### 删除容器

```bash
sudo docker rm unifilehub
```

### 重新部署

```bash
sudo docker stop unifilehub
sudo docker rm unifilehub
sudo docker run -d \
  --name unifilehub \
  -p 80:80 \
  -p 8080:80 \
  -p 3306:3306 \
  -p 5000:5000 \
  -p 5001:5001 \
  -p 5002:5002 \
  -p 5005:5005 \
  -p 5006:5006 \
  -v unifilehub_mysql:/var/lib/mysql \
  unifilehubserver:v2.0
```

---

## 默认环境变量

Docker 启动脚本支持以下环境变量：

| 变量 | 默认值 | 说明 |
| --- | --- | --- |
| `MYSQL_ROOT_PASSWORD` | `Mysql20039248` | 数据库 root 密码 |
| `MYSQL_DATABASE` | `SmartDesk` | 默认数据库名 |
| `MYSQL_APP_USER` | `smartdesk` | 应用数据库用户 |
| `MYSQL_APP_PASSWORD` | `smartdesk` | 应用数据库密码 |
| `DATABASE_URL` | 自动生成 | 后端数据库连接地址 |
| `SECRET_KEY` | `dev-secret` | Flask 应用密钥 |
| `JWT_SECRET_KEY` | `jwt-secret-key` | JWT 签名密钥 |
| `SHAREDCSV_RESOURCE_DIR` | `/app/SharedCSV/resources` | SharedCSV 资源目录 |
| `STORAGE_ROOT` | `/app/PersonalDrive/app/storage` | 个人网盘文件存储目录 |

生产环境建议修改 `MYSQL_ROOT_PASSWORD`、`MYSQL_APP_PASSWORD`、`SECRET_KEY` 和 `JWT_SECRET_KEY`。

---

## 访问地址

部署完成后，可以通过以下地址访问：

```text
http://服务器IP/
http://服务器IP:8080/
```

如果只需要一个 Web 访问端口，可以删除 `-p 8080:80`。

---

## 反馈与支持

如果您遇到问题或有功能建议，欢迎提交 Issue 或 Pull Request。

---

© 2026 UniFileHub Team
