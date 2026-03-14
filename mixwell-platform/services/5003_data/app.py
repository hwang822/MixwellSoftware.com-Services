import os, sys
from flask import Flask, redirect, render_template, request

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
sys.path.insert(0, BASE_DIR)
from config.settings import Config
from portal.models import db
app = Flask(__name__)

folder_name = os.path.basename(os.path.dirname(__file__))
servicePort, serviceName = folder_name.split("_", 1)
servicePort = int(servicePort)

app.config.from_object(Config)
app.config["SQLALCHEMY_DATABASE_URI"] = f"{app.config["SQLALCHEMY_DATABASE_URL"]}/{serviceName}db" 
db.init_app(app)

@app.route("/")
def home():    
    return render_template(f"{serviceName}.html")        
if __name__ == "__main__":
    #with app.app_context():        
        #db.create_all()    
    app.run(port=servicePort)