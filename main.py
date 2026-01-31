import os
import tls_client
import time
import json
import random

# Lädt die Konfiguration aus dem Secret
raw_config = os.getenv("BOT_CONFIG")
try:
    CONFIG_LIST = json.loads(raw_config) if raw_config else []
except Exception as e:
    print(f"[!] JSON Fehler: {e}")
    CONFIG_LIST = []

DB_FILE = "seen_items.txt"

def load_seen():
    if not os.path.exists(DB_FILE): return []
    with open(DB_FILE, "r") as f: return f.read().splitlines()

def save_seen(ids):
    with open(DB_FILE, "w") as f: f.write("\n".join(map(str, ids[-2000:])))

def send_discord(webhook, item):
    import requests
    p = item.get('total_item_price')
    price = float(p.get('amount')) if isinstance(p, dict) else float(p or 0)
    
    # Galerie-Bilder sammeln
    photos = item.get('photos', []) or ([item.get('photo')] if item.get('photo') else [])
    imgs = [img.get('url', '').replace("/medium/", "/full/") for img in photos if img.get('url')]

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
            "image": {"url": imgs[0] if imgs else ""},
            "footer": {"text": "GitHub 24/7 Multi-Bot"}
        }]
    }
    # Bis zu 3 weitere Bilder anhängen
    for extra in imgs[1:4]:
        data["embeds"].append({"url": item.get('url'), "image": {"url": extra}})
    
    requests.post(webhook, json=data)

def run():
    # Wir nutzen verschiedene Browser-Identitäten, um Blöcke zu vermeiden
    identifiers = ["chrome_103", "chrome_112", "firefox_102", "opera_90"]
    session = tls_client.Session(client_identifier=random.choice(identifiers), random_tls_extension_order=True)
    
    seen_ids = load_seen()
    print(f"[*] Datenbank: {len(seen_ids)} IDs geladen.")

    if not CONFIG_LIST:
        print("[!] Keine BOT_CONFIG gefunden. Prüfe die Secrets!")
        return

    # Mische die Reihenfolge der Channels bei jedem Lauf
    random.shuffle(CONFIG_LIST)

    for entry in CONFIG_LIST:
        webhook = entry.get("webhook")
        v_url = entry.get("url")
        if not webhook or not v_url: continue
        
        api_url = v_url if "api/v2" in v_url else f"https://www.vinted.de/api/v2/catalog/items?{v_url.split('?')[-1]}&order=newest_first"
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "de-DE,de;q=0.9"
        }

        try:
            # Kurze Pause, um Vinted nicht zu spammen
            time.sleep(random.uniform(2.5, 5.0))
            
            res = session.get(api_url, headers=headers)
            if res.status_code == 200:
                items = res.json().get("items", [])
                new_found = 0
                for item in items:
                    i_id = str(item["id"])
                    if i_id not in seen_ids:
                        if seen_ids: # Nur senden, wenn DB nicht leer
                            send_discord(webhook, item)
                            new_found += 1
                        seen_ids.append(i_id)
                print(f"[✓] {new_found} neue Artikel für URL: {v_url[:40]}...")
            else:
                print(f"[!] Fehler {res.status_code} bei URL: {v_url[:40]}")
                if res.status_code == 403:
                    print("[!] Abgebrochen wegen 403 Block.")
                    break
        except Exception as e:
            print(f"[!] Fehler: {e}")
    
    save_seen(seen_ids)

if __name__ == "__main__":
    run()
