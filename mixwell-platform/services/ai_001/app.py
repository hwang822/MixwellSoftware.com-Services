import os, sys
from flask import Blueprint, Flask, render_template

app = Flask(__name__)

serviceport = sys.argv[1]
servicedb = sys.argv[2]
app.config["SQLALCHEMY_DATABASE_URI"] = servicedb 

aiService = Blueprint("aiService", __name__) 
@aiService.route("/")
def home():    
    return render_template("ai.html")        

def create_app():
    app.register_blueprint(aiService)    
    return app

if __name__ == "__main__":
    print (f"start running {app.root_path} at {serviceport}")    
    create_app().run(host="127.0.0.1", port=serviceport)  
    # host="127.0.0.1" interal only