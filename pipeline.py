from sheets import sheet_reader
from utils import (make_banner, verification_process,
                   write_csv, make_table, make_person_struct,
                   make_other_names_struct, make_person_profession,
                   make_membership, make_url_struct, colors_to_list,
                   send_data)
# ID sheets
CAPTURE_SHEET_ID = "1mk9LTI5RBYwrEPzILeDY925VJbLVmEoZyRzaa1gZ_hk"
STRUCT_SHEET_ID = "1fKXpwXhKlLLG-kjh8udQIH9poNLs7kAzSnXndZ1Le4Y"
# Capture Read Ranges
READ_RANGES = ["Gubernaturas!A1:AB114",
               "Alcaldías!A1:AC131",
               "Diputaciones!A1:AD1370"
               ]
# Struct read ranges
STRUCT_READ_RANGES = {
    "area": "B1:H376", "chamber": "B1:C358", "role": "B1:F358",
    "coalition": "B1:D36", "party": "B1:F78",
    "profession": "B1:B119", "contest": "B1:G358"
    # "past-membership": "A1:G1",
    }
# Only test in this columns
TEST_FIELDS = ["last_name", "membership_type", "start_date", "end_date",
               "date_birth", "profession_2", "profession_3",
               "profession_4", "profession_5", "profession_6", "Website",
               "URL_FB_page", "URL_FB_profile", "URL_IG", "URL_TW",
               "URL_others"]
API_BASE = 'http://localhost:5000/'
# API endpoints
ENDPOINTS = ["area", "chamber", "role", "coalition", "party", "person",
             "other-name", "profession", "membership", "contest", "url"]


def main():
    make_banner("Pipeline Start")
    print("\t * Getting static tables data")
    # AREA
    area_data = sheet_reader(STRUCT_SHEET_ID,
                             f"Table area!{STRUCT_READ_RANGES['area']}")
    # CHAMBER
    chamber_data = sheet_reader(STRUCT_SHEET_ID,
                                f"Table chamber!{STRUCT_READ_RANGES['chamber']}")
    # ROLE
    role_data = sheet_reader(STRUCT_SHEET_ID,
                             f"Table role!{STRUCT_READ_RANGES['role']}")
    # COALITION
    coalition_data = sheet_reader(STRUCT_SHEET_ID,
                                  f"Table coalition!{STRUCT_READ_RANGES['coalition']}")
    coalition_data = colors_to_list(coalition_data)
    coalitions = sheet_reader(STRUCT_SHEET_ID, "Table coalition!B2:B36",
                              as_list=True)
    coalitions = [c[0].lower().strip() for c in coalitions]
    # PARTY
    party_data = sheet_reader(STRUCT_SHEET_ID,
                              f"Table party!{STRUCT_READ_RANGES['party']}")
    party_data = colors_to_list(party_data)
    parties = sheet_reader(STRUCT_SHEET_ID, "Table party!C2:C78", as_list=True)
    # Parties is a list of lists. Getting party string
    parties = [p[0].lower() for p in parties]
    # CONTEST
    contest_data = sheet_reader(STRUCT_SHEET_ID,
                                f"Table contest!{STRUCT_READ_RANGES['contest']}")
    contest_chambers = sheet_reader(STRUCT_SHEET_ID, "Table contest!C2:C358",
                                    as_list=True)
    contest_chambers = [cc[0].lower() for cc in contest_chambers]
    # PROFESSION
    profession_data = sheet_reader(STRUCT_SHEET_ID,
                                   f"Catalogue profession!{STRUCT_READ_RANGES['profession']}")
    professions_catalogue = sheet_reader(STRUCT_SHEET_ID,
                                         "Catalogue profession!B2:B119",
                                         as_list=True)
    # Professions is a list of lists. Getting only proferssion string
    professions_catalogue = [pc[0].lower() for pc in professions_catalogue]
    url_types = sheet_reader(STRUCT_SHEET_ID,
                             "Catalogue url_types!B2:B23", as_list=True)
    url_types = [u[0] for u in url_types]
    # Dynamic data containers
    person_data, other_names_data, person_profession_data = [], [], []
    membership_data, url_data = [], []
    print("\t OK.")
    # Main loop throught sheet pages
    for read_range in READ_RANGES:
        current_chamber = read_range.split('!')[0].lower()
        # Getting sheet data as list of list
        dataset = sheet_reader(CAPTURE_SHEET_ID, read_range)
        make_banner(f"{current_chamber} = {len(dataset)}")
        # Getting header
        header = dataset[0].keys()
        # Start capture verification
        print("\t * Tests Suite begin")
        error_lines = verification_process(dataset, header)
        if error_lines:
            # Writing report
            write_csv("\n".join(error_lines),
                      f"{current_chamber}_errors")
            print(f"\n\t ** {len(error_lines)} lines failed at {current_chamber} **")
        else:
            print("\t Ok.")

        # PREPROCESSING DYNAMIC DATA
        print("\t * Build dynamic data")

        # PERSON
        person_header = ["full_name", "first_name", "last_name", "date_birth",
                         "gender", "dead_or_alive", "last_degree_of_studies",
                         "contest_id"]
        person_count = len(person_data)
        # This list is ready to be send to the API
        person_tmp = make_person_struct(dataset, current_chamber,
                                        contest_chambers, person_header)
        # Making a table for double check
        person_table = make_table(person_header, person_tmp)
        write_csv(person_table, f"{current_chamber}/person")
        person_data += person_tmp

        # OTHER-NAME
        other_name_header = ["other_name_type", "name", "person_id"]
        # This list is ready to be send to the API
        other_names_tmp = make_other_names_struct(dataset, person_count)
        # Making a table for double check
        other_name_table = make_table(other_name_header, other_names_tmp)
        write_csv(other_name_table, f"{current_chamber}/other-name")
        other_names_data += other_names_tmp

        #  PERSON-PROFESSION
        person_profession_header = ["person_id", "profession_id"]
        person_profession_tmp = make_person_profession(dataset,
                                                       professions_catalogue,
                                                       person_count)
        person_profession_table = make_table(person_profession_header,
                                             person_profession_tmp)
        write_csv(person_profession_table,
                  f"{current_chamber}/person-profession")
        person_profession_data += person_profession_tmp

        # MEMBERSHIP
        membership_header = ["person_id", "role_id", "party_id",
                             "coalition_id", "contest_id",
                             "goes_for_coalition", "membership_type",
                             "goes_for_reelection",
                             "start_date", "end_date", "is_substitute",
                             "parent_membership_id", "changed_from_substitute",
                             "date_changed_from_substitute"]
        membership_tmp = make_membership(dataset, current_chamber,
                                         parties, coalitions,
                                         contest_chambers, membership_header,
                                         person_count)
        membership_table = make_table(membership_header, membership_tmp)
        write_csv(membership_table, f"{current_chamber}/membership")
        membership_data += membership_tmp

        # URL
        url_header = ["url", "description", "url_type", "owner_type",
                      "owner_id"]
        url_tmp = make_url_struct(dataset, url_types, current_chamber,
                                  person_count)
        url_table = make_table(url_header, url_tmp)
        write_csv(url_table, f"{current_chamber}/url")
        url_data += url_tmp
        print("\t * Ok.")
    make_banner("Sending data to API")
    # AREA
    print("\t * AREA")
    send_data(API_BASE, 'area', area_data)
    # CHAMBER
    print("\t * CHAMBER")
    send_data(API_BASE, 'chamber', chamber_data)
    # ROLE
    print("\t * ROLE")
    send_data(API_BASE, 'role', role_data)
    # COALITION
    print("\t * COALITION")
    send_data(API_BASE, 'coalition', coalition_data)
    # PARTY
    print("\t * PARTY")
    send_data(API_BASE, 'party', party_data)
    # PERSON
    print("\t * PERSON")
    send_data(API_BASE, 'person', person_data)
    # OTHER-NAME
    print("\t * OTHER-NAME")
    send_data(API_BASE, 'other-name', other_names_data)
    # PROFESSION
    print("\t * PROFESSION")
    send_data(API_BASE, 'profession', profession_data)
    # PERSON-PROFESSION
    print("\t * PERSON-PROFESSION")
    send_data(API_BASE, 'person-profession', person_profession_data)
    # MEMBERSHIP
    print("\t * MEMBERSHIP")
    send_data(API_BASE, 'membership', membership_data)
    # CONTEST
    print("\t * CONTEST")
    send_data(API_BASE, 'contest', contest_data)
    # URL
    print("\t * URL")
    send_data(API_BASE, 'url', url_data)


if __name__ == "__main__":
    main()
