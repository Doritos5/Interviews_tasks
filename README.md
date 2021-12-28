# Dato exercise

This exercise was made by `Dor Mordechai`

The purpose of this exercise is to get a directory with eml files, parse them, send them to `Apache spam-assassin`, and if the received score is bigger than the threshold, it will be indexed in CSV called `"results.csv"` along with a number of attachments, received time and more.

`required: Python 3.8+`

## Installation

The prerequisite is installed, and up and running `RabitMQ`, at the default port and address.

A durable queue named `incoming_email_files` will be created.

If `RabitMQ` is not up and running in your environment, you can use docker.

```bash
docker run -it --rm --name rabbitmq -p 5672:5672 -p 15672:15672 rabbitmq:3.8-management
```
And the requirement file:
```bash
pip install -r requirements.txt
```
with the following content:
```
pika==1.2.0
parse-emails==0.0.1
```

## Usage

For the `eml_fetcher.py`:

```bash
usage: python3 eml_fetcher.py [mails_folder_path]

Start a service that fetches all .eml file names from a given directory, and
indexes them into a durable queue

optional arguments:
  -h, --help            show this help message and exit
  -m MAILS_FOLDER_PATH, --mails_folder_path MAILS_FOLDER_PATH
                        The directory that contains eml files
```

For the `eml_procceser.py`:

```bash
usage: python3 eml_fetcher.py [threshold] [spam_service_ip] [mails_folder_path] [pool_size]

Initialize n number of workers, then pull and handle .eml files

optional arguments:
  -h, --help            show this help message and exit
  -t THRESHOLD, --threshold THRESHOLD
                        Spam assassin threshold. (default: 5)
  -s SPAM_SERVICE_ADDRESS, --spam_service_address SPAM_SERVICE_ADDRESS
                        Spam service ip and port seperated with column ':'
                        (i.e. 127.0.0.1:1234)
  -m MAILS_FOLDER_PATH, --mails_folder_path MAILS_FOLDER_PATH
                        Directory that contains eml files
  -p POOL_SIZE, --pool_size POOL_SIZE
                        Number of consumers (default: 4)
```
