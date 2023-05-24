#astro.py

from datetime import datetime
from flask import Flask, request, jsonify, render_template
import swisseph as swe
import traceback
import logging
import requests

logging.basicConfig(filename='astro.log', level=logging.DEBUG)

def get_lat_lng(place):
    response = requests.get(f"https://maps.googleapis.com/maps/api/geocode/json?address={place}&key=AIzaSyA1CARWnoYVvJlsglKrBDFgyBuiWXyXjCc")
    resp_json_payload = response.json()
    lat = resp_json_payload['results'][0]['geometry']['location']['lat']
    lng = resp_json_payload['results'][0]['geometry']['location']['lng']
    return lat, lng

app = Flask(__name__, static_url_path='/static')

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/astrology', methods=['POST'])
def astrology():
    try:
        swe.set_sid_mode(swe.SIDM_LAHIRI)
        birthdate = request.form.get('birthdate')
        birthtime = request.form.get('birthtime')
        birthplace = request.form.get('birthplace')
        latitude, longitude = get_lat_lng(birthplace)
        interests = request.form.getlist('interests')
        destination = request.form.get('destination')
        destination_lat, destination_lng = get_lat_lng(destination)

        year, month, day = map(int, birthdate.split('-'))
        hour, minute = map(int, birthtime.split(':'))
        jd = swe.julday(year, month, day, hour + minute / 60)

        birthChart = calculateBirthChart(jd)
        planetaryTransits = calculatePlanetaryTransits()

        recommendedLocations = getRecommendedLocations(birthChart, planetaryTransits, interests, destination_lat, destination_lng)

        return jsonify(recommendedLocations)

    except Exception as e:
        logging.error("Exception occurred", exc_info=True)
        return jsonify({'error': 'An error occurred: {}'.format(str(e))}), 500

def calculateBirthChart(jd):
    # Use the pyswisseph library to calculate the birth chart
    birthChart = {}
    for body in [swe.SUN, swe.MOON, swe.MERCURY, swe.VENUS, swe.MARS, swe.JUPITER, swe.SATURN, swe.URANUS, swe.NEPTUNE, swe.PLUTO]:
        xx, ret = swe.calc_ut(jd, body)
        ayanamsa = swe.get_ayanamsa_ut(jd)
        xx = list(xx)  # Convert tuple to list
        xx[0] = (xx[0] - ayanamsa) % 360  # Subtract the ayanamsa from the longitude
        xx = tuple(xx)  # Convert list back to tuple if necessary
        birthChart[body] = xx
    return birthChart

def calculatePlanetaryTransits():
    planetaryTransits = {}
    utc_now = datetime.utcnow()
    year = utc_now.year
    month = utc_now.month
    day = utc_now.day
    hour = utc_now.hour + utc_now.minute / 60
    jd = swe.julday(year, month, day, hour)

    for body in [swe.SUN, swe.MOON, swe.MERCURY, swe.VENUS, swe.MARS, swe.JUPITER, swe.SATURN, swe.URANUS, swe.NEPTUNE, swe.PLUTO]:
        xx, ret = swe.calc_ut(jd, body)
        ayanamsa = swe.get_ayanamsa_ut(jd)
        xx = list(xx)
        xx[0] = (xx[0] - ayanamsa) % 360
        xx = tuple(xx)
        planetaryTransits[body] = xx
    return planetaryTransits

    # Get the current UTC time
    utc_now = datetime.utcnow()

    # Convert the datetime object to the correct format
    year = utc_now.year
    month = utc_now.month
    day = utc_now.day
    hour = utc_now.hour + utc_now.minute / 60

    # Convert the datetime to a Julian day number
    jd = swe.julday(year, month, day, hour)

    for body in [swe.SUN, swe.MOON, swe.MERCURY, swe.VENUS, swe.MARS, swe.JUPITER, swe.SATURN, swe.URANUS, swe.NEPTUNE, swe.PLUTO]:
        xx, ret = swe.calc_ut(jd, body)
        ayanamsa = swe.get_ayanamsa_ut(jd)
        xx = list(xx)  # Convert tuple to list
        xx[0] = (xx[0] - ayanamsa) % 360  # Subtract the ayanamsa from the longitude
        xx = tuple(xx)  # Convert list back to tuple if necessary
        planetaryTransits[body] = xx
    return planetaryTransits


def getRecommendedLocations(birthChart, planetaryTransits, interests, destination_lat, destination_lng):
    score = 0
    if 'career' in interests:
        # Add logic to calculate the score for career based on the 10th house and its ruler
        score += calculateCareerScore(birthChart, planetaryTransits, destination_lat, destination_lng)
    if 'love' in interests:
        # Add logic to calculate the score for love based on the 7th house and Venus
        score += calculateLoveScore(birthChart, planetaryTransits, destination_lat, destination_lng)
    if 'spiritual growth' in interests:
        # Add logic to calculate the score for spiritual growth based on the 9th house and Jupiter
        score += calculateSpiritualGrowthScore(birthChart, planetaryTransits, destination_lat, destination_lng)
    return [{'destination': destination, 'score': score}]


def calculateCareerScore(birthChart, planetaryTransits, location):
    # Calculate the 10th house cusp
    cusps, ascmc = swe.houses(jd, location['latitude'], location['longitude'], b'A')
    tenth_house_cusp = cusps[10]

    # Calculate the 10th house ruler
    tenth_house_ruler = get_house_ruler(tenth_house_cusp)

    # Calculate the score based on the strength and condition of the 10th house ruler
    score = get_planet_strength(birthChart[tenth_house_ruler], planetaryTransits[tenth_house_ruler])

    return score

def calculateLoveScore(birthChart, planetaryTransits, location):
    # Calculate the 7th house cusp
    cusps, ascmc = swe.houses(jd, location['latitude'], location['longitude'], b'A')
    seventh_house_cusp = cusps[7]

    # Calculate the 7th house ruler
    seventh_house_ruler = get_house_ruler(seventh_house_cusp)

    # Calculate the score based on the strength and condition of Venus
    score = get_planet_strength(birthChart[swe.VENUS], planetaryTransits[swe.VENUS])

    return score

def calculateSpiritualGrowthScore(birthChart, planetaryTransits, location):
    # Calculate the 9th house cusp
    cusps, ascmc = swe.houses(jd, location['latitude'], location['longitude'], b'A')
    ninth_house_cusp = cusps[9]

    # Calculate the 9th house ruler
    ninth_house_ruler = get_house_ruler(ninth_house_cusp)

    # Calculate the score based on the strength and condition of Jupiter
    score = get_planet_strength(birthChart[swe.JUPITER], planetaryTransits[swe.JUPITER])

    return score

# Helper function to get the house ruler
def get_house_ruler(cusp):
    # In Vedic astrology, each sign is ruled by a planet
    # Here is a simple mapping from sign to ruler
    rulers = {
        'Aries': swe.MARS,
        'Taurus': swe.VENUS,
        'Gemini': swe.MERCURY,
        'Cancer': swe.MOON,
        'Leo': swe.SUN,
        'Virgo': swe.MERCURY,
        'Libra': swe.VENUS,
        'Scorpio': swe.MARS,
        'Sagittarius': swe.JUPITER,
        'Capricorn': swe.SATURN,
        'Aquarius': swe.SATURN,
        'Pisces': swe.JUPITER
    }
    # Convert the cusp degree to a sign
    sign = int(cusp / 30)
    signs = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo', 'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces']
    # Return the ruler of the sign
    return rulers[signs[sign]]

# Helper function to calculate the planet strength
def get_planet_strength(natal_position, transit_position):
    # Add logic to determine the planet strength based on its natal and transit positions
    # You can consider factors like aspects, dignity, and other astrological concepts
    # aspects, dignity, and other astrological concepts
    strength = 0

    # Example: Check if the planet is in a favorable aspect with its natal position
    angle = abs(natal_position[0] - transit_position[0]) % 360
    if angle in [0, 60, 90, 120, 180]:  # These are some favorable aspects (conjunction, sextile, square, trine, opposition)
        strength += 1

    return strength

if __name__ == '__main__':
    app.run(debug=True)

