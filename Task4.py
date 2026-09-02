import network
import urequests
import time
from machine import Pin
import dht

# ---------- WIFI ----------
SSID = "Robotic WIFI"
PASSWORD = "rbtWIFI@2025"

# ---------- TELEGRAM ----------
BOT_TOKEN = " "
CHAT_ID = " "
URL_SEND = "https://api.telegram.org/bot{}/sendMessage".format(BOT_TOKEN)
URL_GET = "https://api.telegram.org/bot{}/getUpdates".format(BOT_TOKEN)

# ---------- HARDWARE ----------
sensor = dht.DHT11(Pin(33))
relay = Pin(15, Pin.OUT)

# Most blue relay modules are ACTIVE LOW (IN pin low = relay on).
# If your relay behaves backwards, flip this to True.
RELAY_ACTIVE_LOW = False

# ---------- CONTROL SETTINGS ----------
TEMP_LIMIT = 25       
LOOP_INTERVAL = 5     
POLL_INTERVAL = 1     

relay_state = False
last_temp = None
last_hum = None
last_update_id = 0


def set_relay(on):
    global relay_state
    if RELAY_ACTIVE_LOW:
        relay.value(0 if on else 1)
    else:
        relay.value(1 if on else 0)
    relay_state = on


def relay_text():
    return "ON" if relay_state else "OFF"


def send_telegram(text):
    try:
        r = urequests.post(URL_SEND, json={"chat_id": CHAT_ID, "text": text})
        r.close()          # important on ESP32, otherwise you run out of memory
        print("Sent:", text)
    except Exception as e:
        print("Telegram error:", e)


def status_message():
    if last_temp is None:
        return "Relay: {}\nNo sensor reading yet.".format(relay_text())
    return "Relay: {}\nTemperature: {} C\nHumidity: {} %\nLimit: {} C".format(
        relay_text(), last_temp, last_hum, TEMP_LIMIT)


def handle_command(text):
    cmd = text.strip().lower().split("@")[0]   
    if cmd == "/on":
        if relay_state:
            send_telegram("Relay is already ON.")
        else:
            set_relay(True)
            send_telegram("Relay turned ON. Alerts stopped.\n"
                          "It will switch OFF automatically below {} C.".format(TEMP_LIMIT))
    elif cmd == "/off":
        if relay_state:
            set_relay(False)
            send_telegram("Relay turned OFF.")
        else:
            send_telegram("Relay is already OFF.")
    elif cmd == "/status":
        send_telegram(status_message())
    elif cmd == "/start" or cmd == "/help":
        send_telegram("Commands:\n/on - turn relay on\n/off - turn relay off\n/status - current state")
    else:
        send_telegram("Unknown command. Send /on, /off or /status")


def check_telegram():
    """Read new messages and act on any commands."""
    global last_update_id
    try:
        r = urequests.get("{}?offset={}&timeout=0".format(URL_GET, last_update_id + 1))
        data = r.json()
        r.close()
    except Exception as e:
        print("Poll error:", e)
        return

    for update in data.get("result", []):
        last_update_id = update["update_id"]
        msg = update.get("message") or update.get("edited_message")
        if not msg:
            continue
        if str(msg["chat"]["id"]) != str(CHAT_ID):   # ignore strangers
            continue
        text = msg.get("text")
        if text:
            print("Received:", text)
            handle_command(text)


def flush_old_updates():
    """Skip messages that arrived while the board was off."""
    global last_update_id
    try:
        r = urequests.get(URL_GET)
        data = r.json()
        r.close()
        for update in data.get("result", []):
            last_update_id = update["update_id"]
    except Exception as e:
        print("Flush error:", e)


# ---------- WIFI CONNECT ----------
wifi = network.WLAN(network.STA_IF)
wifi.active(True)
wifi.connect(SSID, PASSWORD)
print("Connecting to WiFi...")
while not wifi.isconnected():
    time.sleep(1)
print("WiFi connected", wifi.ifconfig())

set_relay(False)          
flush_old_updates()       

# ---------- MAIN LOOP ----------
last_read = time.ticks_ms()
last_poll = time.ticks_ms()

while True:
    now = time.ticks_ms()

    # --- Telegram commands (checked often so /on reacts quickly) ---
    if time.ticks_diff(now, last_poll) >= POLL_INTERVAL * 1000:
        last_poll = now
        check_telegram()

    # --- reading + alert / auto-OFF logic, once per LOOP_INTERVAL ---
    if time.ticks_diff(now, last_read) >= LOOP_INTERVAL * 1000:
        last_read = now
        try:
            sensor.measure()
            last_temp = sensor.temperature()
            last_hum = sensor.humidity()
            print("Temp: {} C  Hum: {} %  Relay: {}".format(last_temp, last_hum, relay_text()))

            if last_temp >= TEMP_LIMIT:
                if not relay_state:
                    # repeat every loop until the user sends /on
                    send_telegram("ALERT: Temperature {} C (limit {} C)\n"
                                  "Humidity: {} %\nRelay is OFF - send /on to turn it on.".format(
                                      last_temp, TEMP_LIMIT, last_hum))
                # relay already ON -> stay silent
            else:
                if relay_state:
                    # one-time notice on the way down
                    set_relay(False)
                    send_telegram("Auto-OFF: Temperature dropped to {} C (below {} C).\n"
                                  "Relay switched OFF automatically.".format(last_temp, TEMP_LIMIT))
                # relay already OFF and cool -> stay silent

        except Exception as e:
            print("Sensor error:", e)

    time.sleep_ms(100)