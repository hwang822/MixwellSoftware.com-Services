import os, sys
from flask import Flask, render_template

#BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
#sys.path.insert(0, BASE_DIR)
app = Flask(__name__)

serviceport = sys.argv[1]
servicedb = sys.argv[2]
app.config["SQLALCHEMY_DATABASE_URI"] = servicedb 
#db.init_app(app)


@app.route("/")
def home():    
    return render_template("ai.html")        
if __name__ == "__main__":
    app.run(port=serviceport)