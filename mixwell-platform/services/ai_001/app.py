import os, sys
from flask import Blueprint, Flask, render_template

base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
app = Flask(__name__,static_folder=os.path.join(base_dir, 'static'),static_url_path='/static')

shared_templates = os.path.abspath(os.path.join(base_dir, "templates"))
app.jinja_loader.searchpath.append(shared_templates)
print("Shared templates:", shared_templates)  
sys.path.insert(0, f"{base_dir}")

serviceport = int(app.root_path.rsplit("_")[1]) + 5000
serviceport = int(sys.argv[1]) if len(sys.argv) > 1 else serviceport 

camService = Blueprint("camService", __name__)
app.config["SQLALCHEMY_DATABASE_URI"] = f"cam_{serviceport}" 

aiService = Blueprint("aiService", __name__) 
@aiService.route("/")
def home():    
    return render_template("ai.html", servicename = "Ai Service")        

def create_app():
    app.register_blueprint(aiService)    
    return app

if __name__ == "__main__":
    print (f"start running {app.root_path} at {serviceport}")    
    create_app().run(host="127.0.0.1", port=serviceport)  
    # host="127.0.0.1" interal only