from machine import Pin
import dht
import time

sensor = dht.DHT11(Pin(33))

print("DHT11 Sensor Reading Started...")

while True:
    try:
        sensor.measure() 
        
        temperature = sensor.temperature()  # °C
        humidity = sensor.humidity()        # %
        
        print("Temperature: {} °C".format(temperature))
        print("Humidity: {} %".format(humidity))
        print("---------------------------")
        
    except OSError:
        print("Failed to read from DHT11 sensor")

    time.sleep(5)  # DHT11 needs at least 1 second delay
