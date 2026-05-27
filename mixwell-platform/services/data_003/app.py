import os, sys, cv2
from flask import Blueprint, Flask, render_template
base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
sys.path.insert(0, f"{base_dir}")
from config.settings import Config
from models import db

app = Flask(__name__,static_folder=os.path.join(base_dir, 'static'),static_url_path='/static')
shared_templates = os.path.abspath(os.path.join(base_dir, "templates"))
app.jinja_loader.searchpath.append(shared_templates)
print("Shared templates:", shared_templates)  
sys.path.insert(0, f"{base_dir}")

baseport = int(Config.PORTAL_PORT)
baseport = int(sys.argv[1]) if len(sys.argv) > 1 else baseport
serviceport = int(app.root_path.rsplit("_")[1]) + baseport
app.config["SQLALCHEMY_DATABASE_URI"] = f"cam_{serviceport}" 
#db.init_app(app)
 
count = 0

dataService = Blueprint("dataService", __name__)
@dataService.route("/")
def home():    
    return render_template("data.html", count = count, servicename = "Data Service")        

@dataService.route("/count_plus_one")
def count_plus_one():       
    global count
    count += 1
    print(count)
    return render_template("data.html", count = count)        

@dataService.route("/service/data/count_plus_one")
def service_data_count_plus_one():       
    return count_plus_one()

def smartmeetAPI():    
    http = "https://services.smartmetertexas.net/v2/token/" 
    try:
        response = requests.get(http).json()
    except Exception as e:
        print (e)
    print (response)

def create_app():
    app.register_blueprint(dataService)    
    return app

if __name__ == "__main__":
    print (f"start running {app.root_path} at {serviceport}")    
    create_app().run(host=Config.SERVICE_BIND_HOST_INTERNAL, port=serviceport)    

