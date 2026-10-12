import sqlite3


def create_database():

    connection = sqlite3.connect(
        "database/irrigation.db"
    )

    cursor = connection.cursor()

    # Farmer / farm details
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS farms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            farm_name TEXT,
            location TEXT,
            crop TEXT,
            planting_date TEXT,
            field_area REAL,
            growth_stage TEXT,
            mode TEXT
        )
    """)

    # Irrigation prediction history
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            crop TEXT,
            mode TEXT,
            temperature REAL,
            humidity REAL,
            rainfall REAL,
            soil_moisture REAL,
            irrigation TEXT,
            water_required REAL,
            pump_duration REAL,
            recommendation TEXT,
            date_time TEXT
        )
    """)

    connection.commit()
    connection.close()

    print("Database created successfully!")


if __name__ == "__main__":
    create_database()