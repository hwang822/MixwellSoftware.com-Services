import os, sys
from flask import Flask, render_template

app = Flask(__name__)

serviceport = sys.argv[1]
servicedb = sys.argv[2]
app.config["SQLALCHEMY_DATABASE_URI"] = servicedb 

@app.route("/")
def home():    
    return render_template("ai.html")        
if __name__ == "__main__":
    print (f"start running {app.root_path} at {serviceport}")    
    app.run(port=serviceport)