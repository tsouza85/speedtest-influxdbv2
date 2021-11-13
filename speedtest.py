#!/usr/bin/env python3

import datetime
import json
import os
import subprocess
import time
import socket
import sys
from influxdb_client import InfluxDBClient

# Variables
influxdb_scheme = os.getenv("INFLUXDB_SCHEME", "http")
influxdb_host = os.getenv("INFLUXDB_HOST", "localhost")
influxdb_port = int(os.getenv("INFLUXDB_PORT", 8086))
influxdb_user = os.getenv("INFLUXDB_USER")
influxdb_pass = os.getenv("INFLUXDB_PASS")
influxdb_token = os.getenv("INFLUXDB_TOKEN")
influxdb_org = os.getenv("INFLUXDB_ORG", "-")
influxdb_db = os.getenv("INFLUXDB_DB")
start_time = datetime.datetime.now().replace(microsecond=0).isoformat()
default_hostname = socket.gethostname()
hostname = os.getenv("SPEEDTEST_HOST", default_hostname)
speedtest_server = os.getenv("SPEEDTEST_SERVER")


def db_check():
    print("STATE: Running database check")
    client_health = client.health().status

    if client_health == "pass":
        print("STATE: Connection", client_health)
    elif client_health == "fail":
        print("ERROR: Connection", client_health,
              " - Check scheme, host, port, user, pass, token, org, etc...")
        sys.exit(1)
    else:
        print("ERROR: Something else went wrong")
        sys.exit(1)


def speedtest():
    db_check()

    current_time = datetime.datetime.now().replace(microsecond=0).isoformat()
    print("STATE: Loop running at", current_time)

    # Run Speedtest
    print("STATE: User did not specify speedtest server, using a random server")
    print("STATE: Speedtest running")
    my_speed = subprocess.run(
        ['/usr/bin/SpeedTest', '--output=json'], stdout=subprocess.PIPE, text=True, check=True, timeout=120)

    # Convert the string into JSON, only getting the stdout and stripping the first/last characters
    my_json = json.loads(my_speed.stdout.strip())

    # Get the values from JSON and log them to the Docker logs
    # Basic values
    speed_down = my_json["download"]
    speed_up = my_json["upload"]
    ping_latency = my_json["ping"]
    ping_jitter = my_json["jitter"]
    # Advanced values
    speedtest_server_name = my_json["server"]["name"]
    speedtest_server_sponsor = my_json["server"]["sponsor"]
    speedtest_server_host = my_json["server"]["host"]

    # Print results to Docker logs
    print("NOTE:  RESULTS ARE SAVED IN BPS NOT MBPS")
    print("STATE: Your download     ", speed_down, "bps")
    print("STATE: Your upload       ", speed_up, "bps")
    print("STATE: Your ping latency ", ping_latency, "ms")
    print("STATE: Your ping jitter  ", ping_jitter, "ms")
    print("STATE: Your server info  ", speedtest_server_name,
          speedtest_server_sponsor, speedtest_server_host)

    # This is ugly, but trying to get output in line protocol format (UNIX time is appended automatically)
    # https://docs.influxdata.com/influxdb/v2.0/reference/syntax/line-protocol/
    p = "speedtest," + "service=speedtest.net," + "host=" + str(hostname) + " download=" + str(speed_down) + ",upload=" + str(speed_up) + ",ping_latency=" + str(ping_latency) + ",ping_jitter=" + str(
        ping_jitter) + ",speedtest_server_name=" + "\"" + str(speedtest_server_name) + "\"" + ",speedtest_server_sponsor=" + "\"" + str(speedtest_server_sponsor) + "\"" + ",speedtest_server_host=" + "\"" + str(speedtest_server_host) + "\""

    try:
        print("STATE: Writing to database")
        write_api = client.write_api()
        write_api.write(bucket=influxdb_db, record=p)
        write_api.__del__()
    except Exception as err:
        print("ERROR: Error writing to database")
        print(err)

# Some logging
print("#####\nScript starting!\n#####")

# Check if variables are set
print("STATE: Checking environment variables...")

if 'INFLUXDB_DB' in os.environ:
    print("STATE: INFLUXDB_DB is set")
    pass
else:
    print("ERROR: INFLUXDB_DB is not set")
    sys.exit(1)

if 'INFLUXDB_TOKEN' in os.environ:
    print("STATE: INFLUXDB_TOKEN is set, so we must be talking to an InfluxDBv2 instance")
    pass
    # If token is set, then we are talking to an InfluxDBv2 instance, so INFLUXDB_ORG must also be set
    if 'INFLUXDB_ORG' in os.environ:
        print("STATE: INFLUXDB_ORG is set")
        pass
    else:
        print("ERROR: INFLUXDB_TOKEN is set, but INFLUXDB_ORG is not set")
        sys.exit(1)
else:
    print("STATE: INFLUXDB_TOKEN is not set, so we must be talking to an InfluxDBv1 instance")
    # If token is not set, then we are talking an InfluxDBv1 instance, so INFLUXDB_USER and INFLUXDB_PASS must also be set
    if 'INFLUXDB_USER' in os.environ:
        print("STATE: INFLUXDB_USER is set")
        pass
    else:
        print("ERROR: INFLUXDB_USER is not set")
        sys.exit(1)

    if 'INFLUXDB_PASS' in os.environ:
        print("STATE: INFLUXDB_PASS is set")
        pass
    else:
        print("ERROR: INFLUXDB_PASS is not set")
        sys.exit(1)
    # If token is not set, influxdb_token must be a concatenation of influxdb_user:influxdb_pass when talking to an InfluxDBv1 instance
    # https://docs.influxdata.com/influxdb/v1.8/tools/api/#apiv2query-http-endpoint
    influxdb_token = f'{influxdb_user}:{influxdb_pass}'

# Instantiate the connection
connection_string = influxdb_scheme + "://" + \
    influxdb_host + ":" + str(influxdb_port)
print("STATE: Database URL is... " + connection_string)
print("STATE: Connecting to InfluxDB...")
client = InfluxDBClient(url=connection_string,
                        token=influxdb_token, org=influxdb_org)

try:
    speedtest()
except subprocess.CalledProcessError as e:
    print("command '{}' return with error (code {}): {}".format(
        e.cmd, e.returncode, e.output))
pass
