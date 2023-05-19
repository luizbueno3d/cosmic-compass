#astro.py


from flask import Flask, request, jsonify
import swisseph as swe

app = Flask(__name__)

@app.route('/astrology', methods=['POST'])
def astrology():
    #set up lahini ayanamsa:
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    # Get the user's input from the form
    birthdate = request.form.get('birthdate')
    birthtime = request.form.get('birthtime')
    birthplace = request.form.get('birthplace')
    interests = request.form.getlist('interests')

    # Convert the birthdate and birthtime to a Julian day number
    year, month, day = map(int, birthdate.split('-'))
    hour, minute = map(int, birthtime.split(':'))
    jd = swe.julday(year, month, day, hour + minute / 60)

    # Use the pyswisseph library to calculate the user's natal chart
    birthChart = calculateBirthChart(jd)

    # Use the pyswisseph library to calculate the current planetary transits
    planetaryTransits = calculatePlanetaryTransits()

    # Cross-check the birth chart with the planetary transits and the user's interests
    recommendedLocations = getRecommendedLocations(birthChart, planetaryTransits, interests)

    # Send the recommended locations back to the client
    return jsonify(recommendedLocations)

def calculateBirthChart(jd):
    # Use the pyswisseph library to calculate the birth chart
    birthChart = {}
    for body in [swe.SUN, swe.MOON, swe.MERCURY, swe.VENUS, swe.MARS, swe.JUPITER, swe.SATURN, swe.URANUS, swe.NEPTUNE, swe.PLUTO, swe.NORTH_NODE]:
        xx, ret = swe.calc_ut(jd, body)
        ayanamsa = swe.get_ayanamsa_ut(jd)
        xx[0] = (xx[0] - ayanamsa) % 360  # Subtract the ayanamsa from the longitude
        birthChart[body] = xx
    return birthChart

def calculatePlanetaryTransits(jd):
    # Use the pyswisseph library to calculate the planetary transits
    planetaryTransits = {}
    for body in [swe.SUN, swe.MOON, swe.MERCURY, swe.VENUS, swe.MARS, swe.JUPITER, swe.SATURN, swe.URANUS, swe.NEPTUNE, swe.PLUTO, swe.NORTH_NODE]:
        xx, ret = swe.calc_ut(jd, body)
        ayanamsa = swe.get_ayanamsa_ut(jd)
        xx[0] = (xx[0] - ayanamsa) % 360  # Subtract the ayanamsa from the longitude
        planetaryTransits[body] = xx
    return planetaryTransits

def getRecommendedLocations(birthChart, planetaryTransits, interests):
    recommendedLocations = []
    for location in allPossibleLocations:
        score = 0
        if 'career' in interests:
            # Add logic to calculate the score for career based on the 10th house and its ruler
            score += calculateCareerScore(birthChart, planetaryTransits, location)
        if 'love' in interests:
            # Add logic to calculate the score for love based on the 7th house and Venus
            score += calculateLoveScore(birthChart, planetaryTransits, location)
        if 'spiritual growth' in interests:
            # Add logic to calculate the score for spiritual growth based on the 9th house and Jupiter
            score += calculateSpiritualGrowthScore(birthChart, planetaryTransits, location)
        recommendedLocations.append((location, score))
    # Sort the locations by score in descending order
    recommendedLocations.sort(key=lambda x: x[1], reverse=True)
    return recommendedLocations

def calculateCareerScore(birthChart, planetaryTransits, location):
    # Calculate the 10th house cusp
    cusps, ascmc = swe_houses(jd, location['latitude'], location['longitude'], b'A')
    tenth_house_cusp = cusps[10]

    # Calculate the 10th house ruler
    tenth_house_ruler = get_house_ruler(tenth_house_cusp)

    # Calculate the score based on the strength and condition of the 10th house ruler
    score = get_planet_strength(birthChart[tenth_house_ruler], planetaryTransits[tenth_house_ruler])

    return score

def calculateLoveScore(birthChart, planetaryTransits, location):
    # Calculate the 7th house cusp
    cusps, ascmc = swe_houses(jd, location['latitude'], location['longitude'], b'A')
    seventh_house_cusp = cusps[7]

    # Calculate the 7th house ruler
    seventh_house_ruler = get_house_ruler(seventh_house_cusp)
        # Calculate the score based on the strength and condition of Venus
    score = get_planet_strength(birthChart[swe.VENUS], planetaryTransits[swe.VENUS])

    return score


def calculateSpiritualGrowthScore(birthChart, planetaryTransits, location):
    # Calculate the 9th house cusp
    cusps, ascmc = swe_houses(jd, location['latitude'], location['longitude'], b'A')
    ninth_house_cusp = cusps[9]

    # Calculate the 9th house ruler
    ninth_house_ruler = get_house_ruler(ninth_house_cusp)

    # Calculate the score based on the strength and condition of Jupiter
    score = get_planet_strength(birthChart[swe.JUPITER], planetaryTransits[swe.JUPITER])

    return score

# Helper function to get the house ruler
def get_house_ruler(cusp):
    # Add logic to determine the house ruler based on the cusp degree
    # This is just a placeholder - replace with the actual code
    return swe.SUN

# Helper function to calculate the planet strength
def get_planet_strength(natal_position, transit_position):
    # Add logic to determine the planet strength based on its natal and transit positions
    # You can consider factors like aspects, dignity, and other astrological concepts
    # This is just a placeholder - replace with the actual code
    strength = 0

    # Example: Check if the planet is in a favorable aspect with its natal position
    angle = abs(natal_position[0] - transit_position[0]) % 360
    if angle in [0, 60, 90, 120, 180]:  # These are some favorable aspects (conjunction, sextile, square, trine, opposition)
        strength += 1

    return strength

   

if __name__ == '__main__':
    app.run(debug=True)
