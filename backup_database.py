import sqlite3
from pathlib import Path
from datetime import datetime

PROJECT_DIR = Path(__file__).resolve().parent
DATABASE = PROJECT_DIR / "students.db"
BACKUP_DIR = PROJECT_DIR.parent / "StudentDeveloperHub_Backups"

def backup_database():
    if not DATABASE.exists():
        print("Database file not found.")
        return

    BACKUP_DIR.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    backup_file = BACKUP_DIR / f"students_{timestamp}.db"

    try:
        with sqlite3.connect(DATABASE) as source:
            with sqlite3.connect(backup_file) as destination:
                source.backup(destination)

        print(f"Backup completed: {backup_file}")

    except sqlite3.Error as error:
        print(f"Backup failed: {error}")
        if backup_file.exists():
            backup_file.unlink()

if __name__ == "__main__":
    backup_database()