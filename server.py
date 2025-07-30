from flask import Flask, request, render_template, jsonify
from flask_caching import Cache
from datetime import datetime
from dotenv import load_dotenv
import os
import requests
import redis

load_dotenv()

#Redis connection
app=Flask(__name__)
app.config['CACHE_TYPE'] = 'redis'
app.config['CACHE_REDIS_HOST'] = 'localhost'
app.config['CACHE_REDIS_PORT'] = 6379
app.config['CACHE_REDIS_DB'] = 0
app.config['CACHE_REDIS_URL'] = 'redis://localhost:6379/0'
app.config['CACHE_DEFAULT_TIMEOUT'] = 300

cache=Cache(app)

r = redis.Redis(host='localhost', port=6379, decode_responses=True)


#Weather Data Function + caching it
@cache.memoize(timeout=120)
def Weather_Get_current(city, country):
    cache_key=f'{city},{country}'
    cached_weather=r.get(cache_key)
    if cached_weather:
        cached_weather=weather_data
        return jsonify(weather_data)
    else:
        current_time=datetime.now()
        format_current_time=current_time.strftime("%Y-%m-%dT%H:%M:%S")
        request_url = f"https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline/{city},{country}/{format_current_time}?key={os.getenv('API_KEY')}"
        weather_data=requests.get(request_url).json()
        cache.set(cache_key, weather_data, timeout=300)
        return weather_data
        
#APP
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/weather")
def Weather_Get():
    city=request.args.get("city")
    country=request.args.get("country")
    weather_data=Weather_Get_current(city,country)
    return render_template(
        "Weather_Got.html",
        city=request.args.get("city"),
        status=weather_data["description"],
        celsius_temp=round((5/9)*((weather_data["currentConditions"]["temp"])-32),1),
        celsius_feels_like=round((5/9)*((weather_data["currentConditions"]["feelslike"])-32),1),
    )

if __name__=="__main__":
    app.run(debug=True)