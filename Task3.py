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
URL_UPDATES = "https://api.telegram.org/bot{}/getUpdates".format(BOT_TOKEN)

# ---------- DHT11 ----------
sensor = dht.DHT11(Pin(33))

# ---------- RELAY ----------

relay = Pin(2, Pin.OUT)
relay.value(0)          # make sure relay starts OFF
relay_state = False     

# ---------- WIFI CONNECT ----------
wifi = network.WLAN(network.STA_IF)
wifi.active(True)
wifi.connect(SSID, PASSWORD)

print("Connecting to WiFi...")
while not wifi.isconnected():
    time.sleep(1)

print("WiFi connected")

# ---------- FUNCTION: send a message to Telegram ----------
def send_message(text):
    try:
        urequests.post(URL_SEND, json={
            "chat_id": CHAT_ID,
            "text": text
        })
        print("Sent:", text)
    except Exception as e:
        print("Send error:", e)


# ---------- FUNCTION: check for new commands ----------

last_update_id = 0

def check_commands(temp, hum):
    global last_update_id, relay_state

    try:
        
        url = URL_UPDATES + "?offset={}".format(last_update_id + 1)
        response = urequests.get(url)
        data = response.json()
        response.close()
    except Exception as e:
        print("Poll error:", e)
        return

    # go through any new messages
    for update in data["result"]:
        last_update_id = update["update_id"]  
        message_text = update["message"]["text"]

        print("Command received:", message_text)

        if message_text == "/status":
            state_text = "ON" if relay_state else "OFF"
            send_message("Temp: {} C\nHumidity: {} %\nRelay: {}".format(temp, hum, state_text))

        elif message_text == "/on":
            relay.value(1)
            relay_state = True
            send_message("Relay turned ON")

        elif message_text == "/off":
            relay.value(0)
            relay_state = False
            send_message("Relay turned OFF")


# ---------- MAIN LOOP ----------
while True:
    try:
        sensor.measure()
        temp = sensor.temperature()
        hum = sensor.humidity()

        print("Temp:", temp, "Humidity:", hum)

        #check if anyone sent /status, /on, or /off
        check_commands(temp, hum)

    except Exception as e:
        print("Error:", e)

    time.sleep(5)