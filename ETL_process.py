import boto3
import json
import psycopg2
import configparser
import argparse
import sys
import hashlib
from datetime import datetime

config = configparser.ConfigParser()
print("Attempting to read configuration from:", config.read('postgres.ini'))

class ETL_Process:

    def __init__(self, endpoint_url, queue_name, wait_time, max_messages):
        # Initialize configuration and queue parameters
        print(queue_name)
        config = configparser.ConfigParser()
        config.read('postgres.ini')
        self.__username = config.get('postgres', 'username')
        self.__password = config.get('postgres', 'password')
        self.__host = config.get('postgres', 'host')
        self.__database = config.get('postgres', 'database')
        self.__endpoint_url = endpoint_url
        self.__queue_name = queue_name
        self.__wait_time = wait_time
        self.__max_messages = max_messages

    def get_messages(self):
        # Fetch messages from SQS
        sqs_client = boto3.client("sqs", endpoint_url=self.__endpoint_url)
        try:
            response = sqs_client.receive_message(
                QueueUrl=self.__endpoint_url + '/' + self.__queue_name,
                MaxNumberOfMessages=self.__max_messages,
                WaitTimeSeconds=self.__wait_time
            )
        except Exception as e:
            print("Error - " + str(e))
            sys.exit()
        return response['Messages']
    
    def hash_pii(self, data):
        # Hash data using SHA-256
        return hashlib.sha256(data.encode()).hexdigest()
    
    def transform_data(self, messages):
        # Process messages to mask PII and prepare for DB insertion
        message_list = []
        try:
            if not messages:
                raise IndexError("Message list is empty")
        except IndexError as e:
            print("Error - " + str(e))
            sys.exit()
        
        message_count = 0
        for message in messages:
            message_count += 1
            message_body = json.loads(message['Body'])
            ip = message_body.get('ip')
            device_id = message_body.get('device_id')
            if not ip or not device_id:
                print(f"Skipping message {message['MessageId']} due to missing 'ip' or 'device_id'")
                continue
            
            hashed_ip = self.hash_pii(ip)
            hashed_device_id = self.hash_pii(device_id)
            message_body['ip'] = hashed_ip
            message_body['device_id'] = hashed_device_id
            message_list.append(message_body)
        return message_list

    def load_data_postgre(self, message_list):
        # Load processed data into PostgreSQL
        if not message_list:
            print("Error - message list is empty")
            sys.exit()

        postgres_conn = psycopg2.connect(
            host=self.__host, database=self.__database,
            user=self.__username, password=self.__password
        )
        cursor = postgres_conn.cursor()
        for message_json in message_list:
            try:
                message_json['app_version'] = int(message_json['app_version'].split('.')[0])
                message_json['locale'] = 'None' if message_json['locale'] is None else message_json['locale']
                message_json['create_date'] = datetime.now().strftime("%Y-%m-%d")
                values = list(message_json.values())
                cursor.execute(
                    "INSERT INTO user_logins (user_id, app_version, device_type, masked_ip, locale, masked_device_id, create_date) VALUES (%s, %s, %s, %s, %s, %s, %s)", 
                    values)
                postgres_conn.commit()
            except psycopg2.Error as e:
                print("Failed to insert data:", e)
                postgres_conn.rollback()
        postgres_conn.close()

def main():
    # Set up and run the ETL process
    parser = argparse.ArgumentParser(
        prog="Extract Transform Load - Process",
        description="Program extracts data from SQS queue - Transforms PIIs in the data - Loads the processed data into Postgres",
        epilog="Please raise an issue for code modifications"
    )
    parser.add_argument('-e', '--endpoint-url', required=True, help="Pass the endpoint URL here")
    parser.add_argument('-q', '--queue-name', required=True, help="Pass the queue URL here")
    parser.add_argument('-t', '--wait-time', type=int, default=10, help="Pass the wait time here")
    parser.add_argument('-m', '--max-messages', type=int, default=10, help="Pass the max messages to be pulled from SQS queue here")
    args = vars(parser.parse_args())
    etl_process_object = ETL_Process(args['endpoint_url'], args['queue_name'], args['wait_time'], args['max_messages'])
    print("Fetching messages from SQS Queue...")
    messages = etl_process_object.get_messages()
    print("Masking PIIs from the messages...")
    message_list = etl_process_object.transform_data(messages)
    print("Loading messages to Postgres...")
    etl_process_object.load_data_postgre(message_list)

if __name__ == "__main__":
    main()
