from io import BytesIO
import socket
import re

divider_pattern = re.compile(br'^(.*?)\r?\n(.*?)\r?\n\r?\n', re.DOTALL)
first_line_pattern = re.compile(br'^SPAMD/[^ ]+ 0 EX_OK$')


def _build_message(message):
    reqfp = BytesIO()
    data_len = str(len(message)).encode()
    reqfp.write(b'REPORT SPAMC/1.2\r\n')
    reqfp.write(b'Content-Length: ' + data_len + b'\r\n')
    reqfp.write(b'User: cx42\r\n\r\n')
    reqfp.write(message)
    return reqfp.getvalue()


def parse_response(response):

    match = divider_pattern.match(response)
    first_line = match.group(1)
    headers = match.group(2)
    body = response[match.end(0):]

    # Checking response is good
    match = first_line_pattern.match(first_line)
    if not match:
        return None

    report_list = [s.strip() for s in body.decode('utf-8').strip().split('\n')]
    linebreak_num = report_list.index([s for s in report_list if "---" in s][0])
    tablelists = [s for s in report_list[linebreak_num + 1:]]

    # join line when current one is only wrap of previous
    tablelists_temp = list()
    if tablelists:
        for counter, tablelist in enumerate(tablelists):
            if len(tablelist) > 1:
                if (tablelist[0].isnumeric() or tablelist[0] == '-') and (
                        tablelist[1].isnumeric() or tablelist[1] == '.'):
                    tablelists_temp.append(tablelist)
                else:
                    if tablelists_temp:
                        tablelists_temp[-1] += " " + tablelist
    tablelists = tablelists_temp

    # create final json
    report_json = dict()
    for tablelist in tablelists:
        wordlist = re.split('\s+', tablelist)
        report_json[wordlist[1]] = {'partscore': float(wordlist[0]), 'description': ' '.join(wordlist[1:])}

    headers = headers.decode('utf-8').replace(' ', '').replace(':', ';').replace('/', ';').split(';')
    return float(headers[2])


def handle_spam_assassin(sa_address: str, file_path: str):
    ip, port = sa_address.split(":")
    # Connecting
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.settimeout(15)
    client.connect((ip, int(port)))  # '51.124.222.17'

    # Sending
    with open(file_path, "rb") as fo:
        file_content = fo.read()
    client.sendall(_build_message(file_content))
    client.shutdown(socket.SHUT_WR)

    res = BytesIO()
    while True:
        data = client.recv(4096)
        if data == b'':
            break

        res.write(data)

    return parse_response(res.getvalue())
