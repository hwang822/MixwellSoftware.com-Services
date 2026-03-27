import sys
from flask import Blueprint, Flask, render_template

app = Flask(__name__)

sys.path.insert(0, f"{app.root_path}/../../")
from models import Utility

serviceport = int(app.root_path.rsplit("_")[1]) + 5000
serviceport = int(sys.argv[1]) if len(sys.argv) > 1 else serviceport 

#servicedb = sys.argv[2]
#app.config["SQLALCHEMY_DATABASE_URI"] = f"{servicedb}" 
count = 0

dataService = Blueprint("dataService", __name__)
@dataService.route("/")
def home():    
    return render_template("data.html", count = count)        

@dataService.route("/count_plus_one")
def count_plus_one():       
    global count
    count += 1
    print(count)
    return render_template("data.html", count = count)        

@dataService.route("/service/data/count_plus_one")
def service_data_count_plus_one():       
    return count_plus_one()

def create_app():
    app.register_blueprint(dataService)
    return app

if __name__ == "__main__":
    print (f"start running {app.root_path} at {serviceport}")    
    create_app().run(host="127.0.0.1", port=serviceport)    

