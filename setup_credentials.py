#!/usr/bin/env python3
"""
Configure Smart LMS credentials from the terminal.
Password is entered securely via getpass (not echoed).

Usage:
    python setup_credentials.py
    python setup_credentials.py --username student@isik.edu.tr
"""
import argparse
import getpass
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from smart_lms.config import store_lms_credentials, get_lms_credentials, get_config
from lms_scraper import LMSScraper


def main():
    parser = argparse.ArgumentParser(description="Set Smart LMS / Moodle credentials")
    parser.add_argument("--username", "-u", help="Moodle username (email)")
    parser.add_argument("--no-verify", action="store_true", help="Skip login test")
    args = parser.parse_args()

    cfg = get_config()
    lms_url = cfg.get("lms_base_url", "")

    print(f"Smart LMS — Credential Setup")
    print(f"LMS: {lms_url}")
    print()

    existing_user, existing_pass = get_lms_credentials()
    if existing_user:
        print(f"Currently saved username: {existing_user}")
        overwrite = input("Overwrite? [y/N] ").strip().lower()
        if overwrite != "y":
            print("Aborted.")
            return

    username = args.username or input("Username (email): ").strip()
    if not username:
        print("Error: username cannot be empty.", file=sys.stderr)
        sys.exit(1)

    password = getpass.getpass("Password (input hidden): ")
    if not password:
        print("Error: password cannot be empty.", file=sys.stderr)
        sys.exit(1)

    store_lms_credentials(username, password)
    print("Credentials saved to system keychain.")

    if not args.no_verify:
        print("Testing login…", end=" ", flush=True)
        try:
            scraper = LMSScraper(base_url=lms_url)
            ok = scraper.login_test(username, password)
        except Exception as e:
            print(f"FAILED\nError: {e}", file=sys.stderr)
            sys.exit(1)

        if ok:
            print("OK ✓")
        else:
            print("FAILED\nCheck your username and password.")
            sys.exit(1)


if __name__ == "__main__":
    main()
