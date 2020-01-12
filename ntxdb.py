import time
import sys
from datetime import datetime
import ntxpi
from influxdb import InfluxDBClient


# Configure InfluxDB connection variables
host = "localhost" # localhost default on pi, can also use IP.
port = 8086 # default port
user = "pi" # the user/password created for the pi, with write access
password = "test" 
dbname = "mydb" # the database we created earlier
interval = 1 # Sample period in seconds

# Create the InfluxDB client object
client = InfluxDBClient(host=host, port=port, user=user, password=password, database=dbname)

# Create an aquarium object, shift this to ntxpi later?
aquarium = ntxpi.aquarium()


# think of measurement as a SQL table, it's not...but...
measurement = "aquarium"
# location will be used as a grouping tag later
location = "Seattle"

# Run until you get a ctrl^c
try:
  
  while True:
      # Read the sensor using the configured driver and gpio
      temperature = aquarium.get_status()
      current_time = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')

      # Print for debugging, uncomment the below line
      # print("[%s] Temp: %s (iso, temperature, humidity)) 
      # Create the JSON data structure
      data = [
      {
        "measurement": measurement,
            "tags": {
                "location": location,
            },
            "time": current_time,
            "fields": {
                "temperature" : temperature
            }
        }
      ]
      # Send the JSON data to InfluxDB
      client.write_points(data)
      # Wait until it's time to query again...
      time.sleep(interval)
 
except KeyboardInterrupt:
    pass

