import os
import tls_client
import time
import json
import random
import sys

def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)

# Konfiguration laden
raw_config = os.getenv("BOT_CONFIG")
try:
    CONFIG_LIST = json.loads(raw_config) if raw_config else []
    log(f"✅ Konfiguration geladen: {len(CONFIG_LIST)} Channels.")
except Exception as e:
    log(f"❌ Fehler beim Laden der BOT_CONFIG: {e}")
    sys.exit(1)

DB_FILE = "seen_items.txt"

def load_seen():
    if not os.path.exists(DB_FILE): return []
    with open(DB_FILE, "r") as f: return f.read().splitlines()

def save_seen(ids):
    with open(DB_FILE, "w") as f: f.write("\n".join(map(str, ids[-1000:])))

def get_condition(item):
    status_id = str(item.get('status_id', ''))
    mapping = {"6": "Neu mit Etikett ✨", "1": "Neu ✨", "2": "Sehr gut 👌", "3": "Gut 👍", "4": "Zufriedenstellend 🆗"}
    return mapping.get(status_id, "Gebraucht")

def send_discord(webhook, item):
    import requests
    try:
        p = item.get('total_item_price')
        price_val = float(p.get('amount')) if isinstance(p, dict) else float(p or 0)
        total_est = round(price_val + 0.70 + (price_val * 0.05) + 3.99, 2)
        
        item_id = item.get('id')
        item_url = item.get('url') or f"https://www.vinted.de/items/{item_id}"
        img = item.get('photo', {}).get('url', '').replace("/medium/", "/full/")
        
        data = {
            "username": "Vinted Sniper Elite",
            "embeds": [{
                "title": f"🔥 {item.get('title')}",
                "url": item_url,
                "color": 0x09b1ba,
                "fields": [
                    {"name": "💶 Preis", "value": f"**{price_val:.2f} €**", "inline": True},
                    {"name": "🚚 Gesamt ca.", "value": f"**{total_est:.2f} €**", "inline": True},
                    {"name": "📏 Größe", "value": item.get('size_title', 'N/A'), "inline": True},
                    {"name": "🏷️ Marke", "value": item.get('brand_title', 'Keine'), "inline": True},
                    {"name": "✨ Zustand", "value": get_condition(item), "inline": True},
                    {"name": "⏰ Gefunden", "value": f"<t:{int(time.time())}:R>", "inline": True},
                    {"name": "⚡ Aktionen", "value": f"[🛒 Kaufen](https://www.vinted.de/transaction/buy/new?item_id={item_id}) | [💬 Nachricht]({item_url}#message)", "inline": False}
                ],
                "image": {"url": img},
                "footer": {"text": "24/7 Hacker-Loop ACTIVE"}
            }]
        }
        requests.post(webhook, json=data, timeout=10)
    except Exception as e:
        log(f"❌ Discord Fehler: {e}")

def run_loop():
    session = tls_client.Session(client_identifier="chrome_120", random_tls_extension_order=True)
    seen_ids = load_seen()
    start_time = time.time()
    
    log("🚀 Hacker-Loop gestartet. Warte auf neue Artikel...")

    while True:
        # Loop-Sicherung: Nach 5,5 Stunden beenden für sauberen GitHub-Neustart
        if time.time() - start_time > 19800:
            log("⏳ Zeitlimit erreicht. Starte demnächst neu...")
            break

        random.shuffle(CONFIG_LIST) # Mustererkennung vermeiden

        for entry in CONFIG_LIST:
            webhook = entry.get("webhook")
            v_url = entry.get("url")
            if not webhook or not v_url: continue
            
            params = v_url.split('?')[-1]
            api_url = f"https://www.vinted.de/api/v2/catalog/items?{params}&order=newest_first"

            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept": "application/json, text/plain, */*",
                "Referer": "https://www.vinted.de/"
            }

            try:
                res = session.get(api_url, headers=headers)
                if res.status_code == 200:
                    items = res.json().get("items", [])
                    new_count = 0
                    for item in items:
                        i_id = str(item["id"])
                        if i_id not in seen_ids:
                            if len(seen_ids) > 0:
                                send_discord(webhook, item)
                                new_count += 1
                            seen_ids.append(i_id)
                    if new_count > 0:
                        log(f"✨ {new_count} neue Artikel gefunden!")
                elif res.status_code == 403:
                    log("⚠️ 403 Block! Pausiere kurz...")
                    time.sleep(60)
            except Exception as e:
                log(f"❌ Fehler bei Scan: {e}")
            
            time.sleep(random.uniform(2, 5)) # Schutz vor Ban

        save_seen(seen_ids)
        # Intervall zwischen kompletten Scans
        time.sleep(30) 

if __name__ == "__main__":
    run_loop()
