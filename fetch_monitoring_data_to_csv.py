#!/usr/bin/python
# coding=utf-8
# Initial Source From : http://doc.bonfire-project.eu/R2/monitoring/bonfire_monitoring_data_to_csv.html
import datetime
import time
import argparse
import logging
import unittest
import option
import xmltodict
import zabbix_api
import csv

# ME Change
USERNAME = 'Admin'
PASSWORD = 'zabbixnst'
SERVER = '127.0.0.1'

NAME_FILE = "new_file.csv"
OUTPUT_DIR = "attachment/"
FULL_NAME_FILE = OUTPUT_DIR + NAME_FILE

# --------------------------------------------------------
# Converting Timestamp to Datetime.
# --------------------------------------------------------
def get_datetime_from_timestamp(time_stamp):
    return datetime.datetime.fromtimestamp(int(time_stamp)).strftime('%Y-%m-%d %H:%M:%S')


def get_current_time(_format):
    return datetime.datetime.now().strftime(_format)


# --------------------------------------------------------
# Get File type - we process txt and xml differently
# --------------------------------------------------------
def get_file_type(filename):
    if filename:
        try:
            file_extension = str(filename).split('.')[1]
        except:
            file_extension = ''

        if file_extension == '':
            return 'txt'
        elif file_extension == 'xml':
            return 'xml'
        elif file_extension == 'txt':
            return 'txt'
        else:
            return 'txt'
    else:
        logging.error('Filename is empty. Please enter a Filename')
        exit()


# --------------------------------------------------------
# Loading XML as a dictionary.
# --------------------------------------------------------
def load_xml_as_dictionary(file_name):
    try:
        # Open a file in read-only mode
        document_file = open(file_name, "r")

        # read the file object
        original_document = document_file.read()

        # Parse the read document string
        dictionary_document = xmltodict.parse(original_document)
        return dictionary_document

    # Exit if there is an issue.
    except:
        logging.exception("Could not read XML file please check, Exiting Now.")
        exit()


# --------------------------------------------------------
# Get Keys from XML file (Zabbix Export XML file)
# --------------------------------------------------------
def get_keys_from_xml_file(file_name):
    xml_dictionary = load_xml_as_dictionary(file_name)
    list_of_keys_xml = []

    try:
        for item in xml_dictionary['zabbix_export']['hosts']['host']['items']['item']:
            if item['key'] not in list_of_keys_xml:
                list_of_keys_xml.append(item['key'].strip())
    except:
        logging.error("Please check XML file. XML expected is Zabbix Export XML.")
        exit()

    return list_of_keys_xml


# --------------------------------------------------------
# Get Keys from TXT file. One Key per line.
# --------------------------------------------------------
def get_keys_from_txt_file(file_name):
    try:
        # Open a file in read-only mode
        document_file = open(file_name, "r")

        list_of_keys_txt = []

        for key in document_file:
            key = key.strip()
            if key not in list_of_keys_txt:
                list_of_keys_txt.append(key)

        return list_of_keys_txt

    # Exit if there is an issue.
    except:
        logging.exception("Could not read TXT file please check, Exiting Now. Please use One Key per Line")
        exit()


# --------------------------------------------------------
# Fetch Multiple Key Monitoring Data into a CSV file.
# --------------------------------------------------------
# def fetch_multi_key_monitoring_data_to_csv(username, password, server, hostname, file_name,
#                                            datetime_start, datetime_end, debuglevel=0):
#     extension = get_file_type(file_name)

#     if extension == 'xml':
#         key_list = get_keys_from_xml_file(file_name)
#     else:
#         key_list = get_keys_from_txt_file(file_name)

#     out_file_name = hostname + '-' + get_current_time('%Y-%m-%d-%H-%M-%S') + ".csv"
#     csv_file_to_wt = open(out_file_name, 'w+')

#     # Writing Header
#     csv_file_to_wt.write("key;timestamp;value\n")

#     # Each Key will have a separate file.
#     for key in key_list:
#         logging.debug("Key we are fetching Now : " + str(key))
#         try:
#             fetch_monitoring_data_to_single_csv(username, password, server, hostname, key,
#                                                 csv_file_to_wt, datetime_start, datetime_end, debuglevel)
#         except:
#             logging.error("Could Not Get Key from Zabbix : '" + key + "' , Moving on to Next Key")
#             continue

#     # We are done lets close file.
#     csv_file_to_wt.close()


# --------------------------------------------------------
# Fetching Multiple Monitoring Data to Single CSV.
# --------------------------------------------------------
def fetch_monitoring_data_to_single_csv(hostname, key, csv_file_write, datetime_start, datetime_end, debuglevel):
    # Simple check before we start
    if datetime_start == '' and datetime_end == '':
        logging.error(" Need -t1 option ")
        exit()

    #
    # Connect to Zabbix and get a handle
    #
    zabbix_login_desc = zabbix_api.ZabbixAPI(server=SERVER, log_level=debuglevel)
    zabbix_login_desc.login(USERNAME, PASSWORD)

    #
    # Get host and item id  to get specific Item information.
    #
    host_id = zabbix_login_desc.host.get({"filter": {"host": hostname}, "output": "extend"})[0]["hostid"]
    item_id = zabbix_login_desc.item.get({"filter": {"key_": key, "hostid": host_id}, "output": "extend"})

    logging.debug("Host ID :" + str(host_id))
    logging.debug("Item ID :" + str(item_id))

    # Setting the item id
    item_id_number = item_id[0]["itemid"]

    write_string_to_file = ""

    # Check for start / end datetime
    if datetime_start != '' and datetime_end == '':

        date_start = datetime.datetime.strptime(datetime_start, '%Y-%m-%d %H:%M:%S')

        # Convert to timestamp, since no end time is given we take the current time.
        timestamp_start = time.mktime(date_start.timetuple())
        timestamp_end = int(round(time.time()))

        # Query for the information
        history = zabbix_login_desc.history.get(
            {"history": item_id[0]["value_type"], "time_from": timestamp_start, "time_till": timestamp_end,
             "itemids": [item_id_number, ], "output": "extend"})
        increment = 0

        # We recieve a large dictionary, which we traverse to get our data.
        for history_data in history:
            # write each line at a time.
            # Picking key, clock, value information, (clock is in timestamp format)
            # convert timestamp to current time in %Y-%m-%d %H:%M:%S format
            write_string_to_file = write_string_to_file + key + ";" + \
                                   get_datetime_from_timestamp(history_data["clock"]) + ";" + \
                                   history_data["value"] + "\n"
            # Record counter
            increment += 1

    else:

        # Now we have the start and end time.
        date_start = datetime.datetime.strptime(datetime_start, '%Y-%m-%d %H:%M:%S')
        date_end = datetime.datetime.strptime(datetime_end, '%Y-%m-%d %H:%M:%S')

        # Concert to timestamp
        timestamp_start = time.mktime(date_start.timetuple())
        timestamp_end = time.mktime(date_end.timetuple())

        # Get dictionary
        history = zabbix_login_desc.history.get(
            {"history": item_id[0]["value_type"], "time_from": timestamp_start, "time_till": timestamp_end,
             "itemids": [item_id_number, ], "output": "extend"})

        # Start Counter
        increment = 0

        # Traverse the dictionary (JSON)
        for history_data in history:
            # write each line at a time.
            # Picking key, clock, value information, (clock is in timestamp format)
            # convert timestamp to current time in %Y-%m-%d %H:%M:%S format
            write_string_to_file = write_string_to_file + key + ";" + \
                                   get_datetime_from_timestamp(history_data["clock"]) + ";" + \
                                   history_data["value"] + "\n"

            # Record Counter
            increment += 1

    # Lets write all the values to the file.
    csv_file_write.write(write_string_to_file)


# --------------------------------------------------------
# Unit tests
# --------------------------------------------------------
class TestGetFileType(unittest.TestCase):
    def setUp(self):
        self.file_extension_text = get_file_type('file.txt')
        self.file_extension_xml = get_file_type('file.xml')
        self.file_extension_none = get_file_type('file')
        self.file_extension_empty = get_file_type('')

    def TestResult(self):
        self.assertEqual(self.file_extension_text, 'txt')
        self.assertEqual(self.file_extension_xml, 'xml')
        self.assertEqual(self.file_extension_none, 'txt')
        self.assertEqual(self.file_extension_empty, 'txt')


# --------------------------------------------------------
# Main Function -
# --------------------------------------------------------
def save_merg_csv(result_list):
    with open(NAME_FILE, 'wb') as newfile:
        wr = csv.writer(newfile, quoting=csv.QUOTE_ALL)
        wr.writerow(['key', 'timestemp', 'type', 'megabyte/sec'])
        for row_list in result_list:
            row_list[3] = (((int(row_list[3])*8)%1024)%1024)%60
            print row_list[3]
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

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Fetch history from aggregator and save it into CSV file')
    file_key_group = parser.add_mutually_exclusive_group(required=True)

    parser.add_argument('-s', '--server-ip', help='Server IP address', required=True)

    parser.add_argument('-n', '--hostname', help='Hostname of the VM', required=True)
    parser.add_argument('-n2', '--hostname_second', help='Hostname of the VM', required=True)

    file_key_group.add_argument('-k', '--key', help='Zabbix Item key')
    file_key_group.add_argument('-k2', '--key_second', help='Zabbix Item key')

    file_key_group.add_argument('-f', '--file', help='Zabbix Item key File. XML export file from Zabbix. '
                                                     'Text file with key in each line.'
                                                     'Each Key will create its own csv file.')

    parser.add_argument('-u', '--username', help='Zabbix username', required=True)
    parser.add_argument('-p', '--password', help='Zabbix password', required=True)
    parser.add_argument('-o', '--output', default='',
                        help='Output file name, default key_hostname.csv (will remove all special chars).'
                             'This Option currently works with -k/--key option.')
    parser.add_argument('-t1', '--datetime-start', help='Start datetime, \'yyyy-mm-dd HH:MM:SS\' '
                                                        'use this pattern \'2014-10-15 19:12:00\" '
                                                        'if only t1 specified then time period will be t1 to now() ',
                        required=True)
    parser.add_argument('-t2', '--datetime-end', default='', help='end datetime, \"yyyy-mm-dd HH:MM:SS\" '
                                                                  'use this pattern \'2014-10-15 19:12:00\'')
    parser.add_argument('-v', '--debug-level', default=0, type=int, help='log level, default 0')

    args = parser.parse_args()

    if args.debug_level > 0:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    yesterday = datetime.datetime.now() - datetime.timedelta(days=1)
    yesterday.strftime('%m%d%y%H%M')

    if args.key and args.key_second:
        # Open a file based on the input.
        output_file_name = ''.join(element for element in args.key if element.isalnum())
        output_file_name = str(output_file_name).lower() + '_' + str(args.hostname).lower() + str(get_current_time('%Y-%m-%d')) + ".csv"
        csv_file_to_write = open(output_file_name, 'w+')

        #_second
        output_file_name_second = ''.join(element for element in args.key_second if element.isalnum())
        output_file_name_second = str(output_file_name_second).lower() + '_' + str(args.hostname_second).lower() + str(get_current_time('%Y-%m-%d')) + ".csv"
        csv_file_to_write_second = open(output_file_name_second, 'w+')

        # Writing Header
        csv_file_to_write.write("key;timestamp;value\n")
        csv_file_to_write_second.write("key;timestamp;value\n")

        fetch_monitoring_data_to_single_csv(args.hostname_second, args.key_second, csv_file_to_write_second,
                                            get_current_time('%Y-%m-%d %H:%M:%S'), args.datetime_end, debuglevel=args.debug_level)
        csv_file_to_write_second.close()

        fetch_monitoring_data_to_single_csv(args.hostname, args.key, csv_file_to_write,
                                            get_current_time('%Y-%m-%d %H:%M:%S'), args.datetime_end, debuglevel=args.debug_level)
        csv_file_to_write.close()

        csv_in_data = csv.reader(file(csv_file_to_write))
        csv_out_data = csv.reader(file(csv_file_to_write_second))
        result_list = merging_file(csv_in_data, csv_out_data)
        save_merg_csv(result_list)

    # elif args.file:
    #     fetch_multi_key_monitoring_data_to_csv(args.username, args.password, "http://" + args.server_ip + "/zabbix",
    #                                            args.hostname, args.file, args.datetime_start, args.datetime_end,
    #                                            debuglevel=args.debug_level)
    else:
        exit()
