import os, sys
from flask import Blueprint, Flask, jsonify, render_template
base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
sys.path.insert(0, f"{base_dir}")
from config.settings import Config
from models import db

app = Flask(__name__,static_folder=os.path.join(base_dir, 'static'),static_url_path='/static')
shared_templates = os.path.abspath(os.path.join(base_dir, "templates"))
app.jinja_loader.searchpath.append(shared_templates)
print("Shared templates:", shared_templates)  
sys.path.insert(0, f"{base_dir}")

baseport = int(Config.PORTAL_PORT)
baseport = int(sys.argv[1]) if len(sys.argv) > 1 else baseport
serviceport = int(app.root_path.rsplit("_")[1]) + baseport

app.config["SQLALCHEMY_DATABASE_URI"] = f"tesla_{serviceport}" 
#db.init_app(app)

# =========================
# Service code start here
# =========================

teslaService = Blueprint("teslaService", __name__)

# =========================
# GET VEHICLE DATA
# =========================
def get_vehicle_data():
    import teslapy

    print("Starting Tesla API call...")

    import teslapy

    tesla = teslapy.Tesla(Config.SMTP_EMAIL_G, cache_file='token.json')

    if not tesla.authorized:
        url = tesla.authorization_url()
        print("\n1. Open this URL in Google Chrome browser:\n", url)  # lgoin with tesla account and get callback url as 'https://auth.tesla.com/void/callback?code=NA_oac...'

        redirect_response = input("Paste FULL callback URL here:\n")

        tesla.fetch_token(authorization_response=redirect_response)  # teslay will get token and save to toekn.json for next access check tesla.authorized?

    vehicles = tesla.vehicle_list()

    print("Vehicles fetched:", vehicles)

    if not vehicles:
        return {"error": "No vehicle"}

    vehicle = vehicles[0]

    print("Waking vehicle...")
    vehicle.sync_wake_up()

    data = vehicle.get_vehicle_data()
    print("Vehicle data received")

    return {
        "battery": data["charge_state"]["battery_level"],
        "range": data["charge_state"]["battery_range"],
        "charging": data["charge_state"]["charging_state"],
        "locked": data["vehicle_state"]["locked"],
        "inside_temp": data["climate_state"]["inside_temp"],
        "outside_temp": data["climate_state"]["outside_temp"],
        "status": data["state"]
    }


def get_vehicle_data1():
    import teslapy

    with teslapy.Tesla(Config.SMTP_EMAIL_G, cache_file='token.json') as tesla:

        vehicles = tesla.vehicle_list()

        if not vehicles:
            return {"error": "No vehicle"}

        vehicle = vehicles[0]

        # Wake up car (important)
        vehicle.sync_wake_up()

        data = vehicle.get_vehicle_data()

        return {
            #"name": data["display_name"],
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

# API endpoint to return JSON
@teslaService.route("/get-data")
def get_data():    
    return jsonify(get_vehicle_data())

@teslaService.route("/service/tesla/get-data")
def get_data_api():    
    return jsonify(get_vehicle_data())

def create_app():
    app.register_blueprint(teslaService)
    return app

if __name__ == "__main__":
    print (f"start running {app.root_path} at {serviceport}")    
    create_app().run(host="127.0.0.1", port=serviceport)

