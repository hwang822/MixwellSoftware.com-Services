import os

from flask import Flask, Blueprint, render_template, jsonify
import sys
import teslapy

base_dir = os.path.dirname(os.path.abspath(__file__))
shared_templates = os.path.abspath(os.path.join(base_dir, "../../templates"))

app = Flask(__name__,template_folder=os.path.join(base_dir, "templates"))
app.jinja_loader.searchpath.append(shared_templates)

sys.path.insert(0, f"{base_dir}/../../")
from config.settings import Config

EMAIL = Config.SMTP_EMAIL_G

serviceport = int(base_dir.rsplit("_")[1]) + 5000
serviceport = int(sys.argv[1]) if len(sys.argv) > 1 else serviceport 

# =========================
# Service code start here
# =========================

teslaService = Blueprint("teslaService", __name__)


# =========================
# GET VEHICLE DATA
# =========================

def get_vehicle_data():
    import teslapy

    with teslapy.Tesla(EMAIL, cache_file='token.json') as tesla:

        vehicles = tesla.vehicle_list()

        if not vehicles:
            return {"error": "No vehicle"}

        vehicle = vehicles[0]

        # Wake up car (important)
        vehicle.sync_wake_up()

        data = vehicle.get_vehicle_data()

        return {
            "name": vehicle["display_name"],
            "battery": data["charge_state"]["battery_level"],
            "range": data["charge_state"]["battery_range"],            
            "charging": data["charge_state"]["charging_state"],
            "locked": data["vehicle_state"]["locked"],
            "inside_temp": data["climate_state"]["inside_temp"],
            "outside_temp": data["climate_state"]["outside_temp"],            

            #"Vehicle State": data["charge_state"]["locked"],
            #"Auto A/C": data["climate_state"]["is_auto_conditioning_on"],
            #"Heading": data["drive_state"]["heading"], 
            #"Charge Rate": data["gui_charge_rate_units"]["gui_charge_rate_units"],            
            #"Exterior Color": data["vehicle_config"]["exterior_color"],
            #"Vehicle Odometer": data["vehicle_state"]["odometer"],
            "status": data["state"]
        }
    

# =========================
# ROUTES
# =========================
@teslaService.route("/")
def home():
    return render_template("tesla.html", servicename = "Tesla Service")

@teslaService.route("/api/status")
def status():    
    return jsonify(get_vehicle_data())

@teslaService.route("/service/tesla/api/status")
def tesla_status():
    return status()

def create_app():
    app.register_blueprint(teslaService)
    return app

if __name__ == "__main__":
    print (f"start running {app.root_path} at {serviceport}")    
    create_app().run(host="127.0.0.1", port=serviceport)

