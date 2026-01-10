import csv
from fake_useragent import UserAgent


def save_2disk(list_: list, filename="data/results.csv") -> None:
    if not list_:
        return None

    keys = list_[0].keys()
    with open(filename, "w", newline="", encoding="utf-8") as output_file:
        dict_writer = csv.DictWriter(output_file, fieldnames=keys)
        dict_writer.writeheader()
        dict_writer.writerows(list_)
        return None


def get_header():
    ua = UserAgent()
    header = {"user-agent": ua.random}
    return header
