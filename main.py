import os
import tls_client
import time
import json

# Konfiguration aus GitHub Secrets laden
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
    p = item.get('total_item_price')
    price = float(p.get('amount')) if isinstance(p, dict) else float(p or 0)
    item_url = item.get('url') or f"https://www.vinted.de/items/{item['id']}"
    
    # Bilder-Logik
    photos = item.get('photos', []) or ([item.get('photo')] if item.get('photo') else [])
    imgs = [img.get('url', '').replace("/medium/", "/full/") for img in photos if img.get('url')]

    data = {
        "username": "GitHub Sniper",
        "embeds": [{
            "title": f"🔥 {item.get('title')}",
            "url": item_url,
            "color": 0x09b1ba,
            "fields": [
                {"name": "💶 Preis", "value": f"**{price:.2f} €**", "inline": True},
                {"name": "🏷️ Marke", "value": item.get('brand_title', 'N/A'), "inline": True},
                {"name": "✨ Zustand", "value": "Check Link", "inline": True}
            ],
            "image": {"url": imgs[0] if imgs else ""},
            "footer": {"text": "24/7 GitHub Sniper"}
        }]
    }
    import requests
    requests.post(webhook, json=data)

def run():
    session = tls_client.Session(client_identifier="chrome_112")
    seen_ids = load_seen()
    
    for webhook, v_url in CONFIG.items():
        if not webhook or not v_url: continue
        # URL Konvertierung
        api_url = v_url if "api/v2" in v_url else f"https://www.vinted.de/api/v2/catalog/items?{v_url.split('?')[-1]}&order=newest_first"
        
        try:
            res = session.get(api_url, headers={"User-Agent": "Mozilla/5.0"})
            if res.status_code == 200:
                items = res.json().get("items", [])
                for item in items:
                    i_id = str(item["id"])
                    if i_id not in seen_ids:
                        if seen_ids: send_discord(webhook, item)
                        seen_ids.append(i_id)
            time.sleep(2)
        except Exception as e: print(f"Error: {e}")
    
    save_seen(seen_ids)

if __name__ == "__main__":
    run()
