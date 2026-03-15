import os, sys
from flask import Flask, render_template

#BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
#sys.path.insert(0, BASE_DIR)
app = Flask(__name__)

folder_name = os.path.basename(os.path.dirname(__file__))
servicePort, serviceName = folder_name.split("_", 1)
servicePort = int(servicePort)

@app.route("/")
def home():    
    return render_template(f"{serviceName}.html")        
if __name__ == "__main__":
    app.run(port=servicePort)