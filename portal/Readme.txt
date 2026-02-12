app.py all services enter point from route url\subs+port

python app.py

def load_user(user_id):
def create_admin():

@app.route("/")
def home():
@app.route("/login", methods=["GET","POST"])
def login():
@app.route("/signup", methods=["GET","POST"])
def signup():

@app.route("/service")
@login_required
def service_page():

@app.route("/dashboard")
@login_required
def dashboard():

@app.route("/service/admin")
@login_required
def admin_service():

@app.route("/service/<name>")
@login_required
def service(name):

@app.route("/logout")
def logout():

@app.route("/admin/approve/<int:user_id>")
@login_required
def approve_user(user_id):

@app.route("/admin/delete/<int:user_id>")
@login_required
def delete_user(user_id):

if __name__ == "__main__":

app.py listen 5000 port for ouside request and point to route function

localhost:5000
wsgi starting up on http://127.0.0.1:5000

each plugin app has templates folder of .html files
render_template -> xxxx.html
render_template("home.html")


Production-Ready Plugin Loader
Services/
    LoginService/
        __init__.py
        routes.py
    AISummaryService/
        __init__.py
        routes.py


project/
│
├ app.py                    # Main portal
├ requirements.txt
├ services/
│   ├ AIService/
│   │   ├ __init__.py
│   │   └ aiService.py
│   ├ CamService/
│   │   ├ __init__.py
│   │   └ camService.py
│   └ VideoService/
│       ├ __init__.py
│       └ videoService.py
└ templates/
    ├ login.html
    └ dashboard.html
    