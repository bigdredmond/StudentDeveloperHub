import sqlite3
from pathlib import Path

backup_dir = Path(__file__).resolve().parent.parent / "StudentDeveloperHub_Backups"
backups = sorted(backup_dir.glob("students_*.db"))

if not backups:
    print("No timestamped backup found.")
else:
    backup_file = backups[-1]

    try:
        with sqlite3.connect(backup_file) as conn:
            result = conn.execute("PRAGMA integrity_check").fetchone()[0]

            if result == "ok":
                print("Backup is valid.")
                tables = conn.execute(
                    "SELECT name FROM sqlite_master "
                    "WHERE type = 'table' ORDER BY name"
                ).fetchall()
                print("Tables:", ", ".join(row[0] for row in tables))
            else:
                print("Integrity check failed:", result)

    except sqlite3.Error as error:
        print("Could not verify backup:", error)