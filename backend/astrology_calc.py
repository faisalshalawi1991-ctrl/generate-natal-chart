#!/usr/bin/env python3
"""
Astrology calculation CLI script.

Accepts birth data (name, date, time, latitude, longitude, timezone) via command-line
arguments and generates an astrological birth chart using Kerykeion in offline mode.
"""

import argparse
import sys
from pathlib import Path
from datetime import datetime

from kerykeion import AstrologicalSubjectFactory


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
        return datetime.strptime(s, "%Y-%m-%d")
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
Example:
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

    parser.add_argument(
        "--lat",
        type=valid_latitude,
        required=True,
        help="Birth location latitude (-90 to 90)"
    )

    parser.add_argument(
        "--lng",
        type=valid_longitude,
        required=True,
        help="Birth location longitude (-180 to 180)"
    )

    parser.add_argument(
        "--tz",
        type=str,
        required=True,
        help="IANA timezone string (e.g., 'America/New_York', 'Europe/Berlin')"
    )

    try:
        args = parser.parse_args()

        # Create AstrologicalSubject using Kerykeion in offline mode
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
            online=False
        )

        # Print confirmation with sun sign and position
        print(f"Chart created for {args.name} -- Sun in {subject.sun.sign} at {subject.sun.abs_pos:.2f} degrees")

        return 0

    except Exception as e:
        print(f"Error creating chart: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
