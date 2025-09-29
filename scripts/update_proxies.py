import requests
import json

def fetch_proxies():
    url = "https://proxylist.geonode.com/api/proxy-list?limit=500&page=1&sort_by=lastChecked&sort_type=desc"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            proxies = []
            for proxy in data.get('data', []):
                proxy_entry = {
                    "host": proxy.get('ip'),
                    "port": int(proxy.get('port')),
                    "protocol": proxy.get('protocols')[0].lower() if proxy.get('protocols') else 'http',
                    "country": proxy.get('country_code', 'UN'),
                    "response_time": 1000
                }
                proxies.append(proxy_entry)
            
            # Write to proxies.json
            with open('../proxies.json', 'w', encoding='utf-8') as f:
                json.dump(proxies, f, indent=4)
            print(f"Successfully updated proxies.json with {len(proxies)} proxies")
        else:
            print(f"Failed to fetch proxies. Status code: {response.status_code}")
    except Exception as e:
        print(f"Error occurred: {str(e)}")

if __name__ == "__main__":
    fetch_proxies()