import os
import tls_client
import time
import json

# Lädt die Konfiguration aus dem Secret
raw_config = os.getenv("BOT_CONFIG")
try:
    CONFIG_LIST = json.loads(raw_config) if raw_config else []
except:
    print("[!] FEHLER: BOT_CONFIG Secret hat kein gültiges JSON-Format!")
    CONFIG_LIST = []

DB_FILE = "seen_items.txt"

def load_seen():
    if not os.path.exists(DB_FILE): return []
    with open(DB_FILE, "r") as f: return f.read().splitlines()

def save_seen(ids):
    with open(DB_FILE, "w") as f: f.write("\n".join(map(str, ids[-500:])))

def send_discord(webhook, item):
    import requests
    p = item.get('total_item_price')
    price = float(p.get('amount')) if isinstance(p, dict) else float(p or 0)
    item_url = item.get('url') or f"https://www.vinted.de/items/{item['id']}"
    
    # Bilder-Logik
    photos = item.get('photos', []) or ([item.get('photo')] if item.get('photo') else [])
    imgs = [img.get('url', '').replace("/medium/", "/full/") for img in photos if img.get('url')]

    data = {
        "username": "Vinted Sniper",
        "embeds": [{
            "title": f"🔥 {item.get('title')}",
            "url": item_url,
            "color": 0x09b1ba,
            "fields": [
                {"name": "💶 Preis", "value": f"**{price:.2f} €**", "inline": True},
                {"name": "🏷️ Marke", "value": item.get('brand_title', 'N/A'), "inline": True},
                {"name": "📏 Größe", "value": item.get('size_title', 'N/A'), "inline": True}
            ],
            "image": {"url": imgs[0] if imgs else ""},
            "footer": {"text": "24/7 GitHub Sniper"}
        }]
    }
    # Galerie-Trick für weitere Bilder
    for extra in imgs[1:4]:
        data["embeds"].append({"url": item_url, "image": {"url": extra}})
    
    requests.post(webhook, json=data)

def run():
    session = tls_client.Session(client_identifier="chrome_112")
    seen_ids = load_seen()
    print(f"[*] Datenbank geladen: {len(seen_ids)} IDs bekannt.")
    
    if not CONFIG_LIST:
        print("[!] Keine Konfiguration gefunden.")
        return

    for entry in CONFIG_LIST:
        webhook = entry.get("webhook")
        v_url = entry.get("url")
        if not webhook or not v_url: continue
        
        # URL Konvertierung für API
        api_url = v_url if "api/v2" in v_url else f"https://www.vinted.de/api/v2/catalog/items?{v_url.split('?')[-1]}&order=newest_first"
        
        try:
            res = session.get(api_url, headers={"User-Agent": "Mozilla/5.0"})
            if res.status_code == 200:
                items = res.json().get("items", [])
                print(f"[*] {len(items)} Artikel gefunden für {v_url[:30]}...")
                for item in items:
                    i_id = str(item["id"])
                    if i_id not in seen_ids:
                        if seen_ids: # Beim 1. Mal nur IDs speichern, nicht senden
                            send_discord(webhook, item)
                        seen_ids.append(i_id)
            else:
                print(f"[!] Fehler {res.status_code} bei Vinted Call.")
        except Exception as e:
            print(f"[!] Fehler: {e}")
    
    save_seen(seen_ids)

if __name__ == "__main__":
    run()
