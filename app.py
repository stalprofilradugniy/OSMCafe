from flask import Flask, render_template, request
import requests
import math

app = Flask(__name__)

def haversine(lat1, lon1, lat2, lon2):
    """Рассчитывает расстояние между двумя точками на Земле (в метрах)"""
    R = 6371  # Радиус Земли в км
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c * 1000  # Конвертация в метры

def get_nearby_cafes(lat, lon, radius=1000):
    """Ищет кафе поблизости через Overpass API"""
    OVERPASS_URL = "https://overpass-api.de/api/interpreter"
    query = f"""
    [out:json];
    node["amenity"="cafe"](around:{radius},{lat},{lon});
    out body;
    """
    response = requests.post(OVERPASS_URL, data=query).json()
    
    cafes = []
    for element in response.get('elements', []):
        tags = element.get('tags', {})
        if 'name' in tags and 'rating' in tags:
            cafe_lat = element['lat']
            cafe_lon = element['lon']
            cafes.append({
                'name': tags['name'],
                'rating': float(tags['rating']),
                'distance': haversine(lat, lon, cafe_lat, cafe_lon),
                'address': tags.get('addr:street', '')
            })
    return sorted(cafes, key=lambda x: (-x['rating'], x['distance']))[:3]

@app.route('/', methods=['GET', 'POST'])
def index():
    """Основной маршрут: GET показывает интерфейс, POST обрабатывает координаты"""
    if request.method == 'POST':
        lat = request.form.get('lat', type=float)
        lon = request.form.get('lon', type=float)
        if lat and lon:
            cafes = get_nearby_cafes(lat, lon)
            return render_template('results.html', cafes=cafes)
        return render_template('error.html', message="Не удалось определить местоположение")
    return render_template('index.html')

if __name__ == '__main__':
    app.run(ssl_context='adhoc')  # HTTPS обязательно для геолокации в браузере
