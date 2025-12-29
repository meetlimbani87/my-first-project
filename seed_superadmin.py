"""
Script to create initial Super Admin user.

Usage:
    python seed_superadmin.py

This script reads SUPER_ADMIN_EMAIL and SUPER_ADMIN_PASSWORD from .env file
and creates a Super Admin user if one doesn't exist.
"""

import asyncio
import sys
from sqlalchemy import select
from app.core.database import AsyncSessionLocal, init_db
from app.core.config import settings
from app.core.security import hash_password
from app.models import User, UserRole


async def seed_super_admin():
    """Create initial Super Admin user"""
    print("=" * 60)
    print("Crime Report Management System - Super Admin Seeder")
    print("=" * 60)

    # Initialize database
    print("\nInitializing database...")
    try:
        await init_db()
        print("✓ Database initialized successfully")
    except Exception as e:
        print(f"✗ Failed to initialize database: {e}")
        sys.exit(1)

    # Get credentials from settings
    email = settings.SUPER_ADMIN_EMAIL.lower()
    password = settings.SUPER_ADMIN_PASSWORD

    print(f"\nAttempting to create Super Admin:")
    print(f"  Email: {email}")

    async with AsyncSessionLocal() as db:
        try:
            # Check if user exists
            stmt = select(User).where(User.email == email)
            result = await db.execute(stmt)
            existing_user = result.scalar_one_or_none()

            if existing_user:
                if existing_user.role == UserRole.SUPER_ADMIN:
                    print(f"\n✓ Super Admin already exists with email: {email}")
                    print(f"  User ID: {existing_user.id}")
                    print(f"  Role: {existing_user.role.value}")
                    print(f"  Created: {existing_user.created_at}")
                else:
                    # Update existing user to Super Admin
                    print(f"\n⚠ User exists with role {existing_user.role.value}")
                    print("  Upgrading to SUPER_ADMIN...")

                    existing_user.role = UserRole.SUPER_ADMIN
                    await db.commit()

                    print(f"✓ User upgraded to Super Admin successfully")
                    print(f"  User ID: {existing_user.id}")
                    print(f"  Email: {existing_user.email}")
            else:
                # Create new Super Admin
                print("\n⚙ Creating new Super Admin user...")

                super_admin = User(
                    email=email,
                    password_hash=hash_password(password),
                    role=UserRole.SUPER_ADMIN,
                    is_active=True,
                    is_locked=False
                )

                db.add(super_admin)
                await db.commit()
                await db.refresh(super_admin)

                print(f"✓ Super Admin created successfully!")
                print(f"  User ID: {super_admin.id}")
                print(f"  Email: {super_admin.email}")
                print(f"  Role: {super_admin.role.value}")
                print(f"  Created: {super_admin.created_at}")

            print("\n" + "=" * 60)
            print("SUPER ADMIN CREDENTIALS")
            print("=" * 60)
            print(f"Email:    {email}")
            print(f"Password: {password}")
            print("=" * 60)
            print("\n⚠ IMPORTANT: Change the default password in production!")
            print("⚠ Store these credentials securely.\n")

        except Exception as e:
            print(f"\n✗ Error creating Super Admin: {e}")
            sys.exit(1)


def main():
    """Main entry point"""
    try:
        asyncio.run(seed_super_admin())
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.")
        sys.exit(0)


if __name__ == "__main__":
    main()
