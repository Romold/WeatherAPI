from flask import Flask, jsonify
import requests
import time
import os

app = Flask(__name__)

CACHE = {} 
CACHE_TTL = 300 

def cache_get(key):

    row = CACHE.get(key)
    if not row:
        return None
    
    ts, val = row

    if time.time() - ts > CACHE_TTL:
        del CACHE[key]
        return None 
    
    return val 

def cache_set(key, value):

    CACHE[key] = (time.time(), value)

def geocode_city(city):

    key = f"geocode:{city.lower()}"
    cached = cache_get(key)

    if cached:
        return cached
    
    url = f"https://geocoding-api.open-meteo.com/v1/search?name={city}"
    resp = requests.get(url, timeout=5) 
    data = resp.json()

    results = data.get("results")

    if not results:
        return None 

    out = {
        "name" : results[0]['name'],
        "Country" : results[0]['country'],
        "longitude" : results[0]['longitude'],
        "latitude" : results[0]['latitude'],
    }

    cache_set(key, out)
    return out 

def fetch_current_weather(lat, lon):

    key = f"weather : {lat:.4f}:{lon:.4f}"
    cached = cache_get(key)
    
    if cached:
        return cached
    
    url = (
        "https://api.open-meteo.com/v1/forecast?latitude=52.52&longitude=13.41&current_weather=true&timezone=auto"
    )

    responses = requests.get(url, timeout=5) 
    data = responses.json()

    cw = data.get("current_weather")

    if not cw:
        return None
    
    out = {
        "temperature_c": cw.get("temperature"),
        "windspeed_m_s": cw.get("windspeed"),
        "winddirection_deg": cw.get("winddirection"),
        "weathercode": cw.get("weathercode"),
        "time": cw.get("time"), 
        "raw_response": data
    }

    cache_set(key, out)
    return out 

@app.route("/weather", methods=["GET"])
def weather_by_city(city):

    return jsonify({
        "Site" : "Welcome to this API"
    })

@app.route("/weather/<city>", methods=["GET"])
def weather_by_city(city):

    geo = geocode_city(city)
    if not geo:
        return jsonify({"error": "Could not find location"}), 404
    
    weather = fetch_current_weather(geo["latitude"], geo["longitude"])
    if not weather:
        return jsonify({"error": "Could not fetch weather"}), 404
    
    return jsonify({
        "location": {
            "name": geo["name"],
            # "country": geo["city"],
            "latitude": geo["latitude"],
            "longitude": geo["longitude"]
        },
        "current": weather
    })

if __name__ == "__main__":

    port = int(os.environ.get("PORT", 5000))
    app.run(host = "0.0.0.0", port = port, debug = True)