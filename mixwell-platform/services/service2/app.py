import sys
from flask import Flask, render_template

from models import db
app = Flask(__name__)

serviceport = int(sys.argv[1])
servicedb = sys.argv[2]
app.config["SQLALCHEMY_DATABASE_URI"] = f"{servicedb}" 
db.init_app(app)

@app.route("/")
def home():    
    return render_template("service2.html")        
if __name__ == "__main__":
    with app.app_context():        
        db.create_all()    
    print (f"start running {app.route_path} at {serviceport}")    
    app.run(port=serviceport)
