from sqlalchemy.orm import Session
from sqlalchemy.sql import text
from app.db.database import SessionLocal
from datetime import datetime

# List of seeders to run
SEEDERS = [
    ("create_admin_role", "seed_admin_role"),
    ("create_admin_user", "seed_admin_user"),
]

def seed_admin_role(db: Session):
    """Seeder to create the Admin role."""
    from app.db.models import Role
    import json

    permissions = {
        "logs": True,
        "upload_to_s3": True,
        "configuration": True,
        "user_management": True,
        "download_from_s3": True,
    }

    role = db.query(Role).filter(Role.name == "Admin").first()
    if not role:
        role = Role(
            name="Admin",
            description="Role with all permissions",
            permissions=permissions,
            created_at=datetime.utcnow(),
        )
        db.add(role)
        db.commit()
        print("Admin role created.")


def seed_admin_user(db: Session):
    """Seeder to create the Admin user."""
    from app.db.models import User, Role

    role = db.query(Role).filter(Role.name == "Admin").first()
    if not role:
        raise Exception("Admin role does not exist. Run `create_admin_role` first.")

    user = db.query(User).filter(User.email == "santosh.sah@turing.com").first()
    if not user:
        user = User(
            email="santosh.sah@turing.com",
            name="Admin",
            role_id=role.id,
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.add(user)
        db.commit()
        print("Santosh user created.")

    user = db.query(User).filter(User.email == "bhavna.k@turing.com").first()
    if not user:
        user = User(
            email="bhavna.k@turing.com",
            name="Admin",
            role_id=role.id,
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.add(user)
        db.commit()
        print("Bhavna user created.")

    user = db.query(User).filter(User.email == "harshil.p1@turing.com").first()
    if not user:
        user = User(
            email="harshil.p1@turing.com",
            name="Admin",
            role_id=role.id,
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.add(user)
        db.commit()
        print("Harshil user created.")

    user = db.query(User).filter(User.email == "offem.p@turing.com").first()
    if not user:
        user = User(
            email="offem.p@turing.com",
            name="Admin",
            role_id=role.id,
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.add(user)
        db.commit()
        print("Offem user created.")

    user = db.query(User).filter(User.email == "ezeala.s@turing.com").first()
    if not user:
        user = User(
            email="ezeala.s@turing.com",
            name="Admin",
            role_id=role.id,
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.add(user)
        db.commit()
        print("Samuel user created.")

    user = db.query(User).filter(User.email == "sajjad.s@turing.com").first()
    if not user:
        user = User(
            email="sajjad.s@turing.com",
            name="Admin",
            role_id=role.id,
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.add(user)
        db.commit()
        print("Sajjad user created.")

def run_seeders():
    """Run all pending seeders."""
    db: Session = SessionLocal()
    try:
        # Ensure seeders table exists
        db.execute(
            text("""
            CREATE TABLE IF NOT EXISTS seeders (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL UNIQUE,
                run_at TIMESTAMP DEFAULT NOW()
            )
            """)
        )
        db.commit()

        for seeder_name, seeder_function in SEEDERS:
            # Check if seeder already ran
            result = db.execute(
                text("SELECT 1 FROM seeders WHERE name = :name"),
                {"name": seeder_name}
            ).fetchone()

            if not result:
                print(f"Running seeder: {seeder_name}")
                globals()[seeder_function](db)  # Call the seeder function
                db.execute(
                    text("INSERT INTO seeders (name) VALUES (:name)"),
                    {"name": seeder_name}
                )
                db.commit()
            else:
                print(f"Seeder {seeder_name} already ran.")

    except Exception as e:
        print(f"Error running seeders: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    run_seeders()
