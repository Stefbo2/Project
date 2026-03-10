from database.db import get_connection
from database.models import SCHEMA_STATEMENTS
from utils.seed_data import seed_demo_data


def initialize_database() -> None:
    with get_connection() as connection:
        for statement in SCHEMA_STATEMENTS:
            connection.execute(statement)
        connection.commit()

    seed_demo_data()


if __name__ == "__main__":
    initialize_database()
    print("Database initialized.")
