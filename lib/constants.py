"""Physical constants for Earth distance calculations.

All distance calculations assume input coordinates are in decimal degrees
(WGS84 geographic coordinates: longitude, latitude).
"""
import math

# WGS84 ellipsoid mean radius
EARTH_RADIUS_KM = 6371.0
EARTH_RADIUS_MILES = 3958.8

# Degrees to distance conversion
# Derived from: (2 * π * R) / 360 degrees
#
# For latitude: 1 degree = 69.17 miles everywhere (constant)
# For longitude: 1 degree = 69.17 miles at equator, multiply by cos(lat) elsewhere
MILES_PER_DEGREE = (2 * math.pi * EARTH_RADIUS_MILES) / 360  # ≈ 69.17 miles
KM_PER_DEGREE = (2 * math.pi * EARTH_RADIUS_KM) / 360  # ≈ 111.32 km
