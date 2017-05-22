# coding=utf-8
import csv, smtplib

NAME_FILE = "new_file.csv"
OUTPUT_DIR = "attachment/"

MAIL_CUSTOMER = "" 

MAIL_SENDER_S = "smtp.gmail.com"
MAIL_SENDER_U = ""
MAIL_SENDER_P = ""


def save_merg_csv(result_list):
    with open(NAME_FILE, 'wb') as newfile:
        wr = csv.writer(newfile, quoting=csv.QUOTE_ALL)
        wr.writerow(['key', 'timestemp', 'type', 'megabyte/sec'])
        for row_list in result_list:
            wr.writerow(row_list)


def merging_file(in_file, out_file):
    response = []
    next(in_file)
    next(out_file)
    # non efect
    for in_row in in_file:
        for out_row in out_file:
            in_ = ''.join(in_row).split(';')
            out_ = ''.join(out_row).split(';')
            if in_[1] == in_[1]:
                in_[2] = 'IN'
                out_[2] = 'OUT'
                response.append(in_)
                response.append(out_)
    return response


csv_in_data = csv.reader(file('сsv_tset_in.csv'))
csv_out_data = csv.reader(file('сsv_tset_out.csv'))
result_list = merging_file(csv_in_data, csv_out_data)
