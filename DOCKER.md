# Docker

This project now uses one root-level Docker image that starts:

- built-in MySQL-compatible database service
- `SharedFile` on `5000`
- `UserInfo` on `5001`
- `FIleHistory` on `5002`
- `PersonalDrive` on `5005`

## Build

Run this from the repository root:

```powershell
docker build -t unifileserver/all-in-one .
```

## Run

```powershell
docker run -d --name unifileserver-all ^
  -p 3306:3306 -p 5000:5000 -p 5001:5001 -p 5002:5002 -p 5005:5005 ^
  -v unifileserver-mysql:/var/lib/mysql ^
  -e MYSQL_ROOT_PASSWORD=Mysql20039248 ^
  -e MYSQL_DATABASE=SmartDesk ^
  -e MYSQL_APP_USER=smartdesk ^
  -e MYSQL_APP_PASSWORD=smartdesk ^
  unifileserver/all-in-one
```

## Export image

```powershell
docker save -o unifileserver-all.tar unifileserver/all-in-one
```

## Notes

- Docker startup is handled by [myServer/docker_start_all.sh](D:\Python_list\Pypro_flask\UniFileServerServer\myServer\docker_start_all.sh).
- Python dependencies are installed directly in [Dockerfile](D:\Python_list\Pypro_flask\UniFileServerServer\Dockerfile), not from a requirements file.
- The container keeps database files in `/var/lib/mysql`; use a volume if you want persistence.
- The bundled database comes from Ubuntu's MariaDB packages and is MySQL protocol compatible.
