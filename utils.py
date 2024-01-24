import os
import re
import requests
import json
from datetime import date
from progressbar import ProgressBar
from requests import exceptions as r_excepts
from validations import (last_name_check, membership_type_check,
                         date_format_check, url_check, profession_check,
                         url_other_check)
with open("token.json", 'r') as f:
    TOKEN = json.load(f)
HEADERS = {
    "Authorization": f"{TOKEN['token_type']} {TOKEN['token_value']}"
}

class Catalogues:
    """**Common catalogues for table's construction**
    """
    DEGREES_OF_STUDIES = ['', 'ELEMENTARY', 'HIGH SCHOOL', 'ASSOCIATE DEGREE',
                          'BACHELOR´S DEGREE',
                          'UNIVERSITY 1ST PROFESSIONAL DEGREE',
                          'MASTER DEGREE', 'PHD DEGREE']
    #   PRESIDENTE NACIONAL, GOBERNADOR, DIPUTADO , PRESIDENTE MUNICIPAL, SENADOR NACIONAL, DIPUTACIONES LOCALES
    DISTRICT_TYPES = ['NATIONAL_EXEC', 'REGIONAL_EXEC', 'NATIONAL_LOWER', 'LOCAL_EXEC', 'NATIONAL_UPPER',
                      'REGIONAL_LEGISLATIVE']
    GENDERS = ['', 'M', 'F']
    MEMBERSHIP_TYPES = ['', 'officeholder', 'campaigning_politician',
                        'party_leader', 'officeholder_substitute']
    # privilegiado, apodo, nombre de la boleta
    OTHER_NAMES_TYPES = ['', 'preferred', 'nickname', 'ballot_name']
    #   GOBERNADOR, DIPUTADO , PRESIDENTE MUNICIPAL, SENADOR NACIONAL, DIPUADO LOCAL
    ROLE_TYPES = ['', 'governmentOfficer', 'legislatorLowerBody', 'executiveCouncil', 'legislatorUpperBody',
                  'regionalLegislator']
    SPANISH_ROLES = {'governmentOfficer': "gubernatura",
                     "executiveCouncil": "presidencia",
                     "legislatorLowerBody": "diputación del distrito federal",
                     "legislatorUpperBody": "senaduría",
                     "regionalLegislator": "diputación del distrito local"}
    URL_TYPES = {"Website": "WEBSITE_OFFICIAL",
                 "URL_FB_page": "FACEBOOK_CAMPAIGN",
                 "URL_FB_profile": "FACEBOOK_PERSONAL",
                 "URL_IG": "INSTAGRAM_CAMPAIGN", "URL_TW": "TWITTER",
                 "URL_photo": "PHOTO", "source_of_truth": "SOURCE_OF_TRUTH",
                 "URL_logo": "LOGO"}
    URL_OWNER_TYPES = ["", "PERSON", "PARTY", "COALITION", "MEMBERSHIP"]


def make_banner(title):
    """**Make a banner for visual purposes**

    :param title: Messages to be highlighted
    :type: str
    """
    print()
    print("\t"*5, title)
    print("\t"*5, "-"*len(title))
    print()


def colors_to_list(data):
    """**Convert a string of colors to list**

    :param data: Data from GSheet
    :type: list
    :return: A list of colors
    "rtype: list
    """
    for row in data:
        colors_list = row["colors"].split(",")
        row["colors"] = [color.strip("' ") for color in colors_list]
    return data


def get_columns_data(data, pattern):
    """**Gets data from columns based on a text pattern**

    :param data: Current test fields of the sheet in a dict form
    :type data: dict
    :param pattern: Text pattern to be search in dict keys
    :type pattern: str
    :return: Dict with key-value that match pattern
    :rtype: dict
    """
    return {field: data[field] for field in data if pattern in field}


def row_to_dict(row, header, test_fields=[]):
    """**Converts from a row of the sheet to a python dict**

    :param row: Current row of the sheet
    :type row: list
    :param header: The header of the sheet
    :type header: list
    :return: A dict with header as keys and row as values
    :rtype: dict
    """
    data = dict()
    columns = test_fields if test_fields else header
    # Making dict with column-value pairs
    for column in columns:
        try:
            data[column] = row[header.index(column)]
        # Row is shorter than header. Last fields must be empty
        except IndexError:
            data[column] = ''
            continue
    return data


def verification_process(dataset, header):
    """**Function that run the verifications**

    :param dataset: List of dicts with GSheet header as keys and row as values
    :type dataset: list
    :param header: GSheet header as list
    :type header: list
    :return: List with comma separated strings that contains errors if any
    :rtype: list
    """
    lines = []
    # Loop to read every row
    with ProgressBar(max_value=len(dataset)) as bar:
        for i, row in enumerate(dataset, start=1):
            if not row["person_id"]:
                continue
            line = f'{i}'
            # Tests suite start
            line += ",last_name" if not last_name_check(row["last_name"] or "") else ""
            line += ",membership_type" if not membership_type_check(row["membership_type"]) else ""
            line += ",start_date" if not date_format_check(row["start_date"], "start_end") else ""
            line += ",end_date" if not date_format_check(row["end_date"], "start_end") else ""
            line += ",date_birth" if not date_format_check(row["date_birth"], "birth") else ""
            professions = get_columns_data(row, "profession")
            # TODO: from 2 to 6 only
            line += ",professions" if not profession_check(professions.values()) else ""
            line += url_check(row["Website"].split(','), "light", "Website")
            line += url_check(row["URL_FB_page"].split(','), "strict", "URL_FB_page")
            line += url_check(row["URL_FB_profile"].split(','), "strict", "URL_FB_profile")
            line += url_check(row["URL_IG"].split(','), "strict", "URL_IG")
            line += url_check(row["URL_TW"].split(','), "strict", "URL_TW")
            line += url_other_check(row["URL_others"].split(","))
            # If no errors, discard this line
            if line == str(i):
                line = ''
                continue
            # Adding candidate name at the end of the line
            else:
                line += f",{row['full_name']}"
                lines.append(line)
            bar.update(i - 1)
    return lines


def write_csv(data, name, path=""):
    """**Write a csv file with current data**

    :param data: A comma separated string
    :type data: str
    :param name: Name of the file
    :type:
    :param path:
    :type: str, optional
    """
    full_path = os.path.join(path, name)
    with open(f"{full_path}.csv", 'w', encoding="utf-8") as f:
        f.write(data)


def read_csv(file_name, path="", as_dict=False):
    """**Reads a csv file**

    :param file_name: File name
    :type file_name: str
    :param path: Path of the file, defaults to ""
    :type path: str, optional
    :return: List of lists with csv rows data
    :rtype: list
    """
    full_path = os.path.join(path, file_name)
    with open(full_path + ".csv", "r", encoding="utf-8") as f:
        data = [line.split(",") for line in f.read().rstrip("\n").split("\n")]
    if as_dict:
        header = data.pop(0)
        return [row_to_dict(row, header) for row in data]
    else:
        return data


def make_table(header, dataset):
    """**Fuction that make a csv table from a list of data**

    :param header: Header of the table
    :type header: list
    :param dataset: Data of the table
    :type dataset: list
    :return: Table as string
    :rtype: str
    """
    table = ','.join(header) + '\n'
    for row_data in dataset:
        if "is_deleted" in row_data.keys() and row_data["is_deleted"]:
            continue
        else:
            for field in header:
                try:
                    cell = row_data[field].strip("\r\n ")
                    if ',' in row_data[field] :
                        table += f'"{cell}",'
                    else:
                        table += f'{cell},'
                except AttributeError:
                    table += f"{row_data[field]},"
            table += '\n'
    return table


def get_contest_id(data, contest_chambers):
    """**Gets the contest id based on Catalogues**

    :return: The contest id if any, else
    :rtype: int
    """

    # Gubernaturas
    if data["role_type"] == "governmentOfficer":
        location = data["state"].lower()
        #print("gubernatura: " + Catalogues.SPANISH_ROLES[data["role_type"]])
    # Alcaldías (presidencia)
    elif data["role_type"] == "executiveCouncil":
        location = data["area"].lower()
        #print("alcaldia: " + Catalogues.SPANISH_ROLES[data["role_type"]])
    # Diputación
    elif data["role_type"] == "legislatorLowerBody":
        location = f"distrito federal {data['area']} de {data['state'].lower()}"
        #print("diputacion: " + Catalogues.SPANISH_ROLES[data["role_type"]])
    # Senaduria
    elif data["role_type"] == "legislatorUpperBody":
        location = f"senaduría de {data['state'].lower()}"
        #print("senaduria: " + Catalogues.SPANISH_ROLES[data["role_type"]])
    # Diputación local
    elif data["role_type"] == "regionalLegislator":
        location = f"distrito local {data['area']} {data['state'].lower()}"
        #print("diputacion local: " + Catalogues.SPANISH_ROLES[data["role_type"]])

    location = data['contest'].lower()
    for i, contest_chamber in enumerate(contest_chambers, start=1):
        #if location in contest_chamber and Catalogues.SPANISH_ROLES[data["role_type"]] in contest_chamber:
        if location in contest_chamber:
            return i

    print("person_id: " + str(data["person_id"]))
    print("role_type: " + str(data["role_type"]))
    #print("role_type_es: " + str(Catalogues.SPANISH_ROLES[data["role_type"]]))
    print("location: " + str(location) + "\n")
    #print("contest_chamber: " + str(contest_chambers))
    return -1

def get_role_id(roles, contest_id):
    """**Gets the role id **

    :return: The role id if any, else
    :rtype: int
    """

    for i, role in enumerate(roles, start=1):
        if int(role["contest_id"]) == int(contest_id):
            #print("Role SI " + role["contest_id"] + " vs " + str(contest_id) + ": " + str(i))
            return i

    print("Role NO " + role["contest_id"] + " vs " + str(contest_id))
    return -1

def make_person_struct(dataset, contest_chambers, header):
    """**Function that makes person data**

    This function build a list of dicts with valid person data for the API

    :param dataset: Data from GSheet
    :type dataset: list
    :param contest_chambers: List of static table contest
    :type contest_chambers: list
    :param header: Header of GSheet
    :type header: list
    :return: List with dicts that contains person data
    :rtype: list
    """
    people = []
    for data in dataset:
        row = dict()
        row["is_deleted"] = data["is_deleted"]
        for field in header:
            if field == "gender":
                row[field] = 2 if data[field] == "F" else 1
            elif field == "dead_or_alive":
                row[field] = True if data[field] == "Vivo" else False
            elif field == "last_degree_of_studies":
                if data[field]:
                    last_degree = data[field].upper()
                    row[field] = Catalogues.DEGREES_OF_STUDIES.index(last_degree)
                else:
                    row[field] = -1
            elif field == "contest_id":
                row[field] = get_contest_id(data, contest_chambers)
            elif field == "date_birth":
                if data[field]:
                    row[field] = data[field]
                else:
                    row[field] = '0001-01-01'
            elif field == "curp":
                if data.get(field):
                    row[field] = data[field]
                else:
                    row[field] = ''
            else:
                row[field] = data[field]
        people.append(row)
    return people


def make_other_names_struct(dataset):
    """**Makes other-names data**

    This function makes a valid list of other-name data for the API

    :param dataset: Data from GSheet
    :type dataset: list
    :return: List with dicts that contains other-name data
    :rtype: list
    """
    result = []
    other_name_id = 0
    for i, data in enumerate(dataset, start=1):
        # TODO: check multinickname case
        if data["nickname"]:
            other_name_id += 1
            result.append({
                "other_name_id": other_name_id,
                "is_deleted": data["is_deleted"],
                "other_name_type": 2, # TODO
                "name": data["nickname"],
                "person_id": i
            })
    return result


def make_person_profession(dataset, professions):
    """**Makes person-profession data**

    This function makes a valid list of person-profession data for the API from capture GSheet

    :param dataset: Data from GSheet
    :type dataset: list
    :param professions: Professions list from static table "Catalogue profession"
    :type professions: list
    :return: List with dicts that contains person-profession data
    :rtype: list
    """
    lines = []
    # Search only on this columns
    pattern = r'^profession_[2-6]$'
    person_profession_id = 0
    for i, data in enumerate(dataset, start=1):
        for field in data:
            if re.search(pattern, field):
                profession = data[field].lower()
                if profession:
                    try:
                        profession_id = professions.index(profession) + 1
                        person_profession_id += 1
                        lines.append({
                            "person_profession_id": person_profession_id,
                            "is_deleted": data["is_deleted"],
                            "person_id": i,
                            "profession_id": profession_id
                        })
                    except Exception:
                        print("make_person_profession error", i, "profession not found", profession, professions)
    return lines


def make_membership(dataset, parties, coalitions, contest_chambers, header, roles):
    """**Makes membership data**

    This functions makes a valid list of membership data for the API

    :param dataset: Data from GSheet
    :type dataset: list
    :param parties: Party list from static table "party"
    :type parties: list
    :param coalitions: Coalition list from static table "coalition"
    :type coalitions: list
    :param contest_chambers: constest-chamber list from static table "contest"
    :type contest_chambers: list
    :param header: Header of GSheet
    :type header: list
    :return: List with dicts that contains membership data
    :rtype: list
    """
    lines = []
    for i, data in enumerate(dataset, start=1):
        try:
            if data["coalition"]:
                coalition_id = coalitions.index(data["coalition"].lower().strip()) + 1
            else:
                coalition_id = -1
        except ValueError:
            print("make_membership coalitions error in line", i, "'",data["coalition"].lower().strip(), "'","not found")

        try:
            contest_id = get_contest_id(data, contest_chambers)
            role_id = get_role_id(roles, contest_id)
            lines.append({
                "is_deleted": data["is_deleted"],
                "membership_id": i,
                "person_id": i,
                # TODO: By now contest_id == role_id. Change soon
                "role_id": role_id,
                "party_id": parties.index(data["abbreviation"].lower()) + 1,
                "coalition_id": coalition_id,
                "contest_id": contest_id,
                "goes_for_coalition": True if data["coalition"] else False,
                "membership_type": Catalogues.MEMBERSHIP_TYPES.index(data["membership_type"]),
                "goes_for_reelection": False,  # Always false
                "start_date": data["start_date"], "end_date": data["end_date"],
                "is_substitute": True if data["is_substitute"] == "Sí" else False,
                "parent_membership_id": i if data["is_substitute"] == "Sí" else -1,
                "changed_from_substitute": False,  # TODO:
                "date_changed_from_substitute": "0001-01-01"  # TODO:
            })
        except ValueError:
            print("make_membership parties error in line", i, "'",data["abbreviation"].lower(), "'","not found")

    return lines


def get_url_type_id(field, url_types, url=""):
    """**Gets the url type id**

    Given a list of url types this function gets the id given by the
    field position in the list or the domain in the url

    :param field: Column field from the GSheet
    :type field: list
    :param url_types: Url types from static table "url_types"
    :type url_types: list
    :param url: Current url from GSheet, defaults to ""
    :type url: str, optional
    :return: Url type id
    :rtype: int
    """
    email_pattern = r'^[\w.+-]+@[\w-]+\.[\w.-]+$'
    # Searching by domain
    if field == "URL_others":
        for u_type in url_types:
            if u_type.lower() in url:
                return url_types.index(u_type) + 1
            elif re.search(email_pattern, url):
                return url_types.index("email") + 1
        # Url type not found, return 0
        return 0
    # Searching by column field
    else:
        return url_types.index(Catalogues.URL_TYPES[field].lower()) + 1


def get_owner_id(dataset, field_data, search_field):
    """**Gets party or coalition owner id**

    :param dataset: Data from GSheet
    :type dataset: list
    :param field_data: Value of the cell
    :type field_data: str
    :param search_field: Column field
    :type search_field: str
    :return: Owner id
    :rtype: int
    """
    for i, data in enumerate(dataset, start=1):
        if data[search_field].lower() == field_data.lower():
            return i
    return -1


def make_url_struct(dataset, url_types, url_id_counter, coalitions=[],
                    parties=[], owner_type=""):
    """**Makes url data**

    This function makes a valid list of url data for the API

    :param dataset: Data from GSheet
    :type dataset: list
    :param url_types: List with url types
    :type url_types: list
    :param url_id_counter: Incremental counter to carry the url ids
    :type url_id_counter: int
    :param coalitions: Coalitions list, defaults to []
    :type coalitions: list, optional
    :param parties: Parties list, defaults to []
    :type parties: list, optional
    :param owner_type: Url owner type, defaults to ""
    :type owner_type: str, optional
    :return: List of dicts that contains url data and the ids count
    :rtype: list, int
    """
    # TODO: refactor this stuff :(
    lines = []
    field_pattern = r'(^Website$|^URL_(\w)*$)'
    url_id = url_id_counter
    if owner_type in ["coalition", "party"]:
        for i, data in enumerate(dataset, start=1):
            for field in data:
                if re.search(field_pattern, field):
                    if data[field]:
                        for url in data[field].split(","):
                            if owner_type == "coalition":
                                owner_id = get_owner_id(coalitions, data["Coalicion"],
                                                        "name")
                            else:
                                owner_id = get_owner_id(parties, data["Abreviacion"],
                                                        "abbreviation")
                            url_id += 1
                            lines.append({
                                "url_id": url_id,
                                "url": data[field],
                                "url_type": get_url_type_id(field, url_types),
                                "description": "",
                                "owner_type": 3 if owner_type == "coalition" else 2,
                                "owner_id": owner_id
                            })
    # Person or membership
    else:
        for i, data in enumerate(dataset, start=1):
            for field in data:
                if re.search(field_pattern, field) and field != "URL_others":
                    if data[field]:
                        for url in data[field].split(','):
                            url_id += 1
                            row = {
                                    "url_id": url_id,
                                    "is_deleted": data["is_deleted"],
                                    "url": url.strip(),
                                    "url_type": get_url_type_id(field, url_types),
                                    "description": '',  # TODO
                                    "owner_type": 4 if field == "source_of_truth" else 1,  # TODO: persona, partido, coalicion
                                    "owner_id": i
                                }
                            lines.append(row)
                elif field == "URL_others":
                    for url in data[field].split(","):
                        clean_url = url.strip()
                        if clean_url:
                            url_id += 1
                            row = {
                                "url_id": url_id,
                                "is_deleted": data["is_deleted"],
                                "url": clean_url,
                                "url_type": get_url_type_id(field, url_types, clean_url),
                                "description": '',  # TODO
                                "owner_type": 1,  # TODO: persona, partido, coalicion
                                "owner_id": i
                            }
                            lines.append(row)
    return lines, url_id


def get_dummy_data(endpoint):
    """**Return dommy data based on the enpoint**

    :param endpoint: Endpoint of the API
    :type endpoint: str
    :return: Dummy data valid for the API
    :rtype: dict
    """
    if endpoint == "person":
        dummy_data = {
            "full_name": '',
            "first_name": '',
            "last_name": '',
            "date_birth": '0001-01-01',
            "gender": -1,
            "dead_or_alive": True,
            "last_degree_of_studies": -1,
            "contest_id": -1
        }
    elif endpoint == "other-name":
        dummy_data = {
            "other_name_type": -1,
            "name": "",
            "person_id": -1
        }
    elif endpoint == "person-profession":
        dummy_data = {
            "person_id": -1,
            "profession_id": -1
        }
    elif endpoint == "membership":
        dummy_data = {
            "person_id": -1,
            "role_id": -1,
            "party_id": -1,
            "coalition_id": -1,
            "contest_id": -1,
            "goes_for_coalition": False,
            "membership_type": -1,
            "goes_for_reelection": False,
            "start_date": "0001-01-01",
            "end_date": "0001-01-01",
            "is_substitute": False,
            "parent_membership_id": -1,
            "changed_from_substitute": False,
            "date_changed_from_substitute": "0001-01-01"
        }
    elif endpoint == "url":
        dummy_data = {
            "url": "",
            "description": "",
            "url_type": -1,
            "owner_type": -1,
            "owner_id": -1
        }
    elif endpoint == "area":
        dummy_data = {
            "ocd_id": "",
            "name": "",
            "country": "",
            "state": "",
            "city": "",
            "district_type": -1,
            "parent_area_id": -1,
        }
    elif endpoint == "role":
        dummy_data = {
            "title": "",
            "role": -1,
            "area_id": -1,
            "chamber_id": -1,
            "contest_id": -1,
        }
    elif endpoint == "party":
        dummy_data = {
            "name": "",
            "abbreviation": "",
            "area_id": -1,
            "colors": [],
            "coalition_id": -1,
        }
    elif endpoint == "contest":
        dummy_data = {
            "area_id": -1,
            "title": "",
            "membership_id_winner": -1,
            "start_date": "0001-01-01",
            "end_date": "0001-01-01",
            "election_identifier": ""
        }
    elif endpoint == "chamber":
        dummy_data = {
            "area_id": -1,
            "name": ""
        }
    return dummy_data


def send_data(base_url, endpoint, dataset):
    """**Sends data to the API**

    :param base_url: Base of the url API
    :type base_url: str
    :param endpoint: Current endpoint
    :type endpoint: str
    :param dataset: List of dicts with valid data to the endpoint of the API
    :type dataset: list
    """
    full_url = base_url + endpoint + '/'
    deleted = []
    with ProgressBar(max_value=len(dataset), redirect_stdout=True) as bar:
        for i, row in enumerate(dataset, start=1):
            try:
                if row["is_deleted"]:
                    dummy_data = get_dummy_data(endpoint)
                    r = requests.post(full_url, json=dummy_data, headers=HEADERS)
                    post_status = r.status_code
                    r = requests.delete(f"{full_url}{i}", headers=HEADERS)
                    delete_status = r.status_code
                    print(f"#{i} POST: {post_status} DELETE: {delete_status}")
                    deleted.append(row)
                    continue
                else:
                    del row["is_deleted"]
            except KeyError:
                pass
            try:
                # Sending row data to api
                r = requests.post(full_url, json=row, headers=HEADERS)
                if r.status_code != 201:
                    print(f"[ERROR]: {endpoint} #{i} status code: {r.status_code}")
                    print(f"msg: {r.json()['message']}")
            except r_excepts.ConnectionError:
                print("[CONNECTION ERROR]")
                print(f"#{i} | url: {full_url} | data:{row}")
                exit()
            bar.update(i - 1)
    if deleted:
        with open(f"deleted/{endpoint}.txt", "a") as f:
            json.dump(deleted, f)


def get_urls(api_base):
    """**Gets urls saved in the API

    :param api_base: Base of the url API
    :type api_base: str
    :return: List with dicts that contains url data
    :rtype: list
    """
    endpoint = "url"
    r = requests.get(api_base + endpoint, headers=HEADERS)
    if r.status_code != 200:
        print("[ERROR] {endpoint}: {r.status_code}")
        return []
    else:
        return r.json()


def get_url_ids(urls, current_url, person_id):
    """**Gets the url id**

    :param urls: Urls data
    :type urls: list
    :param old_url: Current url
    :type old_url: str
    :param person_id: Person id in the API
    :type person_id: int
    :return: List of all urls that match url on the API equals to
     current url and person id equals to owner id in the API
    :rtype: list
    """
    return [url["id"] for url in urls if url["url"] == current_url and url["owner_id"] == person_id]


def update_person_data(data, api_base, logger):
    """**Update a single person data on the API**

    :param data: Data with person id, changed field, old and new values
    :type data: dict
    :param api_base: Base of url API
    :type api_base: str
    :param logger: Logger object
    :type logger: object
    """
    endpoint = "person"
    # Getting people
    people = read_csv(endpoint, path="csv_db/", as_dict=True)
    # Week 1 = 3 May
    WEEK = get_update_week()
    field = data["field"]
    # Getting person to be update
    new_person_data = people[int(data["person_id"]) - 1]
    # Get values to be cast
    contest_id = new_person_data["contest_id"]
    gender = new_person_data["gender"]
    last_degree = new_person_data["last_degree_of_studies"]
    is_alive = new_person_data["dead_or_alive"]
    # Update the changed field
    new_person_data[field] = data["new"]
    # Casting data to be send
    new_person_data["contest_id"] = int(contest_id)
    new_person_data["gender"] = int(gender)
    new_person_data["last_degree_of_studies"] = int(last_degree)
    new_person_data["dead_or_alive"] = True if is_alive == "True" else False
    r = requests.put(f"{api_base}{endpoint}/{data['person_id']}",
                     json=new_person_data, headers=HEADERS)
    log_msg = f"""{WEEK},{field},{r.request.method},{r.status_code},{data['person_id']},"{data['old']}","{data['new']}" """
    logger.info(log_msg)


def update_other_name_data(data, api_base, logger):
    """**Update a single other-name data on the API**

    :param data: Data with person id, changed field, old and new values
    :type data: dict
    :param api_base: Base of url API
    :type api_base: str
    :param logger: Logger object
    :type logger: object
    """
    # Week 1 = 3 May
    WEEK = get_update_week()
    endpoint = 'other-name'
    field = data["field"]
    other_names = read_csv(endpoint, path="csv_db/", as_dict=True)
    for name in other_names:
        if data["person_id"] == name["person_id"]:
            new_name = name
    new_name["name"] = data["new"]
    new_name["other_name_type"] = int(new_name["other_name_type"])
    r = requests.put(f"{api_base}{endpoint}/{data['person_id']}", json=new_name,
                     headers=HEADERS)
    log_msg = f"""{WEEK},{field},{r.request.method},{r.status_code},{data['person_id']},"{data['old']}","{data['new']}" """
    logger.info(log_msg)


def update_profession_data(data, api_base, professions_catalogue, logger):
    """**Update a single person-profession data on the API**

    :param data: Data with person id, changed field, old and new values
    :type data: dict
    :param api_base: Base of url API
    :type api_base: str
    :param professions_catalogue: Catalogue of professions
    :type: list
    :param logger: Logger object
    :type logger: object
    """
    endpoint = "person-profession"
    WEEK = get_update_week()
    field = data["field"]
    people_professions = read_csv(endpoint, path="csv_db/", as_dict=True)
    # Profession removed
    if not data["new"]:
        person_profession_id = get_person_profession_id(data,
                                                        people_professions,
                                                        professions_catalogue)
        r = requests.delete(f"{api_base}{endpoint}/{person_profession_id}",
                           headers=HEADERS)
    # It's a new profession
    elif not data["old"]:
        profession_id = professions_catalogue.index(data["new"].lower()) + 1
        new_profession = {
            "person_id": int(data["person_id"]),
            "profession_id": profession_id
        }
        r = requests.post(f"{api_base}{endpoint}/", json=new_profession,
                          headers=HEADERS)
    # Profession changed
    else:
        person_profession_id = get_person_profession_id(data,
                                                        people_professions,
                                                        professions_catalogue)
        new_profession = get_person_profession(person_profession_id,
                                               people_professions)
        new_profession_id = professions_catalogue.index(data["new"].lower()) + 1
        new_profession["profession_id"] = new_profession_id
        r = requests.put(f"{api_base}{endpoint}/{person_profession_id}",
                         json=new_profession, headers=HEADERS)
    log_msg = f"""{WEEK},{field},{r.request.method},{r.status_code},{data['person_id']},"{data['old']}","{data['new']}" """
    logger.info(log_msg)




def update_url_data(data, api_base, urls, url_types, logger):
    """**Update url data**

    :param data: Data with person id, changed field, old and new values
    :type data: dict
    :param api_base: Base of url API
    :type api_base: str
    :param urls: Urls on the API in a list
    :type: list
    :param url_types: Url types catalogue
    :type: list
    :param logger: Logger object
    :type logger: object
    """
    # Week 1 = 3 May
    WEEK = get_update_week()
    endpoint = 'url'
    field = data["field"]
    # Urls removed
    if not data["new"]:
        url_ids = get_url_ids(urls, data["old"], int(data["person_id"]))
        for url_id in url_ids:
            r = requests.delete(f"{api_base}{endpoint}/{url_id}",
                                headers=HEADERS)
    # It's a new url
    elif not data["old"]:
        for new_url in data["new"].split(','):
            new_url = new_url.strip(" \n\r")
            url_data = {
                "url": new_url,
                "url_type": get_url_type_id(field, url_types, new_url),
                "description": '',
                # TODO: coalitions and parties
                "owner_type": 4 if field == "source_of_truth" else 1,
                "owner_id": data["person_id"]
            }
            r = requests.post(f"{api_base}{endpoint}/", json=url_data,
                              headers=HEADERS)
    # Update a previous url
    else:
        # Update a single url
        if len(data["old"].split(",")) == 1 and len(data["new"].split(",")) == 1:
        # Update a single url
            r = False
            for url in urls:
                if int(data["person_id"]) == int(url["owner_id"]) and data["old"] == url["url"]:
                    url_type = "_".join(url["url_type"].split()).lower()
                    new_url_data = {
                        "url": data["new"].strip(" \n\r"),
                        "url_type": url_types.index(url_type) + 1,
                        "description": '',
                        # TODO: make a function for this
                        "owner_type": Catalogues.URL_OWNER_TYPES.index(url["owner_type"]),
                        "owner_id": int(data["person_id"]),
                    }
                    r = requests.put(f"{api_base}{endpoint}/{url['id']}",
                                    json=new_url_data, headers=HEADERS)
        # Update Multi URLs
        else:
            # Symmetric difference
            old_urls = data["old"].split(',')
            new_urls = data["new"].split(',')
            diff_urls = set(old_urls) ^ set(new_urls)
            for url in diff_urls:
                # delete URL
                if url in old_urls:
                    url_ids = get_url_ids(urls, url, int(data["person_id"]))
                    for url_id in url_ids:
                        r = requests.delete(f"{api_base}{endpoint}/{url_id}",
                                            headers=HEADERS)
                # adding URL
                else:
                    url = url.strip(" \n\r")
                    url_data = {
                        "url": url,
                        "url_type": get_url_type_id(field, url_types, url),
                        "description": '',
                        # TODO: coalitions and parties
                        "owner_type": 4 if field == "source_of_truth" else 1,
                        "owner_id": data["person_id"]
                    }
                    r = requests.post(f"{api_base}{endpoint}/", json=url_data,
                                    headers=HEADERS)
    log_msg = f"""{WEEK},{field},{r.request.method},{r.status_code},{data['person_id']},"{data['old']}","{data['new']}" """
    logger.info(log_msg)


def update_membership_data(data, api_base, parties, coalitions, logger):
    """**Update a single membership data on the API**

    :param data: Data with person id, changed field, old and new values
    :type data: dict
    :param api_base: Base of url API
    :type api_base: str
    :param parties: Catalogue of parties
    :type parties: list
    :param coalitions: Catalogue of coalitions
    :type coalitions: list
    :param logger: Logger object
    :type logger: object
    """
    bool_fields = ["goes_for_coalition", "goes_for_reelection",
                   "is_substitute", "changed_from_substitute"]
    int_field_pattern = r".*_id"
    # Week 1 = 3 May
    WEEK = get_update_week()
    endpoint = 'membership'
    field = data["field"]
    memberships = read_csv(endpoint, path="csv_db/", as_dict=True)
    for membership in memberships:
        if data["person_id"] == membership["person_id"]:
            new_membership = membership
    # Casting values
    for key, value in new_membership.items():
        if re.search(int_field_pattern, key):
            new_membership[key] = int(value)
        elif key in bool_fields:
            new_membership[key] = True if value == "True" else False
    if field == "membership_type":
        new_membership[field] = Catalogues.MEMBERSHIP_TYPES.index(data["new"])
    elif field == "abbreviation":
        new_membership["party_id"] = parties.index(data["new"].lower()) + 1
    elif field == "coalition":
        if data["new"]:
            new_membership["coalition_id"] = coalitions.index(data["new"].lower().strip()) + 1
        else:
            new_membership["coalition_id"] = -1
    else:
        new_membership[field] = data["new"]
    r = requests.put(f"{api_base}{endpoint}/{new_membership['membership_id']}",
                     json=new_membership, headers=HEADERS)
    log_msg = f"""{WEEK},{field},{r.request.method},{r.status_code},{data['person_id']},"{data['old']}","{data['new']}" """
    logger.info(log_msg)


def search_by_name(dataset, name):
    """**Get person id by name**

    Function that gets id of a person from the API by name. It's a nayve implementation

    :param dataset: Data from GSheet
    :type dataset: list
    :param name: Person name
    :type name: str
    :return: Person id that match by full name and that row  as dict
    :rtype: int, dict
    """
    for i, row in enumerate(dataset):
        if row["full_name"] == name:
            return i + 1, row
    return -1, {}


def get_capture_lines(dataset):
    """**Generate dict data as in GSheet**

    Function that makes comma separated data as in GSheet and returns it as a list

    :param dataset: Data from GSheet as dict
    :type: list
    :returns: Data as list of csv strings
    :rtype: list
    """
    result = []
    for people in dataset:
        line = people["person_id"] + ','
        line += people["role_type"] + ','
        line += people["first_name"] + ','
        line += people["last_name"] + ','
        line += people["full_name"] + ','
        line += people["nickname"] + ','
        line += people["abbreviation"] + ','
        line += people["coalition"] + ','
        line += people["state"] + ','
        line += people["area"] + ','
        line += people["membership_type"] + ','
        line += people["start_date"] + ','
        line += people["end_date"] + ','
        line += people["is_substitute"] + ','
        line += people["is_titular"] + ','
        line += people["date_birth"] + ','
        line += people["gender"] + ','
        line += people["dead_or_alive"] + ','
        line += people["last_degree_of_studies"] + ','
        line += f'"{people["profession_1"]}",'
        line += people["profession_2"] + ','
        line += people["profession_3"] + ','
        line += people["profession_4"] + ','
        line += people["profession_5"] + ','
        line += people["profession_6"] + ','
        line += f'"{people["Website"]}",'
        line += f'"{people["URL_FB_page"]}",'
        line += f'"{people["URL_FB_profile"]}",'
        line += f'"{people["URL_IG"]}",'
        line += f'"{people["URL_TW"]}",'
        line += f'"{people["URL_others"]}",'
        line += f'"{people["URL_photo"]}",'
        line += f'"{people["source_of_truth"]}",'
        result.append(line)
    return result


def get_update_week():
    """**Get current update week number**

    Calculate current update process week number with respect to first
    update process week (2021, 5, 3)

    :returns: Update process week number
    :rtype: int
    """
    zero_week_date = date(2021, 5, 3)
    current_week = date.today()
    return current_week.isocalendar()[1] - zero_week_date.isocalendar()[1] + 1


def get_person_profession_id(data, people_professions, professions_catalogue):
    """**Gets the person-profession id**

    This function compare the person_id and the profession. If math returns
    the person-profession-id record in the api

    :param data: Data with person_id, old data en new data
    :type data: dict
    :param people_professions: List of person-profession records from the API
    :type people_professions: list
    :param professions_catalogue: Professions catalogue
    :type professions_catalogue: list
    :return: Person-profession id record from the API
    :rtype: int
    """
    for profession in people_professions:
        is_same_person = profession["person_id"] == data["person_id"]
        old_profession = professions_catalogue.index(data["old"].lower()) + 1
        is_same_profession = old_profession == int(profession["profession_id"])
        if is_same_person and is_same_profession:
            return int(profession["person_profession_id"])
    return -1


def get_person_profession(person_profession_id, people_professions):
    """**Gets person-profession record from the API by id**

    :param person_profession_id: Person profession id record
    :type person_profession_id: int
    :param people_professions: List of person-profession records from the API
    :type people_professions: list
    :return: The person profession record corresponding with the id
    :rtype: dict
    """
    for profession in people_professions:
        if int(profession["person_profession_id"]) == person_profession_id:
            profession["person_id"] = int(profession["person_id"])
            return profession
    return {}
