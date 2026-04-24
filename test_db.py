import database_manager as db
import pandas as pd

# Initialize DB (will seed data if not seeded)
db.initialize_db()

print("--- Testing Attendance Functions ---")
# 1. Test mark_attendance
db.mark_attendance("Test User", "Present")
print("✅ Logged 'Test User' attendance.")

# 2. Test get_attendance_logs (All)
all_logs = db.get_attendance_logs()
print(f"✅ Total logs found: {len(all_logs)}")
print(all_logs.head())

# 3. Test get_attendance_logs (Specific)
user_logs = db.get_attendance_logs("Mr. Ashwin")
print(f"✅ Logs for Mr. Ashwin: {len(user_logs)}")
print(user_logs.head())

print("\n--- Testing Navigation Support ---")
# Verify if timetable roles or staff names exist
conn = db.get_connection()
teachers = pd.read_sql_query("SELECT * FROM teachers", conn)
print(f"✅ Staff count: {len(teachers)}")
print(teachers[['name', 'status']].head())
conn.close()
