import time
import sys
import datetime
import ntxpi

# Configure InfluxDB connection variables
host = "192.168.29.190" # My Ubuntu NUC
port = 8086 # default port
user = "pi" # the user/password created for the pi, with write access
password = "test" 
dbname = "mydb" # the database we created earlier
interval = 60 # Sample period in seconds

# Create the InfluxDB client object
client = InfluxDBClient(host, port, user, password, dbname)
aquarium = ntxpi.aquarium()


# Enter the sensor details
sensor = Adafruit_DHT.DHT22
sensor_gpio = 4

# think of measurement as a SQL table, it's not...but...
measurement = "aquarium"
# location will be used as a grouping tag later
location = "Seattle"

# Run until you get a ctrl^c
try:
  
  while True:
      # Read the sensor using the configured driver and gpio
      temperature = aquarium.get_status()
      iso = time.ctime()
      # Print for debugging, uncomment the below line
      # print("[%s] Temp: %s, Humidity: %s" % (iso, temperature, humidity)) 
      # Create the JSON data structure
      data = [
      {
        "measurement": measurement,
            "tags": {
                "location": location,
            },
            "time": iso,
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

