import sqlite3
from datetime import datetime

class TravelDatabase:
    def __init__(self, db_name="travel_assistant.db"):
        """Initialize the database connection and create the table if it doesn't exist."""
        self.db_name = db_name
        self._create_table()

    def _create_table(self):
        """Create the searches table if it doesn't exist."""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS searches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_message TEXT NOT NULL,
                bot_response TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        conn.close()

    def save_search(self, user_message, bot_response):
        """Save a user message and bot response to the database."""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO searches (user_message, bot_response)
            VALUES (?, ?)
        ''', (user_message, bot_response))
        conn.commit()
        conn.close()

    def get_search_history(self, limit=10):
        """Retrieve the latest search history entries."""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT user_message, bot_response, timestamp
            FROM searches
            ORDER BY timestamp DESC
            LIMIT ?
        ''', (limit,))
        history = cursor.fetchall()
        conn.close()
        return history

    def clear_search_history(self):
        """Clear all search history entries."""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM searches')
        conn.commit()
        conn.close()

# Example usage (uncomment to test)
if __name__ == "__main__":
    db = TravelDatabase()
    # Test saving a search
    db.save_search("Where is Paris?", "Paris is in France! Let me plan your trip.")
    # Test retrieving history
    history = db.get_search_history()
    for entry in history:
        print(f"Message: {entry[0]}, Response: {entry[1]}, Time: {entry[2]}")