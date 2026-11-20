import logging
import math
from typing import Tuple

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

EARTH_RADIUS_KM = 6371.0088
HAVERSINE_ROAD_FACTOR = 1.25
OSRM_ROUTE_URL = "https://router.project-osrm.org/route/v1/driving/{shop_lon},{shop_lat};{client_lon},{client_lat}?overview=false"
OSRM_TIMEOUT_SECONDS = 5

COURIER_BASE_FEE_UZS = 5000
COURIER_PER_KM_FEE_UZS = 10000


def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Ikki koordinata orasidagi to'g'ri chiziqli masofani (km) hisoblash."""
    phi1 = math.radians(float(lat1))
    phi2 = math.radians(float(lat2))
    d_phi = math.radians(float(lat2) - float(lat1))
    d_lambda = math.radians(float(lon2) - float(lon1))

    a = (
        math.sin(d_phi / 2.0) ** 2
        + math.cos(phi1) * math.cos(phi2) * (math.sin(d_lambda / 2.0) ** 2)
    )
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(max(0.0, 1.0 - a)))
    return EARTH_RADIUS_KM * c


def calculate_road_distance_km(client_lat: float, client_lon: float) -> Tuple[float, str]:
    """
    Do'kon (SHOP_LAT, SHOP_LON) dan mijoz lokatsiyasigacha avtomobil yo'li masofasini (km) hisoblash.
    1) Asosiy usul: OSRM driving route API (timeout: 5 soniya) -> (distance_km, 'osrm')
    2) Zaxira usul: Haversine * 1.25 -> (distance_km, 'haversine')
    """
    shop_lat = float(getattr(settings, 'SHOP_LAT', 41.338306))
    shop_lon = float(getattr(settings, 'SHOP_LON', 69.270389))
    c_lat = float(client_lat)
    c_lon = float(client_lon)

    url = OSRM_ROUTE_URL.format(
        shop_lon=shop_lon,
        shop_lat=shop_lat,
        client_lon=c_lon,
        client_lat=c_lat,
    )

    try:
        resp = requests.get(
            url,
            timeout=OSRM_TIMEOUT_SECONDS,
            headers={'User-Agent': 'MobiPrice/1.0 (+https://mobiprice.uz)'},
        )
        if resp.status_code == 200:
            payload = resp.json()
            routes = payload.get('routes') if isinstance(payload, dict) else None
            if routes and isinstance(routes, list):
                first_route = routes[0]
                if isinstance(first_route, dict) and first_route.get('distance') is not None:
                    distance_meters = float(first_route['distance'])
                    if distance_meters >= 0:
                        return round(distance_meters / 1000.0, 2), 'osrm'
    except Exception as exc:
        logger.warning("OSRM distance lookup failed, falling back to Haversine: %s", exc)

    straight_km = haversine_distance_km(shop_lat, shop_lon, c_lat, c_lon)
    estimated_road_km = round(straight_km * HAVERSINE_ROAD_FACTOR, 2)
    return estimated_road_km, 'haversine'


def calculate_courier_fee_uzs(distance_km: float) -> int:
    """
    Kuryer xizmati narxini hisoblash formulasi:
    5000 + round(distance_km * 10000)
    Masalan: 2.5 km -> 5000 + 25000 = 30 000 so'm.
    """
    km = max(0.0, float(distance_km))
    return COURIER_BASE_FEE_UZS + round(km * COURIER_PER_KM_FEE_UZS)


def build_google_maps_url(lat: float, lon: float) -> str:
    return f"https://www.google.com/maps/search/?api=1&query={lat},{lon}"


def build_yandex_maps_url(lat: float, lon: float) -> str:
    """Yandex Maps pt parametrida avval longitude, keyin latitude keladi."""
    return f"https://yandex.uz/maps/?pt={lon},{lat}&z=17&l=map"

