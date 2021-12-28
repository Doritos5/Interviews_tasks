# OS Imports
from os import path, listdir, access, R_OK
from time import sleep

# 3d party imports
import argparse

# Local imports
from helpers.rabit_handlers import Publisher


def fetcher(mails_folder_path: str):
    if not mails_folder_path or (not path.exists(mails_folder_path) or not access(mails_folder_path, R_OK)):
        raise RuntimeError(f"The given directory: {mails_folder_path} doe's not exists, or has no read permissions")
    processed_file = set()

    while True:
        with Publisher() as p:
            for file in (f for f in listdir(mails_folder_path) if f.endswith(".eml")):  # Use generator for this
                if file not in processed_file:
                    p.publish_message(file.encode("utf-8"))
                    processed_file.add(file)
                    print(f"indexing {file}\n")
        sleep(2)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Start a service that fetches all .eml file names from a given directory, and indexes them into a "
                    "durable queue",
        usage="python3 eml_fetcher.py [mails_folder_path]")

    parser.add_argument("-m", "--mails_folder_path", type=str, help="Directory that contains eml files", required=True)

    fetcher(**parser.parse_args().__dict__)
