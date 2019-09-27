import requests
from requests import HTTPError
import time
from datetime import datetime

"""
notes on what I've done:

* formatted with black
    This makes it more standard and readable

* put stuff in a main method.
    This allows for it to be more easily used as a module, more easily tested,
    and more easily turned into a cmdline utility.

* fruitlessly look for better ways to parse ISO 8601 dates without 3rd party libs

* added the sorting of kills (and some notes around it)

* suggestions for further improvements
    * pass in the ship id to the get_zkill_data() method instead of looping
    * pass in the number of seconds requested to get_zkill_data() - DONE
    * fetch esi information right when you get the zkill info
    * hard-cap the amount of time you sleep between zkill requests - DONE
    * send errors to stderr instead of stdout
    * add timeouts to the request calls - DONE
    * extra bonus points: spin up another worker thread pool, feed info to it
      via a queue, and get some concurrency to speed up requests

* I added a new method to get names in bulk from the ESI. This should really
  speed up the total time of the script.
"""

# AT Ships, to add additional ships onto the feed. Add the ship_id, found on zkillboard. To the below list.
spec_edition_ships = [
    2836,
    42246,
    32788,
    33675,
    33397,
    32790,
    35781,
    32207,
    35779,
    3516,
    32209,
    33395,
    2834,
    3518,
    33673,
    # Faction Caps
    3514,
    45649,
    42241,
    42126,
    45645,
    42242,
    42133,
    45647,
    42243,
    42124,
    42132
]


def lookup_ids(ids):
    url = "https://esi.evetech.net/latest/universe/names/"
    id_list = list(set(ids))
    try:
        r = requests.post(url, json=id_list, timeout=5.0)
    except requests.ConnectionError:
        pass
    if r.status_code == 200:
        data = r.json()
        ret = {}
        for entry in data:
            ret[entry["id"]] = entry
        return ret


# Make request to zkillboard to get killmails, from the last 7 days, for each AT ship
def get_zkill_data(ship, pastSeconds):
    full_data = []
    req_delay = 0.25
    try:
        base_url = "https://zkillboard.com/api/"
        url = f"{base_url}kills/shipTypeID/{ship}/pastSeconds/{pastSeconds}/"
        response = requests.get(url, timeout=5.0)
        response.raise_for_status()
    except HTTPError as http_err:
        print(f"HTTP Error has occurred: {http_err}")
    except Exception as err:
        print(f"Error has occurred: {err}")
    except TimeoutError as timeout:
        print(f"Timeout error has occurred: {timeout}")
    else:
        data = response.json()
        if req_delay <= 1.75:
            req_delay += 0.25
        time.sleep(req_delay)
        return data


# Get detailed info from ESI about a killmail
def get_esi_killmail(kill_hash=None, kill_id=None):
    if not hash:
        print("Error: No killmail hash provided.")
        return
    try:
        url = f"https://esi.evetech.net/latest/killmails/{kill_id}/{kill_hash}/?datasource=tranquility"
        response = requests.get(url, timeout=5.0)
        response.raise_for_status()
    except HTTPError as http_err:
        print(f"HTTP Error has occurred: {http_err}")
    except Exception as err:
        print(f"Error has occurred: {err}")
    except TimeoutError as timeout:
        print(f"Timeout error has occurred: {timeout}")
    else:
        data = response.json()
        return data


# Get detailed info from ESI, about a system, using the system_id retrieved from zkillboard killmail
def get_system_name(system_id):
    if not system_id:
        print("Error: No killmail hash provided.")
        return
    try:
        url = f"https://esi.evetech.net/latest/universe/systems/{system_id}/?datasource=tranquility&language=en-us"
        response = requests.get(url, timeout=5.0)
        response.raise_for_status()
    except HTTPError as http_err:
        print(f"HTTP Error has occurred: {http_err}")
    except Exception as err:
        print(f"Error has occurred: {err}")
    except TimeoutError as timeout:
        print(f"Timeout error has occurred: {timeout}")
    else:
        data = response.json()
        return data


# Get detailed info from ESI, about a pilot, using the character_id retrieved from zkillboard killmail
def get_pilot_name(char_id):
    if not char_id:
        print("Error: No character id provided.")
        return
    try:
        url = f"https://esi.evetech.net/latest/characters/{char_id}/?datasource=tranquility"
        response = requests.get(url, timeout=0.5)
        response.raise_for_status()
    except HTTPError as http_err:
        print(f"HTTP Error has occurred: {http_err}")
    except Exception as err:
        print(f"Error has occurred: {err}")
    except TimeoutError as timeout:
        print(f"Timeout error has occurred: {timeout}")
    else:
        data = response.json()
        return data


# Get detailed info from ESI, about a ship, using the ship_id retrieved from zkillboard killmail
def get_ship_data(ship_id):
    if not ship_id:
        print("Error: No killmail hash provided.")
        return
    try:
        url = f"https://esi.evetech.net/latest/universe/types/{ship_id}/?datasource=tranquility&language=en-us"
        response = requests.get(url, timeout=5.0)
        response.raise_for_status()
    except HTTPError as http_err:
        print(f"HTTP Error has occurred: {http_err}")
    except Exception as err:
        print(f"Error has occurred: {err}")
    except TimeoutError as timeout:
        print(f"Timeout error has occurred: {timeout}")
    else:
        data = response.json()
        return data


def main():
    zkill_data = []
    for ship in spec_edition_ships:
        data = get_zkill_data(ship, 604800)
        if data:
            zkill_data.extend(data)

    # just to make things faster, let's build a set of stuff to look up
    ids_to_look_up = set()

    # sorting notes
    # in order to sort by date, we need to do the ESI fetch first
    for kill in zkill_data:
        kill_id = kill["killmail_id"]
        kill_hash = kill["zkb"]["hash"]
        esi_data = get_esi_killmail(kill_hash, kill_id)

        # Now what I'm doing here is taking advantage of how mutable types
        # work in Python. Since zkill_data is a list of dictionaries, and
        # dicts are mutable types, that means they are stored by reference,
        # not by instance. That means we can update the local reference
        # (ie the kill variable) and the dictionary in zkill_data is
        # updated too.
        kill["esi_data"] = esi_data  # store it for later

        # store the ids of stuff we want to eventually look up so we can
        # do it all at once
        ids_to_look_up.add(esi_data["solar_system_id"])
        for x in esi_data["attackers"]:
            if "ship_type_id" in x:
                ids_to_look_up.add(x["ship_type_id"])
            if "character_id" in x:
                ids_to_look_up.add(x["character_id"])

    # Now that we've got all the data in a single place, we can sort. There
    # are many different ways to do this, but I'll just do a basic sort on
    # timestamp.
    zkill_data.sort(key=lambda k: k["esi_data"]["killmail_time"])

    # now lookup all the ids all at once
    id_map = lookup_ids(ids_to_look_up)

    for kill in zkill_data:
        kill_id = kill["killmail_id"]
        kill_hash = kill["zkb"]["hash"]
        link = f"https://zkillboard.com/kill/{kill_id}"
        esi_data = kill["esi_data"]  # what we saved above
        location_id = esi_data["solar_system_id"]
        # Set default variables
        system_name = "NA"
        pilot = "NA"
        ship = "NA"
        format_date = "NA"
        system_name = id_map[location_id]["name"]

        if esi_data:
            timestamp = esi_data["killmail_time"]
            # note: this format is ISO8601,
            # but python's standard library doesn't parse it
            format_date = datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%SZ")
            ship_id = None
            try:
                for x in esi_data["attackers"]:
                    if x["ship_type_id"]:
                        ship_id = x["ship_type_id"]

                    if ship_id in spec_edition_ships:
                        ship = id_map[ship_id]["name"]
                        char_id = x["character_id"]
                        pilot = id_map[char_id]["name"]
            except (TypeError, KeyError) as err:
                print(err)
                continue

        print(
            f"""------------------------------------------------------
        AT Killmail loaded:
        Ship: {ship}
        Pilot: {pilot}
        System Name: {system_name}
        Date: {format_date}
        {link}"""
        )


if __name__ == "__main__":
    main()