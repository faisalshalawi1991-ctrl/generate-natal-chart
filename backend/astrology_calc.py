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
from datetime import datetime, timezone, timedelta
from collections import defaultdict

from kerykeion import AstrologicalSubjectFactory, NatalAspects, KerykeionException
from kerykeion.charts.chart_drawer import ChartDrawer
from kerykeion.aspects.aspects_factory import AspectsFactory
from kerykeion.house_comparison.house_comparison_factory import HouseComparisonFactory
from kerykeion.schemas.kr_models import ActiveAspect
from kerykeion.ephemeris_data_factory import EphemerisDataFactory
from kerykeion.transits_time_range_factory import TransitsTimeRangeFactory
import swisseph as swe
import kerykeion
from slugify import slugify


# Profile storage directory
CHARTS_DIR = Path("~/.natal-charts").expanduser()


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

# Default orbs for transit-to-natal aspects (tighter than natal-only orbs)
TRANSIT_DEFAULT_ORBS = [
    ActiveAspect(name='conjunction', orb=3),
    ActiveAspect(name='opposition', orb=3),
    ActiveAspect(name='trine', orb=2),
    ActiveAspect(name='square', orb=2),
    ActiveAspect(name='sextile', orb=1),
]

# Major planets used in transit calculations
MAJOR_PLANETS = [
    'Sun', 'Moon', 'Mercury', 'Venus', 'Mars',
    'Jupiter', 'Saturn', 'Uranus', 'Neptune', 'Pluto'
]

# Default orbs for progressed-to-natal aspects (1-degree orb for all aspects)
# Standard for secondary progressions per Kepler College recommendation
PROG_DEFAULT_ORBS = [
    ActiveAspect(name='conjunction', orb=1),
    ActiveAspect(name='opposition', orb=1),
    ActiveAspect(name='trine', orb=1),
    ActiveAspect(name='square', orb=1),
    ActiveAspect(name='sextile', orb=1),
]

# Default orbs for solar arc directed-to-natal aspects (1-degree for all aspects)
# Professional standard: 1 degree = approx. 1-year timing window (Noel Tyl)
# Plain dict (not ActiveAspect list) — aspects are computed manually, no AspectsFactory
SARC_DEFAULT_ORBS = {
    'conjunction': 1.0,
    'opposition': 1.0,
    'trine': 1.0,
    'square': 1.0,
    'sextile': 1.0,
}

# Naibod mean arc constant: Sun's mean daily motion in degrees per year
# Used for --arc-method mean (constant-rate approximation)
NAIBOD_ARC = 0.98564733  # degrees per year

# Aspect target angles for manual solar arc aspect calculation
SARC_ASPECT_ANGLES = {
    'conjunction': 0,
    'opposition': 180,
    'trine': 120,
    'square': 90,
    'sextile': 60,
}

# Sign offsets for reconstructing house cusp abs_positions from chart.json
# House entries have sign + degree but NO abs_position key
# Planets and angles DO have abs_position directly
SIGN_OFFSETS = {
    'Ari': 0, 'Tau': 30, 'Gem': 60, 'Can': 90,
    'Leo': 120, 'Vir': 150, 'Lib': 180, 'Sco': 210,
    'Sag': 240, 'Cap': 270, 'Aqu': 300, 'Pis': 330,
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


def valid_query_date(s):
    """
    Validate date string in YYYY-MM-DD format for transit query dates.

    Accepts a broader range than valid_date: 1900-2100, to support historical
    and future transit lookups beyond the natal chart date constraints.

    Args:
        s: Date string to validate

    Returns:
        datetime object if valid

    Raises:
        argparse.ArgumentTypeError: If date format is invalid or out of 1900-2100 range
    """
    try:
        dt = datetime.strptime(s, "%Y-%m-%d")
        if dt.year < 1900 or dt.year > 2100:
            raise argparse.ArgumentTypeError(
                f"Query date year must be between 1900 and 2100, got {dt.year}"
            )
        return dt
    except ValueError as e:
        raise argparse.ArgumentTypeError(f"Invalid date format '{s}'. Use YYYY-MM-DD. Error: {e}")


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


def load_natal_profile(slug):
    """
    Load a saved natal chart profile and reconstruct an AstrologicalSubject.

    Reads chart.json from ~/.natal-charts/{slug}/, extracts birth data, and
    reconstructs an AstrologicalSubjectModel using offline mode (no GeoNames).

    Args:
        slug: Profile slug (e.g., 'albert-einstein')

    Returns:
        tuple: (AstrologicalSubjectModel, profile_dict) where profile_dict is the
               full parsed chart.json data

    Raises:
        FileNotFoundError: If the profile directory or chart.json does not exist
        SystemExit(1): If chart.json cannot be parsed or required fields are missing
    """
    profile_dir = CHARTS_DIR / slug
    chart_json_path = profile_dir / "chart.json"

    if not chart_json_path.exists():
        raise FileNotFoundError(
            f"Profile '{slug}' not found. Run --list to see available profiles."
        )

    try:
        with open(chart_json_path, 'r', encoding='utf-8') as f:
            profile_data = json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        print(f"Error reading profile '{slug}': {e}", file=sys.stderr)
        sys.exit(1)

    try:
        meta = profile_data['meta']
        birth_date_str = meta['birth_date']          # e.g. "1879-03-14"
        birth_time_str = meta['birth_time']          # e.g. "11:30"
        location = meta['location']
        lat = float(location['latitude'])
        lng = float(location['longitude'])
        tz_str = location['timezone']
        name = meta['name']

        birth_date = datetime.strptime(birth_date_str, "%Y-%m-%d")
        birth_time = datetime.strptime(birth_time_str, "%H:%M")
    except (KeyError, ValueError) as e:
        print(f"Error parsing profile '{slug}': missing or invalid field — {e}", file=sys.stderr)
        sys.exit(1)

    subject = AstrologicalSubjectFactory.from_birth_data(
        name=name,
        year=birth_date.year,
        month=birth_date.month,
        day=birth_date.day,
        hour=birth_time.hour,
        minute=birth_time.minute,
        lat=lat,
        lng=lng,
        tz_str=tz_str,
        online=False,
        houses_system_identifier='P',
    )

    return subject, profile_data


def save_snapshot(profile_dir, mode, date_str, data):
    """
    Write predictive snapshot JSON to the profile directory.

    Args:
        profile_dir: Path — ~/.natal-charts/{slug}/
        mode:        str  — 'transit', 'progressions', or 'solar-arc'
        date_str:    str  — YYYY-MM-DD for filename (from meta field)
        data:        dict — already-assembled JSON dict from build_*_json()

    Returns:
        Path: The written file path (for confirmation message)
    """
    filename = f"{mode}-{date_str}.json"
    out_path = profile_dir / filename
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    return out_path


def build_transit_json(transit_subject, natal_subject, natal_data, query_date_str, slug):
    """
    Build a transit snapshot JSON dict from transit and natal AstrologicalSubject instances.

    Calculates transit planet positions, natal house placements for transiting planets,
    transit-to-natal aspects using TRANSIT_DEFAULT_ORBS, and aspect movement (applying/separating).

    Args:
        transit_subject: AstrologicalSubjectModel for the transit moment (UTC)
        natal_subject: AstrologicalSubjectModel for the natal chart
        natal_data: dict — full parsed chart.json from the natal profile
        query_date_str: str — YYYY-MM-DD date used for the transit (for meta)
        slug: str — natal profile slug (for meta)

    Returns:
        dict: Transit snapshot with meta, transit_planets, and transit_aspects sections
    """
    natal_meta = natal_data.get('meta', {})
    natal_name = natal_meta.get('name', slug)

    # Build orbs_used dict for meta (aspect name -> orb)
    orbs_used = {ao['name']: ao['orb'] for ao in TRANSIT_DEFAULT_ORBS}

    meta = {
        "natal_name": natal_name,
        "natal_slug": slug,
        "query_date": query_date_str,
        "query_time_utc": "12:00" if transit_subject.hour == 12 and transit_subject.minute == 0 else
                          f"{transit_subject.hour:02d}:{transit_subject.minute:02d}",
        "chart_type": "transit_snapshot",
        "calculated_at": datetime.now(timezone.utc).isoformat(),
        "orbs_used": orbs_used,
    }

    # Build transit planet position list (10 major planets)
    planet_attrs = [
        ('Sun', transit_subject.sun),
        ('Moon', transit_subject.moon),
        ('Mercury', transit_subject.mercury),
        ('Venus', transit_subject.venus),
        ('Mars', transit_subject.mars),
        ('Jupiter', transit_subject.jupiter),
        ('Saturn', transit_subject.saturn),
        ('Uranus', transit_subject.uranus),
        ('Neptune', transit_subject.neptune),
        ('Pluto', transit_subject.pluto),
    ]

    # Compute natal house placement for each transit planet using HouseComparisonFactory
    # first_subject = transit, second_subject = natal
    # first_points_in_second_houses = transit planets in natal houses
    house_comparison = HouseComparisonFactory(
        transit_subject, natal_subject, active_points=MAJOR_PLANETS
    ).get_house_comparison()

    # Build a lookup: point_name -> projected_house_number
    house_lookup = {
        item.point_name: item.projected_house_number
        for item in house_comparison.first_points_in_second_houses
    }

    transit_planets = []
    for name, planet in planet_attrs:
        natal_house = house_lookup.get(name)
        transit_planets.append({
            "name": name,
            "sign": planet.sign,
            "degree": round(planet.abs_pos % 30, 2),
            "abs_position": round(planet.abs_pos, 4),
            "retrograde": bool(planet.retrograde),
            "natal_house": natal_house,
        })

    # Calculate transit-to-natal aspects using AspectsFactory.dual_chart_aspects
    # first_subject = transit (moving), second_subject = natal (fixed)
    dual_aspects_model = AspectsFactory.dual_chart_aspects(
        transit_subject,
        natal_subject,
        active_points=MAJOR_PLANETS,
        active_aspects=TRANSIT_DEFAULT_ORBS,
        second_subject_is_fixed=True,
    )

    transit_aspects = []
    for asp in dual_aspects_model.aspects:
        # Only include aspects where p1 is a transit planet and p2 is a natal planet
        if asp.p1_name in MAJOR_PLANETS and asp.p2_name in MAJOR_PLANETS:
            transit_aspects.append({
                "transit_planet": asp.p1_name,
                "natal_planet": asp.p2_name,
                "aspect": asp.aspect,
                "orb": round(asp.orbit, 2),
                "applying": asp.aspect_movement == 'Applying',
                "movement": asp.aspect_movement,
            })

    return {
        "meta": meta,
        "transit_planets": transit_planets,
        "transit_aspects": transit_aspects,
    }


def calculate_transits(args):
    """
    Orchestrate transit snapshot calculation for an existing natal profile.

    Loads the natal profile identified by args.transits, creates a transit subject
    for the requested date (args.query_date, or current UTC if not specified),
    and prints the transit JSON to stdout.

    Args:
        args: Parsed argparse Namespace with .transits (slug) and .query_date (datetime or None)

    Returns:
        0 on success, 1 on error
    """
    try:
        # Load natal chart profile
        natal_subject, natal_data = load_natal_profile(args.transits)

        # Determine query datetime (UTC)
        if args.query_date is not None:
            # Use specified date at UTC noon
            query_dt = args.query_date.replace(hour=12, minute=0, second=0, microsecond=0)
            query_date_str = args.query_date.strftime("%Y-%m-%d")
        else:
            # Use current UTC moment
            query_dt = datetime.now(timezone.utc)
            query_date_str = query_dt.strftime("%Y-%m-%d")

        # Create transit subject at 0,0 UTC (geocentric, no location bias)
        transit_subject = AstrologicalSubjectFactory.from_birth_data(
            name='Current Transits',
            year=query_dt.year,
            month=query_dt.month,
            day=query_dt.day,
            hour=query_dt.hour,
            minute=query_dt.minute,
            lat=0.0,
            lng=0.0,
            tz_str='UTC',
            online=False,
            houses_system_identifier='P',
        )

        # Assemble transit JSON dict
        transit_dict = build_transit_json(
            transit_subject, natal_subject, natal_data, query_date_str, args.transits
        )

        # Output to stdout
        print(json.dumps(transit_dict, indent=2))

        if args.save:
            date_str = transit_dict['meta'].get('query_date', 'unknown')
            try:
                out_path = save_snapshot(CHARTS_DIR / args.transits, 'transit', date_str, transit_dict)
                print(f"Snapshot saved: {out_path}", file=sys.stderr)
            except Exception as e:
                print(f"Warning: Could not save snapshot: {e}", file=sys.stderr)

        return 0

    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error calculating transits: {e}", file=sys.stderr)
        return 1


def parse_preset_range(preset, reference_date=None):
    """
    Convert preset range string to (start_dt, end_dt) UTC noon datetimes.

    Args:
        preset: One of 'week', '30d', '3m', 'year'
        reference_date: datetime to use as 'today' (default: today UTC)

    Returns:
        Tuple[datetime, datetime]: (start, end) at UTC noon
    """
    if reference_date is None:
        reference_date = datetime.now(timezone.utc).replace(tzinfo=None)

    today = reference_date.replace(hour=12, minute=0, second=0, microsecond=0)

    DELTAS = {
        'week':  timedelta(days=6),
        '30d':   timedelta(days=29),
        '3m':    timedelta(days=89),
        'year':  timedelta(days=364),
    }
    if preset not in DELTAS:
        raise ValueError(f"Invalid preset: {preset}. Use: week, 30d, 3m, year")

    return today, today + DELTAS[preset]


def build_timeline_events(results):
    """
    Extract exact transit aspect hit events from TransitsTimeRangeModel.

    An 'exact hit' is detected when an aspect's aspect_movement transitions from
    'Applying' (on day N) to 'Separating' or 'Static' (on day N+1).
    The hit date is reported as day N (the last day in the Applying state).
    The orb on day N is the closest recorded approach.

    Args:
        results: TransitsTimeRangeModel from TransitsTimeRangeFactory.get_transit_moments()

    Returns:
        List[dict]: Sorted list of event dicts, each with:
            - date (str): YYYY-MM-DD of the exact hit
            - transit_planet (str): Name of the transiting planet
            - aspect (str): Aspect type (conjunction, opposition, etc.)
            - natal_planet (str): Name of the natal planet
            - orb_at_hit (float): Closest orb recorded (the applying orb on hit date)
    """
    aspect_tracking = defaultdict(list)
    for tm in results.transits:
        date_str = tm.date[:10]  # YYYY-MM-DD from ISO datetime
        for asp in tm.aspects:
            if asp.p1_name in MAJOR_PLANETS and asp.p2_name in MAJOR_PLANETS:
                key = (asp.p1_name, asp.aspect, asp.p2_name)
                aspect_tracking[key].append((date_str, round(asp.orbit, 3), asp.aspect_movement))

    events = []
    for (transit_planet, aspect_type, natal_planet), track in aspect_tracking.items():
        for i in range(1, len(track)):
            prev_date, prev_orb, prev_mv = track[i - 1]
            _curr_date, _curr_orb, curr_mv = track[i]
            if prev_mv == 'Applying' and curr_mv in ('Separating', 'Static'):
                events.append({
                    'date': prev_date,
                    'transit_planet': transit_planet,
                    'aspect': aspect_type,
                    'natal_planet': natal_planet,
                    'orb_at_hit': prev_orb,
                })

    events.sort(key=lambda e: e['date'])
    return events


def build_timeline_json(results, natal_data, slug, start_dt, end_dt):
    """
    Assemble complete timeline JSON dict from factory results and natal data.

    Args:
        results: TransitsTimeRangeModel from TransitsTimeRangeFactory.get_transit_moments()
        natal_data: dict — full parsed chart.json from the natal profile
        slug: str — natal profile slug
        start_dt: datetime — timeline start (UTC noon)
        end_dt: datetime — timeline end (UTC noon)

    Returns:
        dict: Timeline JSON with 'meta' and 'events' sections
    """
    events = build_timeline_events(results)

    natal_meta = natal_data.get('meta', {})
    natal_name = natal_meta.get('name', slug)

    range_days = (end_dt - start_dt).days

    orbs_used = {ao['name']: ao['orb'] for ao in TRANSIT_DEFAULT_ORBS}

    meta = {
        "natal_name": natal_name,
        "natal_slug": slug,
        "start_date": start_dt.strftime("%Y-%m-%d"),
        "end_date": end_dt.strftime("%Y-%m-%d"),
        "range_days": range_days,
        "chart_type": "transit_timeline",
        "calculated_at": datetime.now(timezone.utc).isoformat(),
        "orbs_used": orbs_used,
        "event_count": len(events),
        "sampling_note": "Daily resolution; fast Moon aspects (< 4h in orb) may not appear.",
    }

    return {
        "meta": meta,
        "events": events,
    }


def calculate_timeline(args):
    """
    Orchestrate transit timeline calculation for an existing natal profile.

    Loads the natal profile identified by args.timeline, determines the date range
    from either preset (--range) or custom (--start/--end) arguments, generates
    daily ephemeris data, runs transit comparisons, extracts exact hit events, and
    prints the timeline JSON to stdout.

    Args:
        args: Parsed argparse Namespace with .timeline (slug), .range, .start, .end

    Returns:
        0 on success, 1 on error
    """
    try:
        natal_subject, natal_data = load_natal_profile(args.timeline)

        # Determine date range
        if args.start and args.end:
            # Custom range (TRAN-07)
            start_dt = args.start.replace(hour=12, minute=0, second=0, microsecond=0)
            end_dt = args.end.replace(hour=12, minute=0, second=0, microsecond=0)
            if start_dt >= end_dt:
                print("Error: --start must be before --end", file=sys.stderr)
                return 1
            range_days = (end_dt - start_dt).days
            if range_days > 365:
                print("Error: Custom date range cannot exceed 365 days", file=sys.stderr)
                return 1
        elif args.start or args.end:
            print("Error: both --start and --end required for custom range", file=sys.stderr)
            return 1
        else:
            # Preset range (TRAN-06)
            start_dt, end_dt = parse_preset_range(args.range)

        # Generate daily ephemeris (lat=0, lng=0, UTC — geocentric, location-independent)
        eph_factory = EphemerisDataFactory(
            start_datetime=start_dt,
            end_datetime=end_dt,
            step_type='days',
            step=1,
            lat=0.0,
            lng=0.0,
            tz_str='Etc/UTC',
        )
        ephemeris_subjects = eph_factory.get_ephemeris_data_as_astrological_subjects()

        # Run transit comparison against natal chart
        transit_factory = TransitsTimeRangeFactory(
            natal_chart=natal_subject,
            ephemeris_data_points=ephemeris_subjects,
            active_points=MAJOR_PLANETS,
            active_aspects=TRANSIT_DEFAULT_ORBS,
        )
        results = transit_factory.get_transit_moments()

        # Extract exact hit events and assemble output
        timeline_dict = build_timeline_json(results, natal_data, args.timeline, start_dt, end_dt)
        print(json.dumps(timeline_dict, indent=2))

        if args.save:
            date_str = timeline_dict['meta'].get('start_date', 'unknown')
            try:
                out_path = save_snapshot(CHARTS_DIR / args.timeline, 'timeline', date_str, timeline_dict)
                print(f"Snapshot saved: {out_path}", file=sys.stderr)
            except Exception as e:
                print(f"Warning: Could not save snapshot: {e}", file=sys.stderr)

        return 0

    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error calculating timeline: {e}", file=sys.stderr)
        return 1


def compute_progressed_jd(birth_jd, target_jd):
    """
    Compute the progressed Julian Day using the day-for-a-year formula.

    Formula: progressed_jd = birth_jd + (target_jd - birth_jd) / 365.25

    The elapsed years between birth and target become elapsed days in the
    ephemeris (one day of ephemeris time = one year of life). The divisor
    365.25 is the Julian year — standard in Western tropical astrology.

    Args:
        birth_jd: Julian Day number of the birth moment (including fractional hour)
        target_jd: Julian Day number of the target date/moment

    Returns:
        float: Progressed Julian Day number
    """
    return birth_jd + (target_jd - birth_jd) / 365.25


def build_monthly_moon(birth_jd, target_year, natal_lat, natal_lng, natal_tz_str):
    """
    Calculate progressed Moon position for each month of target_year.

    Uses the 1st day of each month at UTC noon as the target moment,
    calculates progressed JD, creates a progressed subject, and extracts
    Moon sign and degree. Sign changes are detected and flagged.

    Args:
        birth_jd: Julian Day number of the birth moment
        target_year: Integer year for which to calculate the 12-month Moon positions
        natal_lat: Natal chart latitude (used for progressed subject creation)
        natal_lng: Natal chart longitude (used for progressed subject creation)
        natal_tz_str: Natal chart timezone string (used for progressed subject creation)

    Returns:
        List[dict]: 12 entries with month (YYYY-MM), sign, degree, and optional sign_change
    """
    monthly = []
    prev_sign = None

    for month in range(1, 13):
        month_jd = swe.julday(target_year, month, 1, 12.0)
        prog_jd = compute_progressed_jd(birth_jd, month_jd)
        py, pm, pd, ph = swe.revjul(prog_jd)

        m_subj = AstrologicalSubjectFactory.from_birth_data(
            name=f'prog_moon_{month}',
            year=int(py), month=int(pm), day=int(pd),
            hour=int(ph), minute=int((ph - int(ph)) * 60),
            lat=natal_lat, lng=natal_lng, tz_str=natal_tz_str,
            online=False, houses_system_identifier='P',
        )
        sign = m_subj.moon.sign
        degree = round(m_subj.moon.position % 30, 2)

        entry = {
            "month": f"{target_year}-{month:02d}",
            "sign": sign,
            "degree": degree,
        }
        if prev_sign is not None and sign != prev_sign:
            entry["sign_change"] = f"{prev_sign} -> {sign}"

        monthly.append(entry)
        prev_sign = sign

    return monthly


def build_progressed_json(progressed_subject, natal_subject, natal_data, slug,
                          target_date_str, target_jd, birth_jd, prog_year=None):
    """
    Assemble complete secondary progressions JSON dict.

    Args:
        progressed_subject: AstrologicalSubjectModel for the progressed date
        natal_subject: AstrologicalSubjectModel for the natal chart
        natal_data: dict — full parsed chart.json from natal profile
        slug: str — natal profile slug
        target_date_str: str — YYYY-MM-DD target date (may be None for age-based)
        target_jd: float — Julian Day number of target date
        birth_jd: float — Julian Day number of birth moment
        prog_year: int or None — year for monthly Moon report (defaults to target year)

    Returns:
        dict: Complete progressions JSON with meta, progressed_planets, progressed_angles,
              progressed_aspects, monthly_moon, and distribution_shift sections
    """
    natal_meta = natal_data.get('meta', {})
    natal_name = natal_meta.get('name', slug)
    location = natal_meta.get('location', {})
    natal_lat = float(location['latitude'])
    natal_lng = float(location['longitude'])
    natal_tz_str = location['timezone']

    # Compute progressed date parts
    prog_jd = compute_progressed_jd(birth_jd, target_jd)
    py, pm, pd, ph = swe.revjul(prog_jd)
    prog_hour = int(ph)
    prog_minute = int((ph - prog_hour) * 60)

    # Compute target_date_str if not provided (age-based mode)
    if target_date_str is None:
        ty, tm, td, th = swe.revjul(target_jd)
        target_date_str = f"{int(ty):04d}-{int(tm):02d}-{int(td):02d}"

    # Compute age at target
    age_at_target = int((target_jd - birth_jd) / 365.25)

    # Determine prog_year for monthly Moon report
    if prog_year is None:
        # Default: year portion of target date
        ty, tm, td, th = swe.revjul(target_jd)
        prog_year = int(ty)

    # Build orbs_used dict for meta
    orbs_used = {ao['name']: ao['orb'] for ao in PROG_DEFAULT_ORBS}

    # META section
    meta = {
        "natal_name": natal_name,
        "natal_slug": slug,
        "target_date": target_date_str,
        "progressed_date": f"{int(py):04d}-{int(pm):02d}-{int(pd):02d}",
        "progressed_time": f"{prog_hour:02d}:{prog_minute:02d}",
        "age_at_target": age_at_target,
        "chart_type": "secondary_progressions",
        "calculated_at": datetime.now(timezone.utc).isoformat(),
        "orbs_used": orbs_used,
        "prog_year": prog_year,
    }

    # PROGRESSED PLANETS section (10 planets)
    planet_attrs = [
        ('Sun', progressed_subject.sun),
        ('Moon', progressed_subject.moon),
        ('Mercury', progressed_subject.mercury),
        ('Venus', progressed_subject.venus),
        ('Mars', progressed_subject.mars),
        ('Jupiter', progressed_subject.jupiter),
        ('Saturn', progressed_subject.saturn),
        ('Uranus', progressed_subject.uranus),
        ('Neptune', progressed_subject.neptune),
        ('Pluto', progressed_subject.pluto),
    ]

    progressed_planets = []
    for name, planet in planet_attrs:
        progressed_planets.append({
            "name": name,
            "sign": planet.sign,
            "degree": round(planet.position % 30, 2),
            "abs_position": round(planet.abs_pos, 2),
            "retrograde": getattr(planet, 'retrograde', False),
        })

    # PROGRESSED ANGLES section (ASC and MC)
    progressed_angles = [
        {
            "name": "ASC",
            "sign": progressed_subject.ascendant.sign,
            "degree": round(progressed_subject.ascendant.position % 30, 2),
            "abs_position": round(progressed_subject.ascendant.abs_pos, 2),
        },
        {
            "name": "MC",
            "sign": progressed_subject.medium_coeli.sign,
            "degree": round(progressed_subject.medium_coeli.position % 30, 2),
            "abs_position": round(progressed_subject.medium_coeli.abs_pos, 2),
        },
    ]

    # PROGRESSED ASPECTS section (progressed-to-natal, 1-degree orb)
    aspects_model = AspectsFactory.dual_chart_aspects(
        progressed_subject,
        natal_subject,
        active_points=MAJOR_PLANETS,
        active_aspects=PROG_DEFAULT_ORBS,
        second_subject_is_fixed=True,
    )

    progressed_aspects = []
    for asp in aspects_model.aspects:
        if asp.p1_name in MAJOR_PLANETS and asp.p2_name in MAJOR_PLANETS:
            progressed_aspects.append({
                "progressed_planet": asp.p1_name,
                "natal_planet": asp.p2_name,
                "aspect": asp.aspect,
                "orb": round(asp.orbit, 2),
                "applying": asp.aspect_movement == 'Applying',
                "movement": asp.aspect_movement,
            })

    # MONTHLY MOON section
    monthly_moon = build_monthly_moon(birth_jd, prog_year, natal_lat, natal_lng, natal_tz_str)

    # DISTRIBUTION SHIFT section
    def compute_distributions_for_subject(subject):
        """Compute element and modality counts for 10 planets + ASC."""
        planet_bodies = [
            ('Sun', subject.sun), ('Moon', subject.moon),
            ('Mercury', subject.mercury), ('Venus', subject.venus),
            ('Mars', subject.mars), ('Jupiter', subject.jupiter),
            ('Saturn', subject.saturn), ('Uranus', subject.uranus),
            ('Neptune', subject.neptune), ('Pluto', subject.pluto),
        ]
        placements = planet_bodies + [('ASC', subject.ascendant)]
        elem = {'Fire': 0, 'Earth': 0, 'Air': 0, 'Water': 0}
        mod = {'Cardinal': 0, 'Fixed': 0, 'Mutable': 0}
        for name, body in placements:
            e = ELEMENT_MAP.get(body.sign)
            m = MODALITY_MAP.get(body.sign)
            if e:
                elem[e] += 1
            if m:
                mod[m] += 1
        return elem, mod

    natal_elem, natal_mod = compute_distributions_for_subject(natal_subject)
    prog_elem, prog_mod = compute_distributions_for_subject(progressed_subject)

    distribution_shift = {
        "elements": {
            element: {
                "natal": natal_elem[element],
                "progressed": prog_elem[element],
                "delta": prog_elem[element] - natal_elem[element],
            }
            for element in ['Fire', 'Earth', 'Air', 'Water']
        },
        "modalities": {
            modality: {
                "natal": natal_mod[modality],
                "progressed": prog_mod[modality],
                "delta": prog_mod[modality] - natal_mod[modality],
            }
            for modality in ['Cardinal', 'Fixed', 'Mutable']
        }
    }

    return {
        "meta": meta,
        "progressed_planets": progressed_planets,
        "progressed_angles": progressed_angles,
        "progressed_aspects": progressed_aspects,
        "monthly_moon": monthly_moon,
        "distribution_shift": distribution_shift,
    }


def calculate_progressions(args):
    """
    Orchestrate secondary progressions calculation for an existing natal profile.

    Loads the natal profile identified by args.progressions, computes the progressed
    Julian Day using the day-for-a-year formula, creates a progressed subject at the
    natal location, and prints the complete progressions JSON to stdout.

    Args:
        args: Parsed argparse Namespace with .progressions (slug), .target_date,
              .age (int or None), and .prog_year (int or None)

    Returns:
        0 on success, 1 on error
    """
    try:
        # Load natal chart profile
        natal_subject, natal_data = load_natal_profile(args.progressions)

        natal_meta = natal_data.get('meta', {})
        location = natal_meta.get('location', {})
        natal_lat = float(location['latitude'])
        natal_lng = float(location['longitude'])
        natal_tz = location['timezone']

        # Extract birth date/time and compute birth JD
        birth_date_str = natal_meta['birth_date']
        birth_time_str = natal_meta['birth_time']
        birth_dt = datetime.strptime(birth_date_str + ' ' + birth_time_str, "%Y-%m-%d %H:%M")
        birth_jd = swe.julday(birth_dt.year, birth_dt.month, birth_dt.day,
                              birth_dt.hour + birth_dt.minute / 60.0)

        # Validate: cannot use both --age and --target-date
        if args.age is not None and args.target_date is not None:
            print("Error: Cannot use both --age and --target-date", file=sys.stderr)
            return 1

        # Determine target JD and target_date_str
        if args.age is not None:
            target_jd = birth_jd + args.age * 365.25
            target_date_str = None  # will be computed in build_progressed_json
        elif args.target_date is not None:
            target_jd = swe.julday(args.target_date.year, args.target_date.month,
                                   args.target_date.day, 12.0)
            target_date_str = args.target_date.strftime("%Y-%m-%d")
        else:
            # Default: today UTC noon
            today = datetime.now(timezone.utc)
            target_jd = swe.julday(today.year, today.month, today.day, 12.0)
            target_date_str = today.strftime("%Y-%m-%d")

        # Compute progressed JD
        prog_jd = compute_progressed_jd(birth_jd, target_jd)
        py, pm, pd, ph = swe.revjul(prog_jd)
        prog_hour = int(ph)
        prog_minute = int((ph - prog_hour) * 60)

        # Create progressed subject using natal location (CRITICAL: not lat=0.0, lng=0.0)
        progressed_subject = AstrologicalSubjectFactory.from_birth_data(
            name='Progressed',
            year=int(py), month=int(pm), day=int(pd),
            hour=prog_hour, minute=prog_minute,
            lat=natal_lat, lng=natal_lng, tz_str=natal_tz,
            online=False, houses_system_identifier='P',
        )

        # Determine prog_year for monthly Moon report
        if args.prog_year is not None:
            prog_year = args.prog_year
        elif args.age is not None:
            prog_year = birth_dt.year + args.age
        elif args.target_date is not None:
            prog_year = args.target_date.year
        else:
            prog_year = datetime.now(timezone.utc).year

        # Assemble and print progressions JSON
        prog_dict = build_progressed_json(
            progressed_subject, natal_subject, natal_data,
            args.progressions, target_date_str, target_jd, birth_jd,
            prog_year=prog_year,
        )
        print(json.dumps(prog_dict, indent=2))

        if args.save:
            date_str = prog_dict['meta'].get('target_date', 'unknown')
            try:
                out_path = save_snapshot(CHARTS_DIR / args.progressions, 'progressions', date_str, prog_dict)
                print(f"Snapshot saved: {out_path}", file=sys.stderr)
            except Exception as e:
                print(f"Warning: Could not save snapshot: {e}", file=sys.stderr)

        return 0

    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error calculating progressions: {e}", file=sys.stderr)
        return 1


def compute_solar_arc(birth_jd, target_jd, natal_sun_lon, method='true'):
    """
    Compute the solar arc for a target date.

    Two methods supported:
    - 'true': actual distance the progressed Sun has traveled (swe.calc_ut)
    - 'mean': Naibod constant rate (0.98564733 degrees/year)

    Args:
        birth_jd: Julian Day number of the birth moment
        target_jd: Julian Day number of the target date
        natal_sun_lon: Natal Sun absolute longitude (from chart.json abs_position)
        method: 'true' (default) or 'mean'

    Returns:
        float: Solar arc in degrees (0-360)
    """
    elapsed_years = (target_jd - birth_jd) / 365.25
    if method == 'mean':
        return (elapsed_years * NAIBOD_ARC) % 360
    # True arc: progressed Sun longitude - natal Sun longitude
    # Reuse compute_progressed_jd() from Phase 9 for consistent JD arithmetic
    progressed_jd = compute_progressed_jd(birth_jd, target_jd)
    prog_sun_data, _ = swe.calc_ut(progressed_jd, swe.SUN)
    prog_sun_lon = prog_sun_data[0]
    return (prog_sun_lon - natal_sun_lon) % 360


def angular_distance(lon1, lon2):
    """
    Compute the smallest angular distance between two ecliptic longitudes.

    Args:
        lon1: First longitude in degrees (0-360)
        lon2: Second longitude in degrees (0-360)

    Returns:
        float: Angular distance in degrees (0-180)
    """
    diff = abs(lon1 - lon2) % 360
    return 360 - diff if diff > 180 else diff


def build_sarc_aspects(directed_positions, natal_positions, orbs=None):
    """
    Find aspects between SA directed positions and natal positions.

    Uses manual nested-loop calculation (no AspectsFactory) because directed
    positions are not a Kerykeion AstrologicalSubjectModel.

    Args:
        directed_positions: dict of {name: directed_longitude}
        natal_positions: dict of {name: natal_longitude}
        orbs: dict of {aspect_name: max_orb}, defaults to SARC_DEFAULT_ORBS

    Returns:
        list: Aspect dicts sorted by orb ascending
    """
    if orbs is None:
        orbs = SARC_DEFAULT_ORBS

    aspects = []
    for d_name, d_lon in directed_positions.items():
        for n_name, n_lon in natal_positions.items():
            # Skip self-aspects: directed and natal point with same name are redundant
            if d_name == n_name:
                continue
            dist = angular_distance(d_lon, n_lon)
            for asp_name, asp_angle in SARC_ASPECT_ANGLES.items():
                orb = abs(dist - asp_angle)
                if orb <= orbs.get(asp_name, 1.0):
                    aspects.append({
                        'directed_point': d_name,
                        'natal_point': n_name,
                        'aspect': asp_name,
                        'orb': round(orb, 3),
                    })
    return sorted(aspects, key=lambda x: x['orb'])


def build_solar_arc_json(natal_data, slug, birth_jd, target_jd, arc, arc_method):
    """
    Assemble the complete solar arc directions JSON dict.

    Args:
        natal_data: Parsed natal chart.json dict
        slug: Profile slug string
        birth_jd: Julian Day number of birth
        target_jd: Julian Day number of target date
        arc: Solar arc in degrees (float)
        arc_method: 'true' or 'mean'

    Returns:
        dict: Complete solar arc directions output
    """
    elapsed_years = (target_jd - birth_jd) / 365.25

    # Derive target date string from JD
    y, m, d, h = swe.revjul(target_jd)
    target_date_str = f"{int(y):04d}-{int(m):02d}-{int(d):02d}"

    # Build meta section
    natal_meta = natal_data.get('meta', {})
    natal_name = natal_meta.get('name', slug)
    meta = {
        'natal_name': natal_name,
        'natal_slug': slug,
        'target_date': target_date_str,
        'arc_degrees': round(arc, 3),
        'arc_method': arc_method,
        'elapsed_years': round(elapsed_years, 2),
        'chart_type': 'solar_arc_directions',
        'calculated_at': datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S+00:00'),
        'orbs_used': SARC_DEFAULT_ORBS,
    }

    # Extract natal planet positions (10 major planets)
    natal_planets = {
        p['name']: p['abs_position']
        for p in natal_data['planets']
        if p['name'] in MAJOR_PLANETS
    }

    # Extract natal angle positions (ASC and MC)
    natal_angles = {
        a['name']: a['abs_position']
        for a in natal_data['angles']
        if a['name'] in ['ASC', 'MC']
    }

    # Combine natal positions for aspect calculation
    all_natal = {**natal_planets, **natal_angles}

    # Compute directed positions: add arc to every natal longitude
    directed_positions = {name: (lon + arc) % 360 for name, lon in all_natal.items()}

    # Build directed_planets list in MAJOR_PLANETS order
    # Build lookup for natal planet data (sign, degree) from natal_data
    natal_planet_lookup = {p['name']: p for p in natal_data['planets']}
    directed_planets = []
    for planet_name in MAJOR_PLANETS:
        if planet_name not in natal_planet_lookup:
            continue
        natal_p = natal_planet_lookup[planet_name]
        natal_abs = natal_p['abs_position']
        directed_abs = directed_positions[planet_name]
        dir_sign, dir_degree = position_to_sign_degree(directed_abs)
        directed_planets.append({
            'name': planet_name,
            'natal_sign': natal_p.get('sign', ''),
            'natal_degree': round(natal_p.get('degree', 0.0), 2),
            'natal_abs_position': round(natal_abs, 3),
            'directed_abs_position': round(directed_abs, 3),
            'directed_sign': dir_sign,
            'directed_degree': round(dir_degree, 2),
        })

    # Build directed_angles list (ASC then MC)
    natal_angle_lookup = {a['name']: a for a in natal_data['angles']}
    directed_angles = []
    for angle_name in ['ASC', 'MC']:
        if angle_name not in natal_angle_lookup:
            continue
        natal_a = natal_angle_lookup[angle_name]
        natal_abs = natal_a['abs_position']
        directed_abs = directed_positions[angle_name]
        dir_sign, dir_degree = position_to_sign_degree(directed_abs)
        directed_angles.append({
            'name': angle_name,
            'natal_abs_position': round(natal_abs, 3),
            'directed_abs_position': round(directed_abs, 3),
            'directed_sign': dir_sign,
            'directed_degree': round(dir_degree, 2),
        })

    # Compute aspects with applying/separating detection
    aspects_raw = build_sarc_aspects(directed_positions, all_natal)

    # Compute arc one year forward for applying/separating detection
    natal_sun_lon = natal_planets.get('Sun', 0.0)
    arc_future = compute_solar_arc(birth_jd, target_jd + 365.25, natal_sun_lon, method=arc_method)

    aspects = []
    for asp in aspects_raw:
        d_name = asp['directed_point']
        n_name = asp['natal_point']
        asp_name = asp['aspect']
        asp_angle = SARC_ASPECT_ANGLES[asp_name]

        natal_lon_of_directed = all_natal.get(d_name, 0.0)
        natal_lon_of_natal = all_natal.get(n_name, 0.0)

        # Current orb
        current_orb = asp['orb']

        # Future directed position (1 year forward)
        directed_lon_future = (natal_lon_of_directed + arc_future) % 360

        # Future orb
        orb_future = abs(angular_distance(directed_lon_future, natal_lon_of_natal) - asp_angle)

        movement = 'Applying' if orb_future < current_orb else 'Separating'

        aspects.append({
            'directed_point': d_name,
            'natal_point': n_name,
            'aspect': asp_name,
            'orb': current_orb,
            'movement': movement,
        })

    return {
        'meta': meta,
        'directed_planets': directed_planets,
        'directed_angles': directed_angles,
        'aspects': aspects,
    }


def calculate_solar_arcs(args):
    """
    Orchestrate solar arc directions calculation for an existing natal profile.

    Loads natal profile, computes arc (true or mean method), applies arc to all
    natal positions, finds SA-to-natal aspects, and outputs JSON to stdout.

    Args:
        args: Parsed argparse namespace (solar_arcs, target_date, age, arc_method)

    Returns:
        int: Exit code (0 = success, 1 = error)
    """
    try:
        natal_subject, natal_data = load_natal_profile(args.solar_arcs)

        natal_meta = natal_data.get('meta', {})
        birth_date_str = natal_meta['birth_date']
        birth_time_str = natal_meta['birth_time']
        birth_dt = datetime.strptime(birth_date_str + ' ' + birth_time_str, "%Y-%m-%d %H:%M")
        birth_jd = swe.julday(birth_dt.year, birth_dt.month, birth_dt.day,
                              birth_dt.hour + birth_dt.minute / 60.0)

        # Validate mutually exclusive --age and --target-date
        if args.age is not None and args.target_date is not None:
            print("Error: --age and --target-date are mutually exclusive", file=sys.stderr)
            return 1

        # Determine target Julian Day
        if args.age is not None:
            target_jd = birth_jd + args.age * 365.25
        elif args.target_date is not None:
            target_jd = swe.julday(args.target_date.year, args.target_date.month,
                                   args.target_date.day, 12.0)
        else:
            today = datetime.now(timezone.utc)
            target_jd = swe.julday(today.year, today.month, today.day, 12.0)

        # Get arc method (default: 'true')
        arc_method = getattr(args, 'arc_method', 'true')

        # Get natal Sun longitude from profile
        natal_sun_lon = next(
            p['abs_position'] for p in natal_data['planets'] if p['name'] == 'Sun'
        )

        # Compute solar arc
        arc = compute_solar_arc(birth_jd, target_jd, natal_sun_lon, method=arc_method)

        # Build and emit JSON
        sarc_dict = build_solar_arc_json(natal_data, args.solar_arcs, birth_jd, target_jd, arc, arc_method)
        print(json.dumps(sarc_dict, indent=2))

        if args.save:
            date_str = sarc_dict['meta'].get('target_date', 'unknown')
            try:
                out_path = save_snapshot(CHARTS_DIR / args.solar_arcs, 'solar-arc', date_str, sarc_dict)
                print(f"Snapshot saved: {out_path}", file=sys.stderr)
            except Exception as e:
                print(f"Warning: Could not save snapshot: {e}", file=sys.stderr)

        return 0

    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error calculating solar arc directions: {e}", file=sys.stderr)
        return 1


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


def check_existing_profile(profile_dir, person_name):
    """
    Check if profile exists and display existing data. Returns True if ok to proceed.

    Args:
        profile_dir: Path to the profile directory
        person_name: Name of the person (for display)

    Returns:
        True if profile doesn't exist (ok to proceed), False if exists (needs confirmation)
    """
    chart_json = profile_dir / "chart.json"
    if not chart_json.exists():
        return True  # No existing profile, proceed

    # Load and display existing birth details
    with open(chart_json, 'r', encoding='utf-8') as f:
        existing = json.load(f)

    meta = existing.get('meta', {})
    loc = meta.get('location', {})
    print(f"\nWARNING: Profile '{person_name}' already exists")
    print(f"  Birth date: {meta.get('birth_date', 'Unknown')}")
    print(f"  Birth time: {meta.get('birth_time', 'Unknown')}")
    print(f"  Location:   {loc.get('city', 'N/A')}, {loc.get('nation', 'N/A')}")
    print(f"  Lat/Lng:    {loc.get('latitude', 'N/A')}, {loc.get('longitude', 'N/A')}")
    print(f"  Timezone:   {loc.get('timezone', 'N/A')}")
    print(f"  Generated:  {meta.get('generated_at', 'Unknown')}")
    print()

    # In non-interactive mode (piped input), default to not overwriting
    # For script use, require --force flag
    return False  # Signal that confirmation is needed


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
        "slug": slugify(args.name),
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


def list_profiles():
    """
    List all existing chart profiles with person names and birth details.

    Returns:
        0 on success
    """
    if not CHARTS_DIR.exists():
        print("No chart profiles found")
        print(f"(Directory {CHARTS_DIR} does not exist)")
        return 0

    # Get all profile directories, skip hidden files
    profiles = [
        d for d in CHARTS_DIR.iterdir()
        if d.is_dir() and not d.name.startswith('.')
    ]

    if not profiles:
        print("No chart profiles found")
        return 0

    print(f"Found {len(profiles)} chart profile(s):\n")

    for profile_dir in sorted(profiles):
        chart_json = profile_dir / "chart.json"
        chart_svg = profile_dir / "chart.svg"

        # Display profile slug as header
        print(f"  {profile_dir.name}/")

        # Read chart.json for person details
        if chart_json.exists():
            try:
                with open(chart_json, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                meta = data.get('meta', {})
                loc = meta.get('location', {})
                print(f"    Name:     {meta.get('name', 'Unknown')}")
                print(f"    Born:     {meta.get('birth_date', '?')} at {meta.get('birth_time', '?')}")
                city = loc.get('city')
                nation = loc.get('nation')
                if city and nation:
                    print(f"    Location: {city}, {nation}")
                else:
                    print(f"    Location: {loc.get('latitude', '?')}, {loc.get('longitude', '?')} ({loc.get('timezone', '?')})")
            except (json.JSONDecodeError, KeyError):
                print("    (invalid chart data)")

        # Show file status
        files = []
        if chart_json.exists(): files.append("chart.json")
        if chart_svg.exists(): files.append("chart.svg")
        print(f"    Files:    {', '.join(files) if files else 'none'}")
        print()

    return 0


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

    # Positional argument (optional when using --list)
    parser.add_argument(
        "name",
        nargs="?",
        help="Person's name"
    )

    # Required arguments (when not using --list)
    parser.add_argument(
        "--date",
        type=valid_date,
        help="Birth date in YYYY-MM-DD format"
    )

    parser.add_argument(
        "--time",
        type=valid_time,
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

    parser.add_argument(
        "--list",
        action="store_true",
        help="List all existing chart profiles"
    )

    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing profile without confirmation"
    )

    parser.add_argument(
        '--save',
        action='store_true',
        help='Save snapshot to profile directory with date-based filename'
    )

    parser.add_argument(
        '--transits',
        metavar='SLUG',
        help='Calculate transits for an existing chart profile (e.g., albert-einstein)'
    )

    parser.add_argument(
        '--query-date',
        type=valid_query_date,
        default=None,
        help='Date for transit calculation YYYY-MM-DD (default: current UTC time)'
    )

    parser.add_argument(
        '--timeline',
        metavar='SLUG',
        help='Generate transit timeline for an existing chart profile (e.g., albert-einstein)'
    )
    parser.add_argument(
        '--range',
        choices=['week', '30d', '3m', 'year'],
        default='30d',
        help='Preset date range for timeline (default: 30d). Ignored if --start/--end given.'
    )
    parser.add_argument(
        '--start',
        type=valid_query_date,
        default=None,
        help='Custom timeline start date YYYY-MM-DD (requires --end)'
    )
    parser.add_argument(
        '--end',
        type=valid_query_date,
        default=None,
        help='Custom timeline end date YYYY-MM-DD (requires --start)'
    )

    parser.add_argument(
        '--progressions',
        metavar='SLUG',
        help='Calculate secondary progressions for an existing chart profile (e.g., albert-einstein)'
    )
    parser.add_argument(
        '--target-date',
        type=valid_query_date,
        default=None,
        dest='target_date',
        help='Target date for progressions YYYY-MM-DD (default: today UTC)'
    )
    parser.add_argument(
        '--age',
        type=int,
        default=None,
        help='Target age in whole years for progressions (alternative to --target-date)'
    )
    parser.add_argument(
        '--prog-year',
        type=int,
        default=None,
        dest='prog_year',
        help='Year for monthly progressed Moon report (default: year of target date)'
    )
    parser.add_argument(
        '--solar-arcs',
        metavar='SLUG',
        dest='solar_arcs',
        help='Calculate solar arc directions for an existing chart profile (e.g., albert-einstein)'
    )
    parser.add_argument(
        '--arc-method',
        choices=['true', 'mean'],
        default='true',
        dest='arc_method',
        help='Solar arc calculation method: true (default, actual progressed Sun) or mean (Naibod constant)'
    )

    try:
        args = parser.parse_args()

        # Handle --list flag
        if args.list:
            return list_profiles()

        # Handle --solar-arcs flag (MUST come before --progressions, --timeline, --transits)
        if args.solar_arcs:
            return calculate_solar_arcs(args)

        # Handle --progressions flag (MUST come before --timeline, --transits, and natal validation)
        if args.progressions:
            return calculate_progressions(args)

        # Handle --timeline flag (MUST come before --transits and natal validation)
        if args.timeline:
            return calculate_timeline(args)

        # Handle --transits flag (MUST come before natal validation)
        if args.transits:
            return calculate_transits(args)

        # Validate name is provided for chart generation
        if not args.name:
            parser.error("Name is required for chart generation (or use --list to list profiles)")

        # Validate date and time are provided for chart generation
        if not args.date:
            parser.error("--date is required for chart generation")
        if not args.time:
            parser.error("--time is required for chart generation")

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

        # Build comprehensive JSON structure
        chart_dict = build_chart_json(subject, args)

        # Save to profile directory
        profile_slug = slugify(args.name)
        profile_dir = CHARTS_DIR / profile_slug

        # Check for existing profile
        if not args.force and not check_existing_profile(profile_dir, args.name):
            print("Use --force to overwrite existing profile")
            return 1

        # Create directory and save files
        profile_dir.mkdir(parents=True, exist_ok=True)

        # Write chart.json
        json_file = profile_dir / "chart.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(chart_dict, f, indent=2, ensure_ascii=False)

        # Generate SVG using ChartDrawer
        try:
            # Try ChartDataFactory approach first (5.7.2 API)
            try:
                from kerykeion.chart_data_factory import ChartDataFactory
                chart_data = ChartDataFactory.create_natal_chart_data(subject)
                drawer = ChartDrawer(chart_data=chart_data)
                drawer.save_svg(output_path=str(profile_dir), filename="chart", remove_css_variables=True)
            except (ImportError, AttributeError):
                # Fall back to direct subject approach
                drawer = ChartDrawer(subject)
                drawer.save_svg(output_path=str(profile_dir), filename="chart")

            # Kerykeion may create files with different names - find and rename if needed
            svg_files = list(profile_dir.glob("chart*.svg"))
            if svg_files:
                # If the file isn't exactly "chart.svg", rename it
                if svg_files[0].name != "chart.svg":
                    svg_files[0].rename(profile_dir / "chart.svg")

            svg_file = profile_dir / "chart.svg"
            if not svg_file.exists():
                print(f"Warning: SVG generation may have failed - chart.svg not found", file=sys.stderr)

        except Exception as e:
            print(f"Warning: SVG generation failed: {e}", file=sys.stderr)

        # Print confirmation
        print(f"\n=== CHART SAVED ===")
        print(f"Profile: {args.name}")
        print(f"Location: {profile_dir.absolute()}")
        if json_file.exists():
            print(f"  - chart.json ({json_file.stat().st_size} bytes)")
        if (profile_dir / "chart.svg").exists():
            print(f"  - chart.svg ({(profile_dir / 'chart.svg').stat().st_size} bytes)")

        return 0

    except Exception as e:
        print(f"Error creating chart: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
