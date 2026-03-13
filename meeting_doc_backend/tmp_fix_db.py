from django.db import connection

def run_sql():
    with connection.cursor() as cursor:
        try:
            cursor.execute("ALTER TABLE meetings_meeting ADD COLUMN IF NOT EXISTS session_key VARCHAR(40) DEFAULT '';")
            print("session_key column added or already exists.")
        except Exception as e:
            print(f"Error adding session_key: {e}")

        try:
            cursor.execute("CREATE INDEX IF NOT EXISTS meetings_meeting_session_key_idx ON meetings_meeting(session_key);")
            print("session_key index created or already exists.")
        except Exception as e:
            print(f"Error creating index: {e}")

        # Also remove unique from video_id if it exists
        try:
            cursor.execute("ALTER TABLE meetings_meeting DROP CONSTRAINT IF EXISTS meetings_meeting_video_id_key;")
            print("Dropped unique constraint on video_id.")
        except Exception as e:
            print(f"Error dropping constraint: {e}")

if __name__ == "__main__":
    import os
    import django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    django.setup()
    run_sql()
