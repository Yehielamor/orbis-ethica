import sqlite3
import os

DB_PATH = "orbis_ethica.db"

def migrate():
    if not os.path.exists(DB_PATH):
        print(f"❌ Database not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # 1. Create blocks table
        print("Creating blocks table...")
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS blocks (
            "index" INTEGER NOT NULL, 
            hash VARCHAR NOT NULL, 
            previous_hash VARCHAR NOT NULL, 
            timestamp DATETIME, 
            validator_id VARCHAR NOT NULL, 
            signature VARCHAR NOT NULL, 
            PRIMARY KEY ("index"), 
            UNIQUE (hash)
        );
        """)

        # 2. Add block_hash column to ledger_entries if not exists
        print("Checking ledger_entries schema...")
        cursor.execute("PRAGMA table_info(ledger_entries)")
        columns = [info[1] for info in cursor.fetchall()]
        
        if "block_hash" not in columns:
            print("Adding block_hash column to ledger_entries...")
            cursor.execute("ALTER TABLE ledger_entries ADD COLUMN block_hash VARCHAR REFERENCES blocks(hash)")
        else:
            print("block_hash column already exists.")

        conn.commit()
        print("✅ Schema update complete!")

    except Exception as e:
        print(f"❌ Migration failed: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
