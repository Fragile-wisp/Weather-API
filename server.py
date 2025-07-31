from flask import Flask, request, render_template, jsonify, abort
from flask_caching import Cache
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from datetime import datetime
from dotenv import load_dotenv
import os
import requests
import redis

load_dotenv()
app=Flask(__name__)

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

#Flask Limiter
limiter=Limiter(
    get_remote_address,
    app=app,
    storage_uri="redis://localhost:6379",
    storage_options={"socket_connect_timeout": 30},
    strategy="fixed-window",
)

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
        
#Error Handling
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500

#APP
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/weather")
@limiter.limit("10 per minute")
def Weather_Get():
    try:
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
    except:
        abort(400,description="Valid City/Country not entered")

if __name__=="__main__":
    app.run(debug=True)