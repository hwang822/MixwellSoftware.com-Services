import sys
from flask import Flask, render_template

app = Flask(__name__)

serviceport = int(sys.argv[1])
servicedb = sys.argv[2]
app.config["SQLALCHEMY_DATABASE_URI"] = f"{servicedb}" 

@app.route("/")
def home():    
    return render_template("data.html")        
if __name__ == "__main__":
    app.run(port=serviceport)