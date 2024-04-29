import re
import datetime


def last_name_check(lastname):
    """**Check if lastname has at least two items**

    :param lastname: A lastname in list format
    :type: list
    :return: True is pass test, False otherwise
    :rtype: bool
    """
    return True if len(lastname) >= 3 else False


def membership_type_check(membership):
    """**Check if membership type is campaing_politician until June 2**

    :param membership: The membership type
    :type membership: str
    :return: True if membership type is campaing_politician and date
    is before June 2, False otherwise
    :rtype: bool
    """
    return True if membership in ["campaigning_politician", "officeholder", "party_leader"] else False


def date_format_check(date, date_type):
    """**Check if date has the format YYYY-MM-DD and a valid date**

    :param date: A date
    :type: str
    :return: True if date has the format YYYY-MM-DD with a valid date False
    otherwise
    :rtype: bool
    """
    birth_pattern = '(^(19|20)[0-9]{2}-(0[1-9]|1[0-2])-(0[1-9]|[1-2][0-9]|3[0-1])$|^$)'
    start_end_pattern = '(^20[0-2][0-9]-(0[1-9]|1[0-2])-(0[1-9]|[1-2][0-9]|3[0-1])$|^$)'
    if date_type == "birth":
        return True if re.search(birth_pattern, date) or "" else False
    elif date_type == "start_end":
        return True if re.search(start_end_pattern, date) or "" else False


def url_check(urls, mode, field):
    """**Check if the url has the valid format**

    Valid format in regex: "^http[s]?://w{3}\.\w+\.\w+$"

    :param url: A url
    :type: str
    :return: True if the url has a valid format False otherwise
    :rtype: bool
    """

    if mode == "strict":
        pattern = '(^http[s]?:\/\/w{3}\.(facebook|instagram|twitter)\.com\/([\w.%?=-]+)?$|^$)'
    elif mode == "light":
        pattern = '(^http[s]?:\/\/(w{3}\.)?[\w-]+[.\w]+(\/[\w.?%=@&-]+)*$|^$)'
    wrong_urls = [str(i) for i, url in enumerate(urls, start=1) if not re.search(pattern, url)]

    return f",{field}({','.join(wrong_urls)})" if wrong_urls else ""


def url_other_check(urls):
    wrong_urls = []
    email_pattern = '^[\w.+-]+@[\w-]+\.[\w.-]+$'
    url_pattern = '^http[s]?:\/\/(w{3}\.)?\w+[.\w]+(\/[\w.?%=@&-]+)*$'
    pattern = f'({email_pattern}|{url_pattern}|^$)'
    wrong_urls = [str(i+1) for i, url in enumerate(urls, start=1) if not re.search(pattern, url)]
    return f",URL_others({'|'.join(wrong_urls)})" if wrong_urls else ""


def profession_check(professions):
    """**Check if candidate have duplicated professions**

    :param professions: List of professions
    :type professions: list
    :return: True if candidate haven't duplicated professions, False otherwise
    :rtype: bool
    """
    # Ignoting empty columns
    professions = [profession for profession in professions if profession != ""]
    return True if len(professions) == len(set(professions)) else False
