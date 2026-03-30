from flask import Flask, Blueprint, render_template, jsonify
import sys
import teslapy

app = Flask(__name__)
sys.path.insert(0, f"{app.root_path}/../../")
from config.settings import Config

serviceport = int(app.root_path.rsplit("_")[1]) + 5000
serviceport = int(sys.argv[1]) if len(sys.argv) > 1 else serviceport 

teslaService = Blueprint("teslaService", __name__)

EMAIL = Config.SMTP_EMAIL_G

#tesla = teslapy.Tesla(EMAIL, cache_file='token.json')

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
    return render_template("tesla.html")

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

