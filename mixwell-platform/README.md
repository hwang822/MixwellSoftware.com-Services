Python/Flask Concept 

######################################
services share model or function.
at BASE_PATH = "mixwell-platform"

BASE_PATH/.env
         /core
            /settings.py
            /serviceSetup.py

CMD => cd BASE_PATH

BASE_PATH/.env
  PORTAL_PORT = "5000"
  AUTH_PORT = "5003"
  AUTH_URL = "http://localhost"

BASE_PATH/core/settings.py
  import os
  from dotenv import load_dotenv
  # Load .env from project root
  load_dotenv()
  class Config:
      PORTAL_PORT = os.getenv("PORTAL_PORT")
      AUTH_PORT = os.getenv("AUTH_PORT")
      AUTH_URL = os.getenv("AUTH_URL")

BASE_PATH/core/serviceSetup.py





####################################

FLASK request data from A to B.
Service A → send one string (route path) or one integer (user_id) + status
Service B → receive it
#####################################

METHOD 1 — Send as JSON (Most Common & Cleanest)

🔹 Service A (Sender)
import requests

data = {
    "user_id": 123,
    "status": "active"
}

r = requests.post(
    "http://localhost:5001/receive",
    json=data   # automatically sets Content-Type: application/json
)

print(r.status_code)

🔹 Service B (Receiver)

from flask import request

@app.route("/receive", methods=["POST"])
def receive():
    data = request.get_json()

    user_id = data.get("user_id")
    status = data.get("status")

    print("User ID:", user_id)
    print("Status:", status)

    return {"message": "received"}, 200


METHOD 2 — Send Only ONE Simple Value

🔹 Service A (Sender)

requests.post(
    "http://localhost:5001/receive",
    json={"user_id": 123}
)

🔹 Service B (Receive)

data = request.get_json()
user_id = data["user_id"]


##############################
Get request from paort service to auth service
service.py
    services = requests.get(f"{auth_path}/service/all").json()    
    return render_template("portal.html", services=services)
auth.py
@app.route("/service/all", methods=["GET"])
def service_all():
    return Utility.services_all()

Utility.py
def services_all():
    services = Service.query.all()
    servicesJson = jsonify([s.to_dict() for s in services])
    return servicesJson

#############################







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

control-shift-p => Python Select interpreter => C:\Workarea\MixwellSoftware.com-Services\mixwell-platform\venv\Scripts\python.exe
wil using same python under mixwell-platform

C:\Users\hwang>dir C:\Workarea\MixwellSoftware.com-Services\mixwell-platform\venv\Scripts
 Volume in drive C is Windows-SSD
 Volume Serial Number is EC27-33FA

 Directory of C:\Workarea\MixwellSoftware.com-Services\mixwell-platform\venv\Scripts

02/27/2026  02:34 PM    <DIR>          .
02/27/2026  02:30 PM    <DIR>          ..
02/27/2026  02:30 PM             2,406 activate
02/27/2026  02:30 PM             1,031 activate.bat
02/27/2026  02:30 PM            26,199 Activate.ps1
02/27/2026  02:30 PM               393 deactivate.bat
02/27/2026  02:34 PM           108,427 flask.exe
02/27/2026  02:30 PM           108,440 pip.exe
02/27/2026  02:30 PM           108,440 pip3.12.exe
02/27/2026  02:30 PM           108,440 pip3.exe
02/27/2026  02:30 PM           270,616 python.exe
02/27/2026  02:30 PM           259,352 pythonw.exe
              10 File(s)        993,744 bytes
               2 Dir(s)  65,075,929,088 bytes free



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