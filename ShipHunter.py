import requests
from requests import HTTPError
import time
spec_edition_ships = [2836, 42246, 32788, 33675, 33397, 32790, 35781, 32207, 35779, 3516, 32209, 33395, 2834, 3518, 33673]

def get_system_name(system_id):
    if not system_id:
        print("Error: No killmail hash provided.")
        return
    try:
        url = f"https://esi.evetech.net/latest/universe/systems/{system_id}/?datasource=tranquility&language=en-us"
        response = requests.get(url)
        response.raise_for_status()
    except HTTPError as http_err:
        print(f"HTTP Error has occurred: {http_err}")
    except Exception as err:
        print(f"Error has occurred: {err}")
    else:
        data = response.json()
        return data

def get_ship_data(ship_id):
    if not ship_id:
        print("Error: No killmail hash provided.")
        return
    try:
        url = f"https://esi.evetech.net/latest/universe/types/{ship_id}/?datasource=tranquility&language=en-us"
        response = requests.get(url)
        response.raise_for_status()
    except HTTPError as http_err:
        print(f"HTTP Error has occurred: {http_err}")
    except Exception as err:
        print(f"Error has occurred: {err}")
    else:
        data = response.json()
        return data

# Make request to zkillboard to get killmails, from the last 7 days, for each AT ship
def get_zkill_data():
    full_data = []
    req_delay = 0.25
    for ship in spec_edition_ships:
        try:
            base_url = "https://zkillboard.com/api/"
            url = f"{base_url}kills/shipTypeID/{ship}/pastSeconds/604800/"
            response = requests.get(url)
            response.raise_for_status()
        except HTTPError as http_err:
            print(f"HTTP Error has occurred: {http_err}")
        except Exception as err:
            print(f"Error has occurred: {err}")
        else:
            data = response.json()
            if data:
                full_data.extend(data)
            req_delay +=0.25
            time.sleep(req_delay)
    return full_data

# Get detailed info from ESI about a killmail
def get_esi_killmail(kill_hash=None, kill_id=None):
    if not hash:
        print("Error: No killmail hash provided.")
        return
    try:
        url = f"https://esi.evetech.net/latest/killmails/{kill_id}/{kill_hash}/?datasource=tranquility"
        response = requests.get(url)
        response.raise_for_status()
    except HTTPError as http_err:
        print(f"HTTP Error has occurred: {http_err}")
    except Exception as err:
        print(f"Error has occurred: {err}")
    else:
        data = response.json()
        return data

zkill_data = get_zkill_data()

for kill in zkill_data:
    kill_id = kill['killmail_id']
    kill_hash = kill["zkb"]["hash"]
    link = f"https://zkillboard.com/kill/{kill_id}"
    # Invoke HTTP Request functions.
    esi_data = get_esi_killmail(kill_hash, kill_id)
    location_id = esi_data["solar_system_id"]
    sys_data = get_system_name(location_id)
    #ship_data = get_ship_data()
    # Set default variables
    system_name = "NA"
    pilot = "NA"
    ship = "NA"
    format_date = "NA"
    if sys_data:
        system_name = sys_data["name"]

    if esi_data:
        date = esi_data["killmail_time"]
        format_date = date.translate({ord(i): None for i in "TZ"})
        ship_id = None
        for x in esi_data["attackers"]:
            if x["ship_type_id"]:
                ship_id = x["ship_type_id"]
            if ship_id in spec_edition_ships:
                ship_data = get_ship_data(ship_id)
                ship = ship_data["name"]

    print(f"""------------------------------------------------------
    AT Killmail loaded:
    Ship: {ship}
    Pilot: {pilot}
    System Name: {system_name}
    Date: {format_date}
    {link}""")




