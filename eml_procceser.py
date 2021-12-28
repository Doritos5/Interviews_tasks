# OS Imports
import pathlib
from multiprocessing import Manager
import os

# 3d party imports
from concurrent.futures import ProcessPoolExecutor
import argparse
import parse_emails


# Local imports
from helpers.rabit_handlers import Consumer
from helpers.spam_assassin_utils import handle_spam_assassin


# Global variables
__SPAM_SERVICE_ADDR__ = __MAIL_DIR_PATH__ = __FILE_DIR_PATH__ = str()
__THRESHOLD__ = 0

m = Manager()
lock = m.Lock()


def set_csv_file():
    global __FILE_DIR_PATH__
    __FILE_DIR_PATH__ = os.path.join(pathlib.Path(__file__).parent.resolve(), "results.csv")

    if not os.path.exists(__FILE_DIR_PATH__):
        with open(__FILE_DIR_PATH__, "w") as fw:
            fw.write("eml filename, Subject, Sender address, Spam-assassin score, # of attachments, Received date")


set_csv_file()

def fetch_time_received_from_header(headers: list) -> str:
    return [cell["value"] for cell in headers
            if cell["name"] == "Received"][0].split(";")[-1]


def handle_single_file(ch, method, properties, body):
    global lock, __FILE_DIR_PATH__, __SPAM_SERVICE_ADDR__, __MAIL_DIR_PATH__, __THRESHOLD__

    file_name = body.decode("utf-8")
    file_path = os.path.join(__MAIL_DIR_PATH__, file_name)

    email = parse_emails.ParseEmails(file_path=file_path, parse_only_headers=False)
    email.parse_emails()
    parsed_email = email.parsed_email

    mail_score = handle_spam_assassin(file_path=file_path,
                                      sa_address=__SPAM_SERVICE_ADDR__)
    if mail_score < __THRESHOLD__:
        return

    file_details = [file_name,
                    parsed_email["Subject"],
                    parsed_email["From"],
                    str(mail_score),
                    str(len(parsed_email['AttachmentNames'])),
                    fetch_time_received_from_header(headers=parsed_email["Headers"])]

    with lock:
        with open(__FILE_DIR_PATH__, "a") as csv_writer:
            try:
                csv_writer.write(f"\n{','.join(file_details)}")
            except Exception as e1:
                # TODO: Maybe add logger?
                print("Error occured while handling message, returning without ack")
                return
            ch.basic_ack(delivery_tag=method.delivery_tag)


def worker():
    Consumer().consume(callback_func=handle_single_file)


def worker_factory(threshold: float, spam_service_address: str, mails_folder_path: dict, pool_size: int):
    # TODO: Check connection to the spam_service_address
    global __SPAM_SERVICE_ADDR__, __MAIL_DIR_PATH__, __THRESHOLD__
    __SPAM_SERVICE_ADDR__, __MAIL_DIR_PATH__, __THRESHOLD__ = spam_service_address, mails_folder_path, threshold

    features = list()

    with ProcessPoolExecutor(pool_size) as executor:
        for _ in range(pool_size):
            feature = executor.submit(worker)
            features.append(feature)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Initialize n number of workers, then pull and handle .eml files",
        usage="python3 eml_fetcher.py [threshold] [spam_service_ip] [mails_folder_path] [pool_size]",
    )

    parser.add_argument("-t", "--threshold", type=float, help="Spam assassin threshold. (default: 5)", default=5)
    parser.add_argument(
        "-s",
        "--spam_service_address",
        type=str,
        help="Spam service ip and port seperated with "
        "column ':' (i.e. 127.0.0.1:1234)",
        required=True,
    )
    parser.add_argument("-m", "--mails_folder_path", type=str, help="Directory that contains eml files",
                        required=True)
    parser.add_argument(
        "-p", "--pool_size", type=int, help="Number of consumers (default: 4)", default=4)

    worker_factory(**parser.parse_args().__dict__)
