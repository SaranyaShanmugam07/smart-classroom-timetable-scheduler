import database_manager as db
import sqlite3

# Cleanup if previous test left debris
conn = db.get_connection()
c = conn.cursor()
c.execute("DELETE FROM users WHERE username = 'teststaff'")
c.execute("DELETE FROM teachers WHERE name = 'Mr. Test Onboarding'")
conn.commit()
conn.close()

print("--- Testing Dynamic Staff Onboarding ---")
# 1. Sign up as a new Staff
success, message = db.signup("teststaff", "pass123", "Mr. Test Onboarding", "MKCE@2026", "Staff")
print(f"Signup result: {success}, {message}")

# 2. Check if user is in users table
conn = db.get_connection()
c = conn.cursor()
c.execute("SELECT role, full_name FROM users WHERE username = 'teststaff'")
user = c.fetchone()
print(f"User in DB: {user}")

# 3. Check if user is also in teachers table
c.execute("SELECT specialty, status FROM teachers WHERE name = 'Mr. Test Onboarding'")
teacher = c.fetchone()
print(f"Teacher in Directory: {teacher}")

if user and teacher:
    print("\n✅ Verification Successful: New staff is automatically onboarded!")
else:
    print("\n❌ Verification Failed!")

conn.close()
