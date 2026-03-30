from flask import Flask, Blueprint, render_template, jsonify
import sys
import teslapy

app = Flask(__name__)
sys.path.insert(0, f"{app.root_path}/../../")
from config.settings import Config
# first generet auth json file 
# C:\Workarea\MixwellSoftware.com-Services\mixwell-platform\services\tesla_011>venv\Scripts\activate
# python tesla_login_auto.py
# run app.py will auto login

EMAIL = Config.SMTP_EMAIL_G

def login():
    with teslapy.Tesla(EMAIL, cache_file='token.json') as tesla:

        if not tesla.authorized:
            print("Opening browser for Tesla login...")
            tesla.fetch_token(interactive=True)   # ✅ KEY

        print("✅ Authorized:", tesla.authorized)

        vehicles = tesla.vehicle_list()
        print("🚗 Vehicles:", vehicles)


if __name__ == "__main__":
    login()