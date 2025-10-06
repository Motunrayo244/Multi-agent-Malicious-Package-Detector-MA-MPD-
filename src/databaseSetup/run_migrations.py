import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import os
from dotenv import load_dotenv

load_dotenv()

# --- Database Configuration ---
DB_HOST = os.getenv("PG_DB_HOST", "localhost")
DB_PORT = os.getenv("PG_DB_PORT", "5432")
DB_NAME = os.getenv("PG_DB_NAME", "postgres")
DB_USER = os.getenv("PG_ADMIN_USER", "postgres")
DB_PASSWORD = os.getenv("PG_PASSWORD")
SCHEMA_NAME = os.getenv("MAS_MPD_SCHEMA", "public")

# --- Load SQL from file ---
MIGRATIONS_DIR = "migrations"


def get_migrations(migrations_dir: str=MIGRATIONS_DIR):
    migrations = ""
    migration_files = os.listdir(migrations_dir)
    for migration_file in migration_files:
        if migration_file.endswith(".sql"):
            with open(os.path.join(migrations_dir, migration_file), "r") as f:
                migrations += f.read() + "\n"
    return migrations

def run_migrations():
    sql_script = get_migrations(MIGRATIONS_DIR)
    connection = None
    cursor = None
    if not sql_script.strip():
        print("❌ No SQL migrations found.")
        return
    try:
        connection = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            
        )
        connection.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = connection.cursor()
        cursor.execute(sql_script)
        connection.commit()

        print("✅ migrations executed successfully.")
    except psycopg2.Error as e:
        print("❌ Error executing migrations:", e)
        if connection:
            connection.rollback() 

    except Exception as e:
        print("❌ Error creating tables:", e)

    finally:
        if connection:
            connection.close()

if __name__ == "__main__":
    run_migrations()
