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

def get_condition(item):
    # Mapping für den Zustand
    status_id = str(item.get('status_id', ''))
    mapping = {
        "6": "Neu mit Etikett ✨",
        "1": "Neu ohne Etikett ✨",
        "2": "Sehr gut 👌",
        "3": "Gut 👍",
        "4": "Zufriedenstellend 🆗"
    }
    return mapping.get(status_id, "Gebraucht")

def send_discord(webhook, item):
    import requests
    
    # Preisberechnungen
    p = item.get('total_item_price')
    price_val = float(p.get('amount')) if isinstance(p, dict) else float(p or 0)
    # Schätzung: 0.70€ + 5% Gebühr + ca. 3.99€ Versand
    total_est = round(price_val + 0.70 + (price_val * 0.05) + 3.99, 2)
    
    item_id = item.get('id')
    item_url = item.get('url') or f"https://www.vinted.de/items/{item_id}"
    img = item.get('photo', {}).get('url', '').replace("/medium/", "/full/")
    
    data = {
        "username": "Vinted Sniper PRO",
        "embeds": [{
            "title": f"🔥 {item.get('title')}",
            "url": item_url,
            "color": 0x09b1ba,
            "fields": [
                {"name": "💶 Preis", "value": f"**{price_val:.2f} €**", "inline": True},
                {"name": "🚚 Gesamt ca.", "value": f"**{total_est:.2f} €**", "inline": True},
                {"name": "📏 Größe", "value": item.get('size_title', 'N/A'), "inline": True},
                {"name": "🏷️ Marke", "value": item.get('brand_title', 'Keine Marke'), "inline": True},
                {"name": "✨ Zustand", "value": get_condition(item), "inline": True},
                {"name": "⏰ Gefunden", "value": f"<t:{int(time.time())}:R>", "inline": True},
                {"name": "⚡ Aktionen", "value": f"[🛒 Kaufen](https://www.vinted.de/transaction/buy/new?item_id={item_id}) | [💬 Nachricht]({item_url}#message)", "inline": False}
            ],
            "image": {"url": img},
            "footer": {"text": "GitHub 24/7 Sniper • Multi-Channel"},
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        }]
    }
    requests.post(webhook, json=data)

def run():
    session = tls_client.Session(client_identifier="chrome_120", random_tls_extension_order=True)
    seen_ids = load_seen()
    
    if not CONFIG_LIST:
        print("[!] BOT_CONFIG Secret leer!")
        return

    for entry in CONFIG_LIST:
        webhook = entry.get("webhook")
        v_url = entry.get("url")
        if not webhook or not v_url: continue
        
        # API URL Umwandlung
        params = v_url.split('?')[-1]
        api_url = f"https://www.vinted.de/api/v2/catalog/items?{params}"
        if "order=" not in api_url: api_url += "&order=newest_first"

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json, text/plain, */*"
        }

        try:
            # Cookies holen
            session.get("https://www.vinted.de", headers=headers)
            time.sleep(1)
            
            res = session.get(api_url, headers=headers)
            if res.status_code == 200:
                items = res.json().get("items", [])
                for item in items:
                    i_id = str(item["id"])
                    if i_id not in seen_ids:
                        if seen_ids: # Nur senden, wenn es nicht der allererste Lauf ist
                            send_discord(webhook, item)
                        seen_ids.append(i_id)
            print(f"[*] Check erledigt für URL: {v_url[:30]}... Status: {res.status_code}")
        except Exception as e:
            print(f"[!] Fehler: {e}")
            
    save_seen(seen_ids)

if __name__ == "__main__":
    run()
