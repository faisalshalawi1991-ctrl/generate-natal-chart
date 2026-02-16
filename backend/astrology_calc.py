#!/usr/bin/env python3
"""
Astrology calculation CLI script.

Accepts birth data (name, date, time, latitude, longitude, timezone) via command-line
arguments and generates an astrological birth chart using Kerykeion in offline mode.
"""

import argparse
import sys
import os
from pathlib import Path
from datetime import datetime

from kerykeion import AstrologicalSubjectFactory, NatalAspects, KerykeionException


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
                    'houses_system_identifier': 'P'
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
                houses_system_identifier='P'
            )

        # Verify Placidus house system
        if subject.houses_system_identifier != "P":
            print(f"Warning: Expected Placidus (P), got {subject.houses_system_identifier}", file=sys.stderr)

        # Temporary confirmation message
        print(f"Chart calculated successfully for {args.name}")

        return 0

    except Exception as e:
        print(f"Error creating chart: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
