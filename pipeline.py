import sys
from datetime import datetime
from sheets import sheet_reader
from static_tables import (area_data, chamber_data, role_data, coalition_data,
                           coalitions_catalogue, party_data, parties,
                           contest_data, contest_chambers, profession_data,
                           professions_catalogue, url_types)
from utils import (make_banner, verification_process,
                   write_csv, make_table, make_person_struct,
                   make_other_names_struct, make_person_profession,
                   make_membership, make_url_struct, send_data)
# ID sheets
CAPTURE_SHEET_ID = "1p7XMADrpEXRKzC3WKwlr3zcpyuJ_moCy04tkEyWEPYY"
# Capture Read Ranges
READ_RANGE = "Todos!A1:AL1635"
COALITION_URL_RANGE = "URL_logo_partido_coal!A1:H1"
PARTY_URL_RANGE = "URL_logo_partido_coal!I1:R93"
CSV_DB_PATH = 'csv_db'
API_BASE = 'http://localhost:5000/'
# API endpoints
ENDPOINTS = ["area", "chamber", "role", "coalition", "party", "person",
             "other-name", "profession", "membership", "contest", "url"]
DB_TYPE = sys.argv[1]


def main():
    """**Entry function to the pipeline**

    This script made three actions: Run verifications, preprocess
    sheets data and sent these data to the API.

    :return: None
    """
    make_banner("(1/3) VERIFICATIONS")
    # Getting sheet data as list of list
    dataset = sheet_reader(CAPTURE_SHEET_ID, READ_RANGE)
    # Getting header
    header = dataset[0].keys()
    # Start capture verification
    print(f"\t * Test {len(dataset)} rows")
    error_lines = verification_process(dataset, header)
    if error_lines:
        # Writing report
        date = datetime.now()
        str_date = date.strftime("%y-%b-%d")
        write_csv("\n".join(error_lines), f"errors/{str_date}_errors")
        print(f"\n\t ** {len(error_lines)} fails **")
    else:
        print("\t OK. ")

    for data in dataset:
        empty_person_id = not data["person_id"]
        is_not_officerholder = data["membership_type"] != "officeholder"
        if DB_TYPE == "local":
            data["is_deleted"] = empty_person_id
        elif DB_TYPE == "fb":
            data["is_deleted"] = is_not_officerholder or empty_person_id
        else:
            print("[ERROR]: Insert valid values: <local | fb>")
            return -1
    # PREPROCESSING DYNAMIC DATA
    make_banner("(2/3) BUILD DYNAMIC DATA")

    # PERSON
    person_header = ["person_id", "dni", "full_name", "first_name", "last_name",
                     "date_birth", "gender", "dead_or_alive",
                     "last_degree_of_studies", "contest_id"]
    # This list is ready to be send to the API
    person_data = make_person_struct(dataset, contest_chambers, person_header)
    # Making a table for double check
    person_table = make_table(person_header, person_data)
    write_csv(person_table, f"{CSV_DB_PATH}/person")
    for person in person_data:
        del person["person_id"]

    # OTHER-NAME
    other_name_header = ["other_name_id", "other_name_type", "name",
                         "person_id"]
    # This list is ready to be send to the API
    other_names_data = make_other_names_struct(dataset)
    # Making a table for double check
    other_name_table = make_table(other_name_header, other_names_data)
    write_csv(other_name_table, f"{CSV_DB_PATH}/other-name")
    for other_name in other_names_data:
        del other_name["other_name_id"]

    #  PERSON-PROFESSION
    person_profession_header = ["person_profession_id", "person_id",
                                "profession_id"]
    person_profession_data = make_person_profession(dataset,
                                                    professions_catalogue)
    person_profession_table = make_table(person_profession_header,
                                         person_profession_data)
    write_csv(person_profession_table, f"{CSV_DB_PATH}/person-profession")
    for person_profession in person_profession_data:
        del person_profession["person_profession_id"]

    # MEMBERSHIP
    membership_header = ["membership_id", "person_id", "role_id", "party_id",
                         "coalition_id", "contest_id",
                         "goes_for_coalition", "membership_type",
                         "goes_for_reelection",
                         "start_date", "end_date", "is_substitute",
                         "parent_membership_id", "changed_from_substitute",
                         "date_changed_from_substitute"]
    membership_data = make_membership(dataset, parties, coalitions_catalogue,
                                      contest_chambers, membership_header)
    membership_table = make_table(membership_header, membership_data)
    write_csv(membership_table, f"{CSV_DB_PATH}/membership")
    for membership in membership_data:
        del membership["membership_id"]

    # URL
    url_header = ["url_id", "url", "description", "url_type", "owner_type",
                  "owner_id"]
    url_id_counter = 0
    url_data, url_id_counter = make_url_struct(dataset, url_types,
                                               url_id_counter)
    # Getting parties and coalition URLs
    party_url = sheet_reader(CAPTURE_SHEET_ID, PARTY_URL_RANGE)
    coalition_url = sheet_reader(CAPTURE_SHEET_ID, COALITION_URL_RANGE)

    url_party, url_id_counter = make_url_struct(party_url, url_types,
                                                url_id_counter, coalition_data,
                                                party_data, "party")
    url_coalition, url_id_counter = make_url_struct(coalition_url, url_types,
                                                    url_id_counter,
                                                    coalition_data, party_data,
                                                    "coalition")
    url_data += url_party
    url_data += url_coalition
    url_table = make_table(url_header, url_data)
    write_csv(url_table, f"{CSV_DB_PATH}/url")
    for url in url_data:
        del url["url_id"]
    print("\t * Ok.")

    make_banner("(3/3) SEND DATA TO API")
    # AREA (static)
    print("\t * AREA")
    send_data(API_BASE, 'area', area_data)
    # CHAMBER (static)
    print("\t * CHAMBER")
    send_data(API_BASE, 'chamber', chamber_data)
    # ROLE (static)
    print("\t * ROLE")
    send_data(API_BASE, 'role', role_data)
    # COALITION (static)
    print("\t * COALITION")
    send_data(API_BASE, 'coalition', coalition_data)
    # PARTY (static)
    print("\t * PARTY")
    send_data(API_BASE, 'party', party_data)
    # PERSON (dynamic)
    print("\t * PERSON")
    send_data(API_BASE, 'person', person_data)
    # OTHER-NAME (dynamic)
    print("\t * OTHER-NAME")
    send_data(API_BASE, 'other-name', other_names_data)
    # PROFESSION (static)
    print("\t * PROFESSION")
    send_data(API_BASE, 'profession', profession_data)
    # PERSON-PROFESSION (dynamic)
    print("\t * PERSON-PROFESSION")
    send_data(API_BASE, 'person-profession', person_profession_data)
    # MEMBERSHIP (dynamic)
    print("\t * MEMBERSHIP")
    send_data(API_BASE, 'membership', membership_data)
    # CONTEST (static)
    print("\t * CONTEST")
    send_data(API_BASE, 'contest', contest_data)
    # URL (dynamic)
    print("\t * URL")
    send_data(API_BASE, 'url', url_data)
    make_banner("Finish. Have a nice day :)")


if __name__ == "__main__":
    main()
