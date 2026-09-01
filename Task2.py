import network
import urequests
import time
from machine import Pin
import dht

# ---------- WIFI ----------
SSID = "Robotic WIFI"
PASSWORD = "rbtWIFI@2025"

# ---------- TELEGRAM ----------
BOT_TOKEN = "8657601341:AAH_7bUTcNDGi0StYzCz61PZHlNrx5_921U"
CHAT_ID = "-5074828078"

URL_SEND = "https://api.telegram.org/bot{}/sendMessage".format(BOT_TOKEN)

# ---------- DHT11 ----------
sensor = dht.DHT11(Pin(33))

# ---------- WIFI CONNECT ----------
wifi = network.WLAN(network.STA_IF)
wifi.active(True)
wifi.connect(SSID, PASSWORD)

print("Connecting to WiFi...")
while not wifi.isconnected():
    time.sleep(1)

print("WiFi connected")

# ---------- MAIN LOOP ----------
while True:
    try:
        sensor.measure()
        temp = sensor.temperature()
        hum = sensor.humidity()

        message = "Hello from ESP32! Bot is online."

        urequests.post(URL_SEND, json={
            "chat_id": CHAT_ID,
            "text": message
        })

        print("Sent:", message)

    except Exception as e:
        print("Error:", e)

    time.sleep(5  )   # send every 10 seconds (change if needed)

