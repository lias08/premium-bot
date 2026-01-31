import os
import tls_client
import time
import json
import random

# Konfiguration laden
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
    with open(DB_FILE, "w") as f: f.write("\n".join(map(str, ids[-1000:])))

def send_discord(webhook, item):
    import requests
    p = item.get('total_item_price')
    price = float(p.get('amount')) if isinstance(p, dict) else float(p or 0)
    img = item.get('photo', {}).get('url', '').replace("/medium/", "/full/")
    
    data = {
        "username": "Vinted Sniper Elite",
        "embeds": [{
            "title": f"🔥 {item.get('title')}",
            "url": item.get('url'),
            "color": 0x09b1ba,
            "fields": [
                {"name": "💶 Preis", "value": f"**{price:.2f} €**", "inline": True},
                {"name": "🏷️ Marke", "value": item.get('brand_title', 'N/A'), "inline": True}
            ],
            "image": {"url": img},
            "footer": {"text": "GitHub 24/7 Sniper"}
        }]
    }
    requests.post(webhook, json=data)

def run():
    # TLS Client simuliert einen echten Browser (Chrome 120)
    session = tls_client.Session(client_identifier="chrome_120", random_tls_extension_order=True)
    seen_ids = load_seen()
    
    if not CONFIG_LIST:
        print("[!] FEHLER: BOT_CONFIG Secret leer oder ungültig!")
        return

    for entry in CONFIG_LIST:
        webhook = entry.get("webhook")
        v_url = entry.get("url")
        if not webhook or "http" not in v_url: continue
        
        # API URL Umwandlung
        params = v_url.split('?')[-1]
        api_url = f"https://www.vinted.de/api/v2/catalog/items?{params}"
        if "order=" not in api_url: api_url += "&order=newest_first"

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "de-DE,de;q=0.9",
            "Origin": "https://www.vinted.de",
            "Referer": "https://www.vinted.de/"
        }

        try:
            # Vor dem eigentlichen Call einmal die Hauptseite aufrufen (Cookie-Check)
            session.get("https://www.vinted.de", headers=headers)
            time.sleep(1)
            
            res = session.get(api_url, headers=headers)
            print(f"[*] Status {res.status_code} für {v_url[:40]}...")

            if res.status_code == 200:
                items = res.json().get("items", [])
                for item in items:
                    i_id = str(item["id"])
                    if i_id not in seen_ids:
                        if seen_ids: send_discord(webhook, item)
                        seen_ids.append(i_id)
            elif res.status_code == 403:
                print("[!] Vinted blockiert GitHub. Probiere es in 5 Min erneut.")
        except Exception as e:
            print(f"[!] Fehler: {e}")
            
    save_seen(seen_ids)

if __name__ == "__main__":
    run()
