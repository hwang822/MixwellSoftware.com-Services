import sys
from flask import Blueprint, Flask, render_template

app = Flask(__name__)
serviceport = int(sys.argv[1])
servicedb = sys.argv[2]
app.config["SQLALCHEMY_DATABASE_URI"] = f"{servicedb}" 

rdpService = Blueprint("registryService", __name__)
@rdpService.route("/")
def home():    
    return render_template(f"rdp.html")        

def create_app():
    app.register_blueprint(rdpService)
    return app
if __name__ == "__main__":
    print (f"start running {app.root_path} at {serviceport}")    
    create_app().run(host="127.0.0.1", port=serviceport)