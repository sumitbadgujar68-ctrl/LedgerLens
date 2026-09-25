"""Create or reset a LedgerLens investigator account (Phase 7 authentication bootstrap).

The password is read from the INVESTIGATOR_PASSWORD environment variable or an
interactive prompt; it is never accepted as a command-line argument so it
cannot leak through shell history or process listings.

Usage (from the backend directory):

    python scripts/create_investigator.py --username jane@agency.gov \
        --email jane@agency.gov --full-name "Jane Investigator"
"""

import argparse
import asyncio
import os
import sys
from getpass import getpass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select

from app.db.database import async_session_maker
from app.db.models import Investigator
from app.services.auth.security import hash_password

PASSWORD_ENV = "INVESTIGATOR_PASSWORD"


def parse_args(argv=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create or reset an investigator account")
    parser.add_argument("--username", required=True)
    parser.add_argument("--email", required=True)
    parser.add_argument("--full-name", required=True)
    parser.add_argument("--role", default="investigator", choices=["admin", "investigator", "viewer"])
    return parser.parse_args(argv)


def read_password() -> str:
    password = os.environ.get(PASSWORD_ENV)
    if password:
        return password
    password = getpass("Password (min 8 chars): ")
    confirmation = getpass("Confirm password: ")
    if password != confirmation:
        raise SystemExit("Passwords do not match")
    return password


async def apply(args: argparse.Namespace, password: str) -> Investigator:
    async with async_session_maker() as session:
        result = await session.execute(
            select(Investigator).where(Investigator.username == args.username)
        )
        investigator = result.scalar_one_or_none()
        password_hash = hash_password(password)
        if investigator is None:
            investigator = Investigator(
                username=args.username,
                email=args.email,
                full_name=args.full_name,
                role=args.role,
                active=True,
                password_hash=password_hash,
            )
            session.add(investigator)
        else:
            investigator.email = args.email
            investigator.full_name = args.full_name
            investigator.role = args.role
            investigator.active = True
            investigator.password_hash = password_hash
        await session.commit()
        await session.refresh(investigator)
        return investigator


def main(argv=None) -> int:
    args = parse_args(argv)
    password = read_password()
    if len(password) < 8:
        raise SystemExit("Password must be at least 8 characters")
    investigator = asyncio.run(apply(args, password))
    print(f"investigator ready: {investigator.username} ({investigator.investigator_id})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
