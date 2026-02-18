import os
import sys
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Load .env
load_dotenv()

database_url = os.getenv("DATABASE_URL")
if not database_url:
    print("DATABASE_URL not found")
    sys.exit(1)

print(f"Connecting to: {database_url}")

try:
    # SSL requirement for Azure
    connect_args = {
        "ssl": {
            "ssl": True,
            "ssl_verify_cert": False,
            "ssl_verify_identity": False
        }
    }
    engine = create_engine(database_url, connect_args=connect_args)
    with engine.connect() as connection:
        # Check current time in DB
        result = connection.execute(text("SELECT NOW(), @@global.time_zone, @@session.time_zone;"))
        row = result.fetchone()
        print(f"DB NOW(): {row[0]}")
        print(f"DB Global TZ: {row[1]}")
        print(f"DB Session TZ: {row[2]}")
        
        # Check latest items
        print("\nLatest 5 Logistics Items:")
        result = connection.execute(text("SELECT tracking_number, status, created_at, completed_at, destination FROM logistics_item ORDER BY created_at DESC LIMIT 5;"))
        for row in result:
             print(f"ID: {row[0]}, Status: {row[1]}, Created: {row[2]}, Dest: {row[4]}")

except Exception as e:
    print(f"Error: {e}")
