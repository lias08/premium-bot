import os
import tls_client
import time
import json
import random

raw_config = os.getenv("BOT_CONFIG")
try:
    CONFIG_LIST = json.loads(raw_config) if raw_config else []
except:
    CONFIG_LIST = []

DB_FILE = "seen_items.txt"

def load_seen():
    if not os.path.exists(DB_FILE): return []
    with open(DB_FILE, "r") as f: return f.read().splitlines()

def save_seen(ids):
    # Nur die neuesten IDs behalten, um die Datei klein zu halten
    with open(DB_FILE, "w") as f: f.write("\n".join(map(str, ids[-1000:])))

def send_discord(webhook, item):
    import requests
    # ... (Hier die send_discord Funktion aus der vorigen Nachricht einfügen)
    requests.post(webhook, json=data)

def run_loop():
    session = tls_client.Session(client_identifier="chrome_120")
    seen_ids = load_seen()
    
    # Der Bot läuft hier bis GitHub ihn nach ca. 6 Stunden killt
    start_time = time.time()
    
    print("[!] Hacker-Modus aktiviert: Endlosschleife gestartet.")

    while True:
        # Nach 5,5 Stunden beenden wir den Loop selbst, damit GitHub 
        # die seen_items.txt noch speichern kann, bevor der Kill kommt.
        if time.time() - start_time > 20000: 
            print("[!] Zeitlimit fast erreicht. Speichere und beende...")
            break

        for entry in CONFIG_LIST:
            webhook = entry.get("webhook")
            v_url = entry.get("url")
            
            headers = {"User-Agent": "Mozilla/5.0"} # Minimalistisch
            api_url = v_url if "api/v2" in v_url else f"https://www.vinted.de/api/v2/catalog/items?{v_url.split('?')[-1]}&order=newest_first"

            try:
                res = session.get(api_url, headers=headers)
                if res.status_code == 200:
                    items = res.json().get("items", [])
                    for item in items:
                        i_id = str(item["id"])
                        if i_id not in seen_ids:
                            send_discord(webhook, item)
                            seen_ids.append(i_id)
                
                # Kurze Pause zwischen den Kanälen
                time.sleep(1) 
            except:
                pass
        
        save_seen(seen_ids)
        print(f"[*] Scan abgeschlossen. Warte 30s... (Zeit gelaufen: {int(time.time() - start_time)}s)")
        time.sleep(30) # DEIN INTERVALL: Hier kannst du auf 10-30 Sekunden gehen

if __name__ == "__main__":
    run_loop()
