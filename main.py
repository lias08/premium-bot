import os
import tls_client
import time
import json

# Konfiguration aus GitHub Secrets
CONFIG = {
    os.getenv("WEBHOOK_1"): os.getenv("https://www.vinted.de/catalog?search_text=sweater&catalog[]=1811&price_to=20.0&currency=EUR&size_ids[]=207&size_ids[]=208&size_ids[]=209&brand_ids[]=304&brand_ids[]=88&search_id=30738255657&order=newest_first")
}

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
    data = {
        "embeds": [{
            "title": f"✨ NEU: {item.get('title')}",
            "url": item.get('url'),
            "description": f"Preis: **{price:.2f} €**",
            "color": 0x09b1ba
        }]
    }
    requests.post(webhook, json=data)

def run():
    session = tls_client.Session(client_identifier="chrome_112")
    seen_ids = load_seen()
    print(f"[*] Datenbank geladen: {len(seen_ids)} IDs bekannt.")
    
    for webhook, v_url in CONFIG.items():
        if not webhook or not v_url:
            print("[!] FEHLER: Webhook oder URL fehlt in den Secrets!")
            continue
        
        # API URL Fix
        api_url = v_url if "api/v2" in v_url else f"https://www.vinted.de/api/v2/catalog/items?{v_url.split('?')[-1]}&order=newest_first"
        
        print(f"[*] Scanne Vinted...")
        try:
            res = session.get(api_url, headers={"User-Agent": "Mozilla/5.0"})
            print(f"[*] Status Code: {res.status_code}")
            
            if res.status_code == 200:
                items = res.json().get("items", [])
                print(f"[*] {len(items)} Artikel in der Liste gefunden.")
                
                new_count = 0
                for item in items:
                    i_id = str(item["id"])
                    if i_id not in seen_ids:
                        if len(seen_ids) > 0: # Verhindert Spam beim 1. Lauf
                            send_discord(webhook, item)
                            new_count += 1
                        seen_ids.append(i_id)
                
                print(f"[*] {new_count} neue Artikel an Discord gesendet.")
            else:
                print(f"[!] Vinted hat die Anfrage abgelehnt (Block).")
                
        except Exception as e:
            print(f"[!] Kritischer Fehler: {e}")
    
    save_seen(seen_ids)

if __name__ == "__main__":
    run()
