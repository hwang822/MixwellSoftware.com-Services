✅ 最终推荐项目结构（完全独立微服务）

你不要再用一个 mixwell 包了。
改成 4个完全独立项目：

mixwell-platform/

│
├── auth-server/
│        templates\
│            login.html
│            signup.html│
│        ├──app.py
│        ├──models.py
|        ├──__init__.py
|        ├──config.py
│
├── portal-server/
│
├── service1-server/
│
└── service2-server/

每个都是独立 Flask App

*****************************
cmd=> cd mixwell-platform
cmd=>python -m venv venv

one folder mixwell-platform\venv will be created.
cmd=> pip install flask sqlalchemy psycopg2-binary

vscode open folder auth-server.


another vscode open folder service1.

Verify model is installed in your venv

CMD => cd C:\Workarea\MixwellSoftware.com-Services\mixwell-platform
CMD => venv\Scripts\activate
CMD => pip install flask_login (at even)
  Collecting flask_login
    Obtaining dependency information for flask_login from https://files.pythonhosted.org/packages/59/f5/67e9cc5c2036f58115f9fe0f00d203cf6780c3ff8ae0e705e7a9d9e8ff9e/Flask_Login-0.6.3-py3-none-any.whl.metadata
    Downloading Flask_Login-0.6.3-py3-none-any.whl.metadata (5.8 kB)
CMD (venv) C:\Workarea\MixwellSoftware.com-Services\mixwell-platform>pip show flask_login
  Name: Flask-Login
  Version: 0.6.3
  Summary: User authentication and session management for Flask.

from flask_login import LoginManager, login_required, current_user, login_user, logout_user

########################################
1. install postgersql database

pip install psycopg2-binary

然后确认 auth-server\requirements.txt
Flask
Flask-SQLAlchemy
psycopg2-binary
PyJWT
requests
Werkzeug

第一步：检查 PostgreSQL 是否运行?
netstat -ano | findstr 5432

C:\Users\hwang>netstat -ano | findstr 5432
  TCP    127.0.0.1:65431        127.0.0.1:65432        ESTABLISHED     9612
  TCP    127.0.0.1:65432        127.0.0.1:65431        ESTABLISHED     9612

安装 PostgreSQL

下载：

👉 https://www.postgresql.org/download/windows/

安装时记住：

用户名（默认 postgres）

密码

端口（默认 5432）

🔍 第三步：确认数据库存在

进入：

psql -U postgres

然后：

最稳定方式（强烈推荐）

用 Docker 跑 PostgreSQL：

bash =>
docker run --name mixwell-postgres \
-e POSTGRES_PASSWORD=password \
-e POSTGRES_DB=authdb \
-p 5432:5432 \
-d postgres


确认数据库真的存在

你现在不能用 psql，因为 Git Bash 没有 PATH。

请在 Windows CMD 里运行：

"C:\Program Files\PostgreSQL\15\bin\psql.exe" -U postgres

（版本号可能是 14/16）

如果提示输入密码，输入你安装时设置的密码。

进去后执行：

\l

看有没有：

authdb

如果没有：

CREATE DATABASE authdb;

postgres=# CREATE DATABASE authdb;
CREATE DATABASE
postgres=# \l
                                                                    List of databases
   Name    |  Owner   | Encoding | Locale Provider |          Collate           |           Ctype            | Locale | ICU Rules |   Access privileges
-----------+----------+----------+-----------------+----------------------------+----------------------------+--------+-----------+-----------------------
 authdb    | postgres | UTF8     | libc            | English_United States.1252 | English_United States.1252 |        |           |
 postgres  | postgres | UTF8     | libc            | English_United States.1252 | English_United States.1252 |        |           |
 template0 | postgres | UTF8     | libc            | English_United States.1252 | English_United States.1252 |        |           | =c/postgres          +
           |          |          |                 |                            |                            |        |           | postgres=CTc/postgres
 template1 | postgres | UTF8     | libc            | English_United States.1252 | English_United States.1252 |        |           | =c/postgres          +
           |          |          |                 |                            |                            |        |           | postgres=CTc/postgres

download and install pgAdmin (Manager tool for PostgreSQL)

change password. pgAdmin 4\Servers(1)\PostgreSQL 18\Login/Group Roles\postgres->right click->properties...\Definition\Password -> typein new password ->Save

create new database ->   pgAdmin 4\Servers(1)\PostgreSQL 18\Databases (3) -> right clcik -> Create -> Database ...
delete a database  ->   pgAdmin 4\Servers(1)\PostgreSQL 18\Databases (3) -> right clcik -> Delete/Drop -> Database ...