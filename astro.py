#astro.py

from datetime import datetime
from flask import Flask, request, jsonify, render_template
import swisseph as swe
import traceback
import logging
import requests

logging.basicConfig(filename='astro.log', level=logging.DEBUG)

def get_lat_lng(place):
    response = requests.get(f"https://maps.googleapis.com/maps/api/geocode/json?address={place}&key='api_key_here'")
    resp_json_payload = response.json()
    lat = resp_json_payload['results'][0]['geometry']['location']['lat']
    lng = resp_json_payload['results'][0]['geometry']['location']['lng']
    return lat, lng

def getZodiacSign(longitude):
    signs = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo', 'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces']
    return signs[int((longitude + 30) % 360 / 30)]

def getSunSign(birthChart):
    # Calculate the position of the Sun in the birth chart
    sun_longitude = birthChart[swe.SUN][0]
    # Determine the zodiac sign based on the position of the Sun
    sun_sign = getZodiacSign(sun_longitude)
    # Return the sun sign
    return sun_sign

def getMoonSign(birthChart):
    # Calculate the position of the Moon in the birth chart
    moon_longitude = birthChart[swe.MOON][0]
    # Determine the zodiac sign based on the position of the Moon
    moon_sign = getZodiacSign(moon_longitude)
    # Return the moon sign
    return moon_sign

def getAscendant(birthChart):
    # Calculate the position of the eastern horizon (ascendant) in the birth chart
    ascendant_longitude = birthChart['ascendant'][0]
    # Determine the zodiac sign based on the position of the ascendant
    ascendant_sign = getZodiacSign(ascendant_longitude)
    # Return the ascendant
    return ascendant_sign


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


        birthChart = calculateBirthChart(jd, latitude, longitude)
        planetaryTransits = calculatePlanetaryTransits()

        recommendedLocations = getRecommendedLocations(birthChart, planetaryTransits, interests, destination_lat, destination_lng, destination, jd)
        # I added this to get the extra birth_latitude and birth_longitude. 24.May
        recommendedLocations[0]['birth_latitude'] = latitude
        recommendedLocations[0]['birth_longitude'] = longitude

        return render_template('results.html', results=recommendedLocations[0])

    except Exception as e:
        logging.error("Exception occurred", exc_info=True)
        return jsonify({'error': 'An error occurred: {}'.format(str(e))}), 500



def calculateBirthChart(jd, lat, lng):
    # Use the pyswisseph library to calculate the birth chart
    birthChart = {}
    for body in [swe.SUN, swe.MOON, swe.MERCURY, swe.VENUS, swe.MARS, swe.JUPITER, swe.SATURN, swe.URANUS, swe.NEPTUNE, swe.PLUTO]:
        xx, ret = swe.calc_ut(jd, body, swe.FLG_SIDEREAL)
        birthChart[body] = xx

    cusps, ascmc = swe.houses(jd, lat, lng, b'P')
    ascendant_longitude_tropical = ascmc[0]
    ayanamsa = swe.get_ayanamsa(jd)
    ascendant_longitude_sidereal = ascendant_longitude_tropical - ayanamsa
    birthChart['ascendant'] = [ascendant_longitude_sidereal, 0, 0]

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
        xx, ret = swe.calc_ut(jd, body, swe.FLG_SIDEREAL)
        planetaryTransits[body] = xx

    return planetaryTransits



def getRecommendedLocations(birthChart, planetaryTransits, interests, destination_lat, destination_lng, destination, jd):
    score = 0
    if 'career' in interests:
        score += calculateCareerScore(birthChart, planetaryTransits, destination_lat, destination_lng, jd)
    if 'love' in interests:
        score += calculateLoveScore(birthChart, planetaryTransits, destination_lat, destination_lng, jd)
    if 'spiritual growth' in interests:
        score += calculateSpiritualGrowthScore(birthChart, planetaryTransits, destination_lat, destination_lng, jd)

    # Get the sun sign, moon sign, and ascendant from the birth chart
    sun_sign = getSunSign(birthChart)
    moon_sign = getMoonSign(birthChart)
    ascendant = getAscendant(birthChart)

    # what is being returned in the website, today: 24.May.23

    return [{
        'destination': destination, 
        'score': score,
        'longitude': destination_lng,
        'latitude': destination_lat,
        'sun_sign': sun_sign,
        'moon_sign': moon_sign,
        'ascendant': ascendant
    }]

def calculateCareerScore(birthChart, planetaryTransits, destination_lat, destination_lng, jd):
    cusps, ascmc = swe.houses(jd, destination_lat, destination_lng, b'A')
    tenth_house_cusp = cusps[10]
    tenth_house_ruler = get_house_ruler(tenth_house_cusp)
    score = get_planet_strength(birthChart[tenth_house_ruler], planetaryTransits[tenth_house_ruler])
    return score

def calculateLoveScore(birthChart, planetaryTransits, destination_lat, destination_lng, jd):
    cusps, ascmc = swe.houses(jd, destination_lat, destination_lng, b'A')
    seventh_house_cusp = cusps[7]
    seventh_house_ruler = get_house_ruler(seventh_house_cusp)
    score = get_planet_strength(birthChart[swe.VENUS], planetaryTransits[swe.VENUS])
    return score

def calculateSpiritualGrowthScore(birthChart, planetaryTransits, destination_lat, destination_lng, jd):
    cusps, ascmc = swe.houses(jd, destination_lat, destination_lng, b'A')
    ninth_house_cusp = cusps[9]
    ninth_house_ruler = get_house_ruler(ninth_house_cusp)
    score = get_planet_strength(birthChart[swe.JUPITER], planetaryTransits[swe.JUPITER])
    return score

def get_house_ruler(cusp):
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
    sign = int(cusp / 30)
    signs = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo', 'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces']
    return rulers[signs[sign]]

def get_planet_strength(natal_position, transit_position):
    strength = 0
    angle = abs(natal_position[0] - transit_position[0]) % 360
    if angle in [0, 60, 90, 120, 180]:
        strength += 1
    return strength

if __name__ == '__main__':
    app.run(debug=True)

    