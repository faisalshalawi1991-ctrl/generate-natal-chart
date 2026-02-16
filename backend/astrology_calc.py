#!/usr/bin/env python3
"""
Astrology calculation CLI script.

Accepts birth data (name, date, time, latitude, longitude, timezone) via command-line
arguments and generates an astrological birth chart using Kerykeion in offline mode.
"""

import argparse
import sys
import os
import json
from pathlib import Path
from datetime import datetime, timezone

from kerykeion import AstrologicalSubjectFactory, NatalAspects, KerykeionException
import swisseph as swe
import kerykeion


# Essential dignities lookup table for traditional planets (Sun through Saturn)
# Uses 3-letter sign abbreviations matching Kerykeion output format
DIGNITIES = {
    'Sun': {'domicile': ['Leo'], 'exaltation': ['Ari'], 'detriment': ['Aqu'], 'fall': ['Lib']},
    'Moon': {'domicile': ['Can'], 'exaltation': ['Tau'], 'detriment': ['Cap'], 'fall': ['Sco']},
    'Mercury': {'domicile': ['Gem', 'Vir'], 'exaltation': ['Vir'], 'detriment': ['Sag', 'Pis'], 'fall': ['Pis']},
    'Venus': {'domicile': ['Tau', 'Lib'], 'exaltation': ['Pis'], 'detriment': ['Sco', 'Ari'], 'fall': ['Vir']},
    'Mars': {'domicile': ['Ari', 'Sco'], 'exaltation': ['Cap'], 'detriment': ['Lib', 'Tau'], 'fall': ['Can']},
    'Jupiter': {'domicile': ['Sag', 'Pis'], 'exaltation': ['Can'], 'detriment': ['Gem', 'Vir'], 'fall': ['Cap']},
    'Saturn': {'domicile': ['Cap', 'Aqu'], 'exaltation': ['Lib'], 'detriment': ['Can', 'Leo'], 'fall': ['Ari']},
}

# Major fixed stars for conjunction detection
# 13 historically significant stars (magnitude 1-2, used in classical astrology)
# Names must be lowercase for Swiss Ephemeris fixstar2_ut
MAJOR_STARS = [
    ('aldebaran', 'Aldebaran'),    # Eye of the Bull, ~9 Gem
    ('rigel', 'Rigel'),            # Foot of Orion, ~16 Gem
    ('sirius', 'Sirius'),          # Dog Star, brightest, ~14 Can
    ('castor', 'Castor'),          # Alpha Geminorum, ~20 Can
    ('pollux', 'Pollux'),          # Beta Geminorum, ~23 Can
    ('regulus', 'Regulus'),        # Heart of the Lion, ~0 Vir
    ('spica', 'Spica'),            # Wheat Ear of Virgo, ~24 Lib
    ('arcturus', 'Arcturus'),      # Bear Watcher, ~24 Lib
    ('antares', 'Antares'),        # Heart of Scorpion, ~9 Sag
    ('vega', 'Vega'),              # Alpha Lyrae, ~15 Cap
    ('altair', 'Altair'),          # Alpha Aquilae, ~1 Aqu
    ('fomalhaut', 'Fomalhaut'),    # Royal Star, ~3 Pis
    ('algol', 'Algol'),            # Demon Star, ~26 Tau
]

# Element mapping for zodiac signs
# Keys match Kerykeion's sign format (3-letter abbreviations)
ELEMENT_MAP = {
    'Ari': 'Fire', 'Leo': 'Fire', 'Sag': 'Fire',
    'Tau': 'Earth', 'Vir': 'Earth', 'Cap': 'Earth',
    'Gem': 'Air', 'Lib': 'Air', 'Aqu': 'Air',
    'Can': 'Water', 'Sco': 'Water', 'Pis': 'Water',
}

# Modality mapping for zodiac signs
# Keys match Kerykeion's sign format (3-letter abbreviations)
MODALITY_MAP = {
    'Ari': 'Cardinal', 'Can': 'Cardinal', 'Lib': 'Cardinal', 'Cap': 'Cardinal',
    'Tau': 'Fixed', 'Leo': 'Fixed', 'Sco': 'Fixed', 'Aqu': 'Fixed',
    'Gem': 'Mutable', 'Vir': 'Mutable', 'Sag': 'Mutable', 'Pis': 'Mutable',
}


def valid_date(s):
    """
    Validate date string in YYYY-MM-DD format.

    Args:
        s: Date string to validate

    Returns:
        datetime object if valid

    Raises:
        argparse.ArgumentTypeError: If date format is invalid
    """
    try:
        dt = datetime.strptime(s, "%Y-%m-%d")
        # Validate year range: 1800 to current year (Swiss Ephemeris supports historical dates)
        current_year = datetime.now().year
        if dt.year < 1800 or dt.year > current_year:
            raise argparse.ArgumentTypeError(f"Year must be between 1800 and {current_year}")
        return dt
    except ValueError as e:
        raise argparse.ArgumentTypeError(f"Invalid date format '{s}'. Use YYYY-MM-DD. Error: {e}")


def valid_time(s):
    """
    Validate time string in HH:MM 24-hour format.

    Args:
        s: Time string to validate

    Returns:
        datetime object if valid

    Raises:
        argparse.ArgumentTypeError: If time format is invalid
    """
    try:
        return datetime.strptime(s, "%H:%M")
    except ValueError as e:
        raise argparse.ArgumentTypeError(f"Invalid time format '{s}'. Use HH:MM (24-hour). Error: {e}")


def valid_latitude(s):
    """
    Validate latitude value is within -90 to 90 degrees range.

    Args:
        s: Latitude string to validate

    Returns:
        float latitude value if valid

    Raises:
        argparse.ArgumentTypeError: If latitude is out of range
    """
    try:
        lat = float(s)
        if not -90 <= lat <= 90:
            raise ValueError(f"Latitude must be between -90 and 90, got {lat}")
        return lat
    except ValueError as e:
        raise argparse.ArgumentTypeError(f"Invalid latitude '{s}': {e}")


def valid_longitude(s):
    """
    Validate longitude value is within -180 to 180 degrees range.

    Args:
        s: Longitude string to validate

    Returns:
        float longitude value if valid

    Raises:
        argparse.ArgumentTypeError: If longitude is out of range
    """
    try:
        lng = float(s)
        if not -180 <= lng <= 180:
            raise ValueError(f"Longitude must be between -180 and 180, got {lng}")
        return lng
    except ValueError as e:
        raise argparse.ArgumentTypeError(f"Invalid longitude '{s}': {e}")


def position_to_sign_degree(position):
    """
    Convert absolute ecliptic longitude (0-360°) to zodiac sign and degree within sign.

    Args:
        position: Absolute ecliptic longitude in degrees (0-360)

    Returns:
        tuple: (sign_abbreviation, degree_within_sign)
    """
    # Sign abbreviations matching Kerykeion's 3-letter format
    signs = ['Ari', 'Tau', 'Gem', 'Can', 'Leo', 'Vir',
             'Lib', 'Sco', 'Sag', 'Cap', 'Aqu', 'Pis']
    sign_index = int(position // 30) % 12
    degree = position % 30
    return signs[sign_index], degree


def get_planet_dignities(planet_name, planet_sign):
    """
    Determine essential dignities for a planet based on its sign placement.

    Args:
        planet_name: Name of the planet (e.g., 'Sun', 'Moon', 'Mercury')
        planet_sign: Sign abbreviation (e.g., 'Ari', 'Tau', 'Gem')

    Returns:
        list: List of dignity strings (e.g., ['Domicile'], ['Exaltation'], ['Peregrine'])
    """
    if planet_name not in DIGNITIES:
        return []  # Not a traditional planet

    dignities = []
    planet_data = DIGNITIES[planet_name]

    if planet_sign in planet_data['domicile']:
        dignities.append('Domicile')
    if planet_sign in planet_data['exaltation']:
        dignities.append('Exaltation')
    if planet_sign in planet_data['detriment']:
        dignities.append('Detriment')
    if planet_sign in planet_data['fall']:
        dignities.append('Fall')

    # If no dignity found, planet is peregrine
    if not dignities:
        dignities.append('Peregrine')

    return dignities


def build_chart_json(subject, args):
    """
    Build comprehensive JSON-serializable dictionary from AstrologicalSubject.

    Extracts all astrological calculations into a structured format including:
    meta, planets, houses, angles, aspects, asteroids, fixed_stars, arabic_parts,
    dignities, and distributions.

    Args:
        subject: AstrologicalSubject instance with calculated chart data
        args: Parsed command-line arguments containing birth data

    Returns:
        dict: Comprehensive chart data structure
    """
    # META SECTION
    meta = {
        "name": args.name,
        "birth_date": args.date.strftime("%Y-%m-%d"),
        "birth_time": args.time.strftime("%H:%M"),
        "location": {
            "city": getattr(subject, 'city', None),
            "nation": getattr(subject, 'nation', None),
            "latitude": subject.lat,
            "longitude": subject.lng,
            "timezone": subject.tz_str
        },
        "house_system": "Placidus",
        "chart_type": None,  # Will be determined below
        "generated_at": datetime.now(timezone.utc).isoformat()
    }

    # PLANETS SECTION - all 10 main planets
    planets_list = [
        ('Sun', subject.sun), ('Moon', subject.moon),
        ('Mercury', subject.mercury), ('Venus', subject.venus),
        ('Mars', subject.mars), ('Jupiter', subject.jupiter),
        ('Saturn', subject.saturn), ('Uranus', subject.uranus),
        ('Neptune', subject.neptune), ('Pluto', subject.pluto),
    ]

    planets = []
    for name, planet in planets_list:
        planets.append({
            "name": name,
            "sign": planet.sign,
            "degree": planet.position % 30,
            "abs_position": planet.abs_pos,
            "house": str(planet.house),
            "retrograde": getattr(planet, 'retrograde', False)
        })

    # HOUSES SECTION - all 12 house cusps
    houses_list = [
        subject.first_house, subject.second_house, subject.third_house,
        subject.fourth_house, subject.fifth_house, subject.sixth_house,
        subject.seventh_house, subject.eighth_house, subject.ninth_house,
        subject.tenth_house, subject.eleventh_house, subject.twelfth_house,
    ]

    houses = []
    for i, house in enumerate(houses_list, 1):
        houses.append({
            "number": i,
            "sign": house.sign,
            "degree": house.position % 30
        })

    # ANGLES SECTION
    angles_list = [
        ('ASC', subject.ascendant),
        ('MC', subject.medium_coeli),
        ('DSC', subject.descendant),
        ('IC', subject.imum_coeli),
    ]

    angles = []
    for name, angle in angles_list:
        angles.append({
            "name": name,
            "sign": angle.sign,
            "degree": angle.position % 30,
            "abs_position": angle.abs_pos
        })

    # ASPECTS SECTION - major aspects between 10 main planets
    natal_aspects = NatalAspects(subject)
    major_types = ['conjunction', 'opposition', 'trine', 'square', 'sextile']
    planet_names = ['Sun', 'Moon', 'Mercury', 'Venus', 'Mars', 'Jupiter', 'Saturn', 'Uranus', 'Neptune', 'Pluto']

    filtered_aspects = [
        asp for asp in natal_aspects.all_aspects
        if asp.aspect in major_types
        and asp.p1_name in planet_names
        and asp.p2_name in planet_names
    ]

    aspects = []
    for asp in filtered_aspects:
        movement = asp.aspect_movement if hasattr(asp, 'aspect_movement') else ''
        aspects.append({
            "planet1": asp.p1_name,
            "planet2": asp.p2_name,
            "type": asp.aspect,
            "orb": asp.orbit,
            "movement": movement
        })

    # ASTEROIDS SECTION
    asteroid_attrs = [
        ('Chiron', 'chiron'),
        ('Mean Lilith', 'mean_lilith'),
        ('True Lilith', 'true_lilith'),
        ('Ceres', 'ceres'),
        ('Pallas', 'pallas'),
        ('Juno', 'juno'),
        ('Vesta', 'vesta'),
    ]

    asteroids = []
    for name, attr in asteroid_attrs:
        body = getattr(subject, attr, None)
        if body is not None:
            asteroids.append({
                "name": name,
                "sign": body.sign,
                "degree": body.position % 30,
                "house": str(body.house),
                "retrograde": getattr(body, 'retrograde', False)
            })

    # ARABIC PARTS SECTION - Determine day/night chart and calculate parts
    sun_house_str = str(subject.sun.house)
    house_names = {
        'First_House': 1, 'Second_House': 2, 'Third_House': 3, 'Fourth_House': 4,
        'Fifth_House': 5, 'Sixth_House': 6, 'Seventh_House': 7, 'Eighth_House': 8,
        'Ninth_House': 9, 'Tenth_House': 10, 'Eleventh_House': 11, 'Twelfth_House': 12
    }
    sun_house = house_names.get(sun_house_str, int(sun_house_str) if sun_house_str.isdigit() else 1)
    is_day_chart = 7 <= sun_house <= 12

    # Update meta with chart type
    meta["chart_type"] = "Day" if is_day_chart else "Night"

    asc_pos = subject.ascendant.position
    sun_pos = subject.sun.position
    moon_pos = subject.moon.position

    # Calculate Part of Fortune
    if is_day_chart:
        fortune_pos = (asc_pos + moon_pos - sun_pos) % 360
    else:
        fortune_pos = (asc_pos + sun_pos - moon_pos) % 360

    # Calculate Part of Spirit
    if is_day_chart:
        spirit_pos = (asc_pos + sun_pos - moon_pos) % 360
    else:
        spirit_pos = (asc_pos + moon_pos - sun_pos) % 360

    fortune_sign, fortune_degree = position_to_sign_degree(fortune_pos)
    spirit_sign, spirit_degree = position_to_sign_degree(spirit_pos)

    arabic_parts = {
        "part_of_fortune": {"sign": fortune_sign, "degree": fortune_degree},
        "part_of_spirit": {"sign": spirit_sign, "degree": spirit_degree}
    }

    # DIGNITIES SECTION - traditional planets only
    traditional_planets = [
        ('Sun', subject.sun),
        ('Moon', subject.moon),
        ('Mercury', subject.mercury),
        ('Venus', subject.venus),
        ('Mars', subject.mars),
        ('Jupiter', subject.jupiter),
        ('Saturn', subject.saturn),
    ]

    dignities = []
    for name, planet in traditional_planets:
        dignity_status = get_planet_dignities(name, planet.sign)
        dignities.append({
            "planet": name,
            "sign": planet.sign,
            "status": dignity_status
        })

    # FIXED STARS SECTION
    # Set Swiss Ephemeris path
    kerykeion_path = Path(kerykeion.__file__).parent
    sweph_path = kerykeion_path / 'sweph'
    swe.set_ephe_path(str(sweph_path))

    # Calculate Julian day
    jd = swe.julday(args.date.year, args.date.month, args.date.day,
                    args.time.hour + args.time.minute / 60.0)

    # Build points to check: all 10 planets + 4 angles
    points_to_check = [(name, p.abs_pos) for name, p in planets_list] + \
                      [(name, a.abs_pos) for name, a in angles_list]

    fixed_stars = []
    for star_lookup, star_display in MAJOR_STARS:
        try:
            star_data, returned_name, ret_flag = swe.fixstar2_ut(star_lookup, jd, 0)
            star_long = star_data[0]

            for point_name, point_long in points_to_check:
                diff = abs(point_long - star_long)
                if diff > 180:
                    diff = 360 - diff

                if diff <= 1.0:
                    fixed_stars.append({
                        "star": star_display,
                        "conjunct_body": point_name,
                        "orb": diff
                    })
        except Exception:
            # Silently skip stars that can't be calculated
            pass

    # DISTRIBUTIONS SECTION - Elements and Modalities
    # Collect placements: 10 planets + ASC (11 total)
    placements = [(name, p) for name, p in planets_list] + [('ASC', subject.ascendant)]

    # Element distribution
    element_count = {'Fire': 0, 'Earth': 0, 'Air': 0, 'Water': 0}
    element_planets = {'Fire': [], 'Earth': [], 'Air': [], 'Water': []}

    for name, body in placements:
        element = ELEMENT_MAP.get(body.sign)
        if element:
            element_count[element] += 1
            element_planets[element].append(name)

    total_placements = sum(element_count.values())

    elements = {}
    for element in ['Fire', 'Earth', 'Air', 'Water']:
        count = element_count[element]
        percentage = (count / total_placements * 100) if total_placements > 0 else 0
        elements[element] = {
            "count": count,
            "percentage": round(percentage, 1),
            "planets": element_planets[element]
        }

    # Modality distribution
    modality_count = {'Cardinal': 0, 'Fixed': 0, 'Mutable': 0}
    modality_planets = {'Cardinal': [], 'Fixed': [], 'Mutable': []}

    for name, body in placements:
        modality = MODALITY_MAP.get(body.sign)
        if modality:
            modality_count[modality] += 1
            modality_planets[modality].append(name)

    modalities = {}
    for modality in ['Cardinal', 'Fixed', 'Mutable']:
        count = modality_count[modality]
        percentage = (count / total_placements * 100) if total_placements > 0 else 0
        modalities[modality] = {
            "count": count,
            "percentage": round(percentage, 1),
            "planets": modality_planets[modality]
        }

    distributions = {
        "elements": elements,
        "modalities": modalities
    }

    # Assemble final dictionary
    return {
        "meta": meta,
        "planets": planets,
        "houses": houses,
        "angles": angles,
        "aspects": aspects,
        "asteroids": asteroids,
        "fixed_stars": fixed_stars,
        "arabic_parts": arabic_parts,
        "dignities": dignities,
        "distributions": distributions
    }


def main():
    """
    Main entry point for the astrology calculation CLI.

    Returns:
        0 on success, 1 on error
    """
    parser = argparse.ArgumentParser(
        description="Generate astrological birth chart data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Online mode (GeoNames lookup):
  %(prog)s "Test Person" --date 1990-06-15 --time 14:30 --city "London" --nation "GB"

  # Offline mode (exact coordinates):
  %(prog)s "Albert Einstein" --date 1879-03-14 --time 11:30 --lat 48.4011 --lng 9.9876 --tz "Europe/Berlin"
        """
    )

    # Positional argument
    parser.add_argument(
        "name",
        help="Person's name"
    )

    # Required arguments
    parser.add_argument(
        "--date",
        type=valid_date,
        required=True,
        help="Birth date in YYYY-MM-DD format"
    )

    parser.add_argument(
        "--time",
        type=valid_time,
        required=True,
        help="Birth time in HH:MM format (24-hour)"
    )

    # Location arguments - two modes: GeoNames online OR offline coordinates
    parser.add_argument(
        "--city",
        type=str,
        help="City name for GeoNames online lookup (use with --nation)"
    )

    parser.add_argument(
        "--nation",
        type=str,
        help="Nation code for GeoNames online lookup (e.g., 'US', 'GB', 'FR')"
    )

    parser.add_argument(
        "--lat",
        type=valid_latitude,
        help="Birth location latitude (-90 to 90) for offline mode"
    )

    parser.add_argument(
        "--lng",
        type=valid_longitude,
        help="Birth location longitude (-180 to 180) for offline mode"
    )

    parser.add_argument(
        "--tz",
        type=str,
        help="IANA timezone string for offline mode (e.g., 'America/New_York', 'Europe/Berlin')"
    )

    try:
        args = parser.parse_args()

        # Validate location mode: must provide either GeoNames or coordinates (not both, not neither)
        has_geonames = args.city and args.nation
        has_coords = args.lat is not None and args.lng is not None and args.tz

        if not has_geonames and not has_coords:
            parser.error("Must provide either (--city and --nation) or (--lat, --lng, --tz)")
        if has_geonames and has_coords:
            parser.error("Cannot mix location modes: use either (--city/--nation) or (--lat/--lng/--tz)")

        # Create AstrologicalSubject based on location mode
        if has_geonames:
            # GeoNames online mode
            try:
                geonames_username = os.getenv('KERYKEION_GEONAMES_USERNAME')
                kwargs = {
                    'name': args.name,
                    'year': args.date.year,
                    'month': args.date.month,
                    'day': args.date.day,
                    'hour': args.time.hour,
                    'minute': args.time.minute,
                    'city': args.city,
                    'nation': args.nation,
                    'online': True,
                    'houses_system_identifier': 'P',
                    'active_points': ['Sun', 'Moon', 'Mercury', 'Venus', 'Mars', 'Jupiter', 'Saturn',
                                     'Uranus', 'Neptune', 'Pluto', 'Chiron', 'Mean_Lilith', 'True_Lilith',
                                     'Ceres', 'Pallas', 'Juno', 'Vesta', 'Mean_North_Lunar_Node',
                                     'Ascendant', 'Medium_Coeli', 'Descendant', 'Imum_Coeli']
                }
                if geonames_username:
                    kwargs['geonames_username'] = geonames_username

                subject = AstrologicalSubjectFactory.from_birth_data(**kwargs)

                # Display resolved location for user verification
                print(f"Location resolved: {subject.city}, {subject.nation}")
                print(f"Coordinates: {subject.lat:.4f}, {subject.lng:.4f}")
                print(f"Timezone: {subject.tz_str}")

            except KerykeionException as e:
                print(f"Error: Unable to resolve location '{args.city}, {args.nation}'", file=sys.stderr)
                print(f"Details: {e}", file=sys.stderr)
                print("Tip: Check city spelling and nation code (e.g., 'US', 'GB', 'FR')", file=sys.stderr)
                return 1
        else:
            # Offline coordinate mode
            subject = AstrologicalSubjectFactory.from_birth_data(
                name=args.name,
                year=args.date.year,
                month=args.date.month,
                day=args.date.day,
                hour=args.time.hour,
                minute=args.time.minute,
                lng=args.lng,
                lat=args.lat,
                tz_str=args.tz,
                online=False,
                houses_system_identifier='P',
                active_points=['Sun', 'Moon', 'Mercury', 'Venus', 'Mars', 'Jupiter', 'Saturn',
                              'Uranus', 'Neptune', 'Pluto', 'Chiron', 'Mean_Lilith', 'True_Lilith',
                              'Ceres', 'Pallas', 'Juno', 'Vesta', 'Mean_North_Lunar_Node',
                              'Ascendant', 'Medium_Coeli', 'Descendant', 'Imum_Coeli']
            )

        # Verify Placidus house system
        if subject.houses_system_identifier != "P":
            print(f"Warning: Expected Placidus (P), got {subject.houses_system_identifier}", file=sys.stderr)

        # Extract and display all planetary positions
        print("\n=== PLANETARY POSITIONS ===")
        planets = [
            ('Sun', subject.sun), ('Moon', subject.moon),
            ('Mercury', subject.mercury), ('Venus', subject.venus),
            ('Mars', subject.mars), ('Jupiter', subject.jupiter),
            ('Saturn', subject.saturn), ('Uranus', subject.uranus),
            ('Neptune', subject.neptune), ('Pluto', subject.pluto),
        ]
        for name, planet in planets:
            retrograde = " (R)" if getattr(planet, 'retrograde', False) else ""
            # Calculate position within sign (0-30 degrees)
            position_in_sign = planet.position % 30
            print(f"{name:10} {planet.sign:3} {position_in_sign:6.2f}° House {planet.house}{retrograde}")

        # Extract and display all house cusps
        print("\n=== HOUSE CUSPS (Placidus) ===")
        houses = [
            subject.first_house, subject.second_house, subject.third_house,
            subject.fourth_house, subject.fifth_house, subject.sixth_house,
            subject.seventh_house, subject.eighth_house, subject.ninth_house,
            subject.tenth_house, subject.eleventh_house, subject.twelfth_house,
        ]
        for i, house in enumerate(houses, 1):
            position_in_sign = house.position % 30
            print(f"House {i:2}   {house.sign:3} {position_in_sign:6.2f}°")

        # Extract and display all angles
        print("\n=== ANGLES ===")
        angles = [
            ('ASC', subject.ascendant),
            ('MC', subject.medium_coeli),
            ('DSC', subject.descendant),
            ('IC', subject.imum_coeli),
        ]
        for name, angle in angles:
            position_in_sign = angle.position % 30
            print(f"{name:3}        {angle.sign:3} {position_in_sign:6.2f}°")

        # Calculate and display major aspects
        print("\n=== MAJOR ASPECTS ===")
        natal_aspects = NatalAspects(subject)
        major_types = ['conjunction', 'opposition', 'trine', 'square', 'sextile']
        # Filter for major aspects between the 10 main planets only
        planet_names = ['Sun', 'Moon', 'Mercury', 'Venus', 'Mars', 'Jupiter', 'Saturn', 'Uranus', 'Neptune', 'Pluto']
        filtered = [
            asp for asp in natal_aspects.all_aspects
            if asp.aspect in major_types
            and asp.p1_name in planet_names
            and asp.p2_name in planet_names
        ]
        print(f"Found {len(filtered)} major aspects:")
        for asp in filtered:
            # Format aspect movement status
            movement = asp.aspect_movement if hasattr(asp, 'aspect_movement') else ''
            print(f"{asp.p1_name:10} {asp.aspect:12} {asp.p2_name:10} (orb: {asp.orbit:.2f}°, {movement})")

        # Extract and display asteroid positions
        print("\n=== ASTEROIDS ===")
        asteroid_attrs = [
            ('Chiron', 'chiron'),
            ('Mean Lilith', 'mean_lilith'),
            ('True Lilith', 'true_lilith'),
            ('Ceres', 'ceres'),
            ('Pallas', 'pallas'),
            ('Juno', 'juno'),
            ('Vesta', 'vesta'),
        ]
        for name, attr in asteroid_attrs:
            body = getattr(subject, attr, None)
            if body is not None:
                retrograde = " (R)" if getattr(body, 'retrograde', False) else ""
                # Calculate position within sign (0-30 degrees)
                position_in_sign = body.position % 30
                print(f"{name:12} {body.sign:3} {position_in_sign:6.2f}° House {body.house}{retrograde}")
            else:
                print(f"{name:12} Not available")

        # Calculate and display Arabic Parts
        print("\n=== ARABIC PARTS ===")

        # Determine day/night chart based on Sun's house position
        # Day chart: Sun in houses 7-12 (above horizon)
        # Night chart: Sun in houses 1-6 (below horizon)
        sun_house_str = str(subject.sun.house)
        # Extract house number from string like "Ninth_House" or just "9"
        house_names = {
            'First_House': 1, 'Second_House': 2, 'Third_House': 3, 'Fourth_House': 4,
            'Fifth_House': 5, 'Sixth_House': 6, 'Seventh_House': 7, 'Eighth_House': 8,
            'Ninth_House': 9, 'Tenth_House': 10, 'Eleventh_House': 11, 'Twelfth_House': 12
        }
        sun_house = house_names.get(sun_house_str, int(sun_house_str) if sun_house_str.isdigit() else 1)
        is_day_chart = 7 <= sun_house <= 12

        # Get absolute positions
        asc_pos = subject.ascendant.position
        sun_pos = subject.sun.position
        moon_pos = subject.moon.position

        # Calculate Part of Fortune
        if is_day_chart:
            # Day formula: ASC + Moon - Sun
            fortune_pos = (asc_pos + moon_pos - sun_pos) % 360
        else:
            # Night formula: ASC + Sun - Moon
            fortune_pos = (asc_pos + sun_pos - moon_pos) % 360

        # Calculate Part of Spirit (reverse of Fortune)
        if is_day_chart:
            # Day formula: ASC + Sun - Moon
            spirit_pos = (asc_pos + sun_pos - moon_pos) % 360
        else:
            # Night formula: ASC + Moon - Sun
            spirit_pos = (asc_pos + moon_pos - sun_pos) % 360

        # Convert to sign and degree
        fortune_sign, fortune_degree = position_to_sign_degree(fortune_pos)
        spirit_sign, spirit_degree = position_to_sign_degree(spirit_pos)

        # Display results
        chart_type = "Day" if is_day_chart else "Night"
        print(f"Chart Type: {chart_type}")
        print(f"Part of Fortune:  {fortune_sign} {fortune_degree:6.2f}°")
        print(f"Part of Spirit:   {spirit_sign} {spirit_degree:6.2f}°")

        # Display essential dignities for traditional planets
        print("\n=== ESSENTIAL DIGNITIES ===")
        traditional_planets = [
            ('Sun', subject.sun),
            ('Moon', subject.moon),
            ('Mercury', subject.mercury),
            ('Venus', subject.venus),
            ('Mars', subject.mars),
            ('Jupiter', subject.jupiter),
            ('Saturn', subject.saturn),
        ]
        for name, planet in traditional_planets:
            dignities = get_planet_dignities(name, planet.sign)
            dignity_str = ', '.join(dignities) if dignities else 'None'
            print(f"{name:10} in {planet.sign:3}  {dignity_str}")

        print("\nNote: Traditional planets only (Sun-Saturn). Modern planet dignities (Uranus, Neptune, Pluto) are disputed and excluded.")

        # Calculate and display fixed star conjunctions
        print("\n=== FIXED STAR CONJUNCTIONS (orb <= 1.0 deg) ===")

        # Set Swiss Ephemeris path to Kerykeion's sweph directory (contains sefstars.txt)
        kerykeion_path = Path(kerykeion.__file__).parent
        sweph_path = kerykeion_path / 'sweph'
        swe.set_ephe_path(str(sweph_path))

        # Calculate Julian day for the birth data
        jd = swe.julday(args.date.year, args.date.month, args.date.day,
                        args.time.hour + args.time.minute / 60.0)

        # Build points to check: all 10 planets + 4 angles (use abs_pos for absolute longitude)
        points_to_check = [(name, p.abs_pos) for name, p in planets] + \
                          [(name, a.abs_pos) for name, a in angles]

        conjunctions = []
        for star_lookup, star_display in MAJOR_STARS:
            try:
                # Get star position using fixstar2_ut (needs lowercase name)
                # Returns: (tuple_of_6_floats, star_name, retflags)
                star_data, returned_name, ret_flag = swe.fixstar2_ut(star_lookup, jd, 0)
                star_long = star_data[0]  # First element is longitude

                # Check conjunction to each planet and angle
                for point_name, point_long in points_to_check:
                    # Calculate absolute difference with zodiac wrap-around handling
                    diff = abs(point_long - star_long)
                    if diff > 180:
                        diff = 360 - diff

                    # Conjunction if within 1 degree orb
                    if diff <= 1.0:
                        conjunctions.append((star_display, point_name, diff))

            except Exception as e:
                # Handle missing stars gracefully (print warning, continue)
                print(f"Warning: Could not calculate {star_display}: {e}", file=sys.stderr)

        # Display results
        if conjunctions:
            for star_name, point_name, orb in conjunctions:
                print(f"{star_name} conjunct {point_name} (orb: {orb:.2f} deg)")
        else:
            print("No major fixed star conjunctions detected")

        # Calculate and display element distribution
        print("\n=== ELEMENT DISTRIBUTION ===")

        # Collect placements: 10 planets + ASC (11 total)
        placements = [(name, p) for name, p in planets] + [('ASC', subject.ascendant)]

        # Count elements and track which planets are in each
        element_count = {'Fire': 0, 'Earth': 0, 'Air': 0, 'Water': 0}
        element_planets = {'Fire': [], 'Earth': [], 'Air': [], 'Water': []}

        for name, body in placements:
            element = ELEMENT_MAP.get(body.sign)
            if element:
                element_count[element] += 1
                element_planets[element].append(name)

        # Display total
        total_placements = sum(element_count.values())
        print(f"Total placements: {total_placements}")

        # Display each element with count, percentage, and planet names
        for element in ['Fire', 'Earth', 'Air', 'Water']:
            count = element_count[element]
            percentage = (count / total_placements * 100) if total_placements > 0 else 0
            planets_str = ', '.join(element_planets[element]) if element_planets[element] else 'None'
            print(f"{element:5} ({count}): {percentage:5.1f}% - {planets_str}")

        # Calculate and display modality distribution
        print("\n=== MODALITY DISTRIBUTION ===")

        # Count modalities and track which planets are in each
        modality_count = {'Cardinal': 0, 'Fixed': 0, 'Mutable': 0}
        modality_planets = {'Cardinal': [], 'Fixed': [], 'Mutable': []}

        for name, body in placements:
            modality = MODALITY_MAP.get(body.sign)
            if modality:
                modality_count[modality] += 1
                modality_planets[modality].append(name)

        # Display total
        total_placements = sum(modality_count.values())
        print(f"Total placements: {total_placements}")

        # Display each modality with count, percentage, and planet names
        for modality in ['Cardinal', 'Fixed', 'Mutable']:
            count = modality_count[modality]
            percentage = (count / total_placements * 100) if total_placements > 0 else 0
            planets_str = ', '.join(modality_planets[modality]) if modality_planets[modality] else 'None'
            print(f"{modality:8} ({count}): {percentage:5.1f}% - {planets_str}")

        # Build comprehensive JSON structure (for file output in Plan 02)
        chart_dict = build_chart_json(subject, args)

        return 0

    except Exception as e:
        print(f"Error creating chart: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
