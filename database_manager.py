import sqlite3
import bcrypt
import pandas as pd
from datetime import datetime
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "smart_classroom_v2.db")

def get_connection():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def initialize_db():
    conn = get_connection()
    c = conn.cursor()
    
    # 1. Users Table
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password_hash TEXT,
            full_name TEXT,
            role TEXT DEFAULT 'Student' -- 'Admin', 'Staff', 'Student'
        )
    ''')
    
    # Simple migration: add full_name if it doesn't exist
    try:
        c.execute("ALTER TABLE users ADD COLUMN full_name TEXT")
    except sqlite3.OperationalError:
        pass # Column already exists
    
    # 2. Teachers Table (Staff)
    c.execute('''
        CREATE TABLE IF NOT EXISTS teachers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            specialty TEXT, -- 'AIML', 'DS', 'IoT', 'Theory'
            status TEXT DEFAULT 'Available' -- 'Available', 'Absent'
        )
    ''')
    
    # 3. Timetable Table
    c.execute('''
        CREATE TABLE IF NOT EXISTS timetable (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            day TEXT,
            period TEXT,
            subject TEXT,
            teacher_id INTEGER,
            room TEXT,
            FOREIGN KEY (teacher_id) REFERENCES teachers(id)
        )
    ''')
    
    # 4. Attendance Table
    c.execute('''
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            timestamp TEXT,
            status TEXT, -- 'Present', 'Absent'
            network_status TEXT
        )
    ''')
    
    # 5. Rooms Table
    c.execute('''
        CREATE TABLE IF NOT EXISTS rooms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            room_no TEXT UNIQUE,
            lights_status TEXT DEFAULT 'OFF',
            ac_status TEXT DEFAULT 'OFF',
            projector_status TEXT DEFAULT 'OFF',
            occupancy_count INTEGER DEFAULT 0,
            temperature REAL DEFAULT 25.0
        )
    ''')
    
    # 6. System Alerts Table
    c.execute('''
        CREATE TABLE IF NOT EXISTS system_alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            alert_type TEXT, -- 'Critical', 'Warning', 'Info'
            message TEXT,
            room TEXT
        )
    ''')
    
    conn.commit()
    conn.close()
    
    # Seed default data
    seed_data()

def seed_data():
    conn = get_connection()
    c = conn.cursor()
    
    # Check if admin exists
    c.execute("SELECT * FROM users WHERE username = 'admin'")
    if not c.fetchone():
        salt = bcrypt.gensalt()
        pwd_hash = bcrypt.hashpw('admin123'.encode('utf-8'), salt)
        c.execute("INSERT INTO users (username, password_hash, full_name, role) VALUES (?, ?, ?, ?)", 
                  ('admin', pwd_hash.decode('utf-8'), 'System Administrator', 'Admin'))
        
        pwd_hash_t = bcrypt.hashpw('teacher123'.encode('utf-8'), salt)
        c.execute("INSERT INTO users (username, password_hash, full_name, role) VALUES (?, ?, ?, ?)", 
                  ('teacher', pwd_hash_t.decode('utf-8'), 'Dr. Arulkumaran', 'Staff'))
        
    # --- FORCE RESET AND RE-SEED STAFF ---
    c.execute("DELETE FROM teachers")
    teachers = [
        ('Mr. Ashwin', 'AIML'),
        ('Ms. Priya Dharshini', 'PQST'),
        ('Mr. Aadhith', 'ADM'),
        ('Dr. Kavitha', 'AIML'),
        ('Mr. Dinesh', 'DBMS'),
        ('Ms. Divya', 'EDA'),
        ('Mr. Arun', 'AIML'),
        ('Dr. Naveen Kumar', 'ADM'),
        ('Ms. Shalini', 'PQST'),
        ('Mr. Hari Prasad', 'DBMS'),
        ('Ms. Riya', 'ADM')
    ]
    for name, specialty in teachers:
        c.execute("INSERT INTO teachers (name, specialty) VALUES (?, ?)", (name, specialty))
        
    # Check if rooms empty safely
    try:
        c.execute("SELECT COUNT(*) FROM rooms")
        count = c.fetchone()[0]
    except sqlite3.OperationalError:
        count = 0

    if count == 0:
        rooms = [
            ('CR-101', 'ON', 'ON', 'OFF', 45, 23.2),
            ('CR-102', 'ON', 'OFF', 'OFF', 0, 28.5), # WASTAGE SCENARIO: Lights ON but 0 students
            ('LAB-201', 'ON', 'ON', 'ON', 32, 21.0),
            ('LAB-202', 'OFF', 'ON', 'OFF', 12, 22.5)
        ]
        c.executemany("INSERT INTO rooms (room_no, lights_status, ac_status, projector_status, occupancy_count, temperature) VALUES (?, ?, ?, ?, ?, ?)", rooms)
        
    # Seed sample attendance (REMOVED for Fresh Start Demo)
    pass
        
    conn.commit()
    conn.close()

def login(username, password):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT password_hash, role, full_name FROM users WHERE username = ?", (username,))
    row = c.fetchone()
    conn.close()
    
    if row:
        stored_hash = row[0].encode('utf-8')
        if bcrypt.checkpw(password.encode('utf-8'), stored_hash):
            return True, row[1], row[2]
    return False, None, None

def signup(username, password, full_name, access_code, role="Student"):
    if not username or not password:
        return False, "Username and password required"
    
    if access_code != "MKCE@2026":
        return False, "Invalid College Access Code"
    
    conn = get_connection()
    c = conn.cursor()
    salt = bcrypt.gensalt()
    pwd_hash = bcrypt.hashpw(password.encode('utf-8'), salt)
    
    try:
        # Step 1: Create User
        c.execute("INSERT INTO users (username, password_hash, full_name, role) VALUES (?, ?, ?, ?)", 
                  (username, pwd_hash.decode('utf-8'), full_name, role))
        
        # Step 2: Auto-Onboard Staff to Teacher Directory
        if role == "Staff":
            # Check if already exists to avoid Unique constraint failure
            c.execute("SELECT id FROM teachers WHERE name = ?", (full_name,))
            if not c.fetchone():
                c.execute("INSERT INTO teachers (name, specialty, status) VALUES (?, ?, ?)", 
                          (full_name, "Guest Staff", "Available"))
                
        conn.commit()
        return True, "Success"
    except sqlite3.IntegrityError:
        return False, "Username already exists"
    finally:
        conn.close()

def mark_teacher_status(name, status):
    conn = get_connection()
    c = conn.cursor()
    c.execute("UPDATE teachers SET status = ? WHERE name = ?", (status, name))
    conn.commit()
    conn.close()

def generate_smart_timetable():
    """
    Implements the permanent IV-SEM Master Schedule.
    Teachers are FIXED for their subjects. 
    Substitution logic kicks in only on absenteeism.
    """
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    periods = ["I", "II", "III", "IV", "V", "VI", "VII"]
    
    # MASTER SCHEDULE GRID (Fixed Subject/Permanent Teacher mapping)
    # Day -> Period Index -> (Subject, Teacher Name)
    master_grid = {
        "Monday": [("DBMS", "Mr. Dinesh"), ("AIML", "Mr. Ashwin"), ("DBMS LAB", "Mr. Hari Prasad"), ("DBMS LAB", "Mr. Hari Prasad"), ("PQST", "Ms. Priya Dharshini"), ("ADM", "Mr. Aadhith"), ("EDA", "Ms. Divya")],
        "Tuesday": [("ADM", "Mr. Aadhith"), ("AIML", "Mr. Ashwin"), ("AIML LAB", "Dr. Kavitha"), ("AIML LAB", "Dr. Kavitha"), ("DBMS", "Mr. Dinesh"), ("PQST", "Ms. Priya Dharshini"), ("EDA", "Ms. Divya")],
        "Wednesday": [("PQST", "Ms. Priya Dharshini"), ("EDA", "Ms. Divya"), ("ADM LAB", "Ms. Riya"), ("ADM LAB", "Ms. Riya"), ("AIML", "Mr. Ashwin"), ("DBMS", "Mr. Dinesh"), ("ADM", "Mr. Aadhith")],
        "Thursday": [("DBMS", "Mr. Dinesh"), ("ADM", "Mr. Aadhith"), ("EDA", "Ms. Divya"), ("EDA", "Ms. Divya"), ("AIML", "Mr. Ashwin"), ("PQST", "Ms. Priya Dharshini"), ("ADM", "Mr. Aadhith")],
        "Friday": [("ADM", "Mr. Aadhith"), ("DBMS", "Mr. Dinesh"), ("ADM LAB", "Ms. Riya"), ("ADM LAB", "Ms. Riya"), ("AIML", "Mr. Ashwin"), ("AIML", "Mr. Ashwin"), ("PQST", "Ms. Priya Dharshini")]
    }

    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM timetable")
    
    # Pre-fetch teacher IDs to ensure database referential integrity
    teacher_map = {}
    c.execute("SELECT name, id FROM teachers")
    for name, t_id in c.fetchall():
        teacher_map[name] = t_id

    for day in days:
        for i, period in enumerate(periods):
            # Pick from master grid
            subject, t_name = master_grid[day][i]
            # Ensure the teacher exists in DB, else use a fallback
            c.execute("SELECT id FROM teachers WHERE name = ?", (t_name,))
            res = c.fetchone()
            t_id = res[0] if res else 1 

            c.execute("INSERT INTO timetable (day, period, subject, teacher_id) VALUES (?, ?, ?, ?)", 
                      (day, period, subject, t_id))
            
    conn.commit()
    conn.close()
    return True

def get_timetable():
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT t.day, t.period, t.subject, tr.name as teacher_name, tr.specialty
        FROM timetable t
        LEFT JOIN teachers tr ON t.teacher_id = tr.id
    """)
    rows = c.fetchall()
    conn.close()
    return rows

def get_available_substitute(specialty, day, period, exclude_names=None):
    conn = get_connection()
    c = conn.cursor()
    
    # helper: check if teacher is already teaching in this slot PERMANENTLY
    def is_busy(t_name):
        c.execute("""
            SELECT 1 FROM timetable t
            JOIN teachers tr ON t.teacher_id = tr.id
            WHERE tr.name = ? AND t.day = ? AND t.period = ?
        """, (t_name, day, period))
        return c.fetchone() is not None

    import random
    
    # Category mapping for fallback (if no direct specialist found)
    shared_categories = {'PQST': 'EDA', 'EDA': 'PQST', 'AIML': 'DBMS', 'DBMS': 'AIML'}
    alt_spec = shared_categories.get(specialty)

    # Convert exclude_names to a set for faster lookup
    busy_proxies = set(exclude_names) if exclude_names else set()

    def find_best(spec):
        cands = sorted([r[0] for r in c.fetchall()])
        
        # Priority: Available + Specialist + Not Busy + Not already a Proxy elsewhere
        for name in cands:
            if not is_busy(name) and name not in busy_proxies:
                return name
        return None

    # Step A: Look for Direct Specialist
    result = find_best(specialty)
    if result:
        conn.close()
        return f"Proxy: {result}"

    # Step B: Look for Shared-Category Specialist
    if alt_spec:
        result = find_best(alt_spec)
        if result:
            conn.close()
            return f"Proxy: {result}"

    # Step C: Fallback to ANY available staff who isn't busy
    c.execute("SELECT name FROM teachers WHERE status = 'Available'")
    gen_cands = sorted([r[0] for r in c.fetchall()])
    for name in gen_cands:
        if not is_busy(name) and name not in busy_proxies:
            conn.close()
            return f"Substitute: {name}"
            
    conn.close()
    return "HOD Review Required"

def get_lesson_plan(subject):
    """
    Returns AI-generated lesson blueprint and quiz for a subject.
    """
    knowledge_base = {
        'AIML': {
            'summary': 'Artificial Intelligence and Machine Learning (AIML) focuses on the development of algorithms that allow computers to learn from and make decisions based on data. This session covers Supervised vs Unsupervised Learning, Neural Network architectures (Input, Hidden, and Output layers), and the mathematics of Backpropagation for error reduction. Key focus: Gradient Descent and Loss Functions in deep learning models.',
            'quiz': [
                '1. Differentiate between Supervised and Unsupervised Learning.',
                '2. What is the role of an Activation Function in a Neural Network?',
                '3. Explain the term "Overfitting" and how to prevent it.',
                '4. What is Gradient Descent in the context of Model Training?',
                '5. Define the difference between a Neuron and a Layer.'
            ]
        },
        'DBMS': {
            'summary': 'Database Management Systems (DBMS) are essential for storing, retrieving, and managing data in applications. This module explores Relational Database design, the importance of Normalization (1NF, 2NF, 3NF, BCNF) to reduce redundancy, and ACID properties (Atomicity, Consistency, Isolation, Durability) for transaction integrity. Key focus: SQL Query Optimization and Indexing strategies.',
            'quiz': [
                '1. Explain the ACID properties with a real-world example.',
                '2. What is the difference between Primary Key and Unique Key?',
                '3. Define 3rd Normal Form (3NF) requirements.',
                '4. What are Joins in SQL? Explain Left vs Right Join.',
                '5. Why is Indexing important for database performance?'
            ]
        },
        'PQST': {
            'summary': 'Probability and Queueing Systems / Statistics (PQST) provides the mathematical foundation for analyzing random processes and data distributions. Topics include Mean, Median, Mode, Variance, and Standard Deviation. We also cover Normal Distribution (Bell Curve), Central Limit Theorem, and Hypothesis Testing for data-driven decision making. Key focus: Statistical modeling for Big Data.',
            'quiz': [
                '1. Define the Central Limit Theorem.',
                '2. What is the difference between Probability and Statistics?',
                '3. Explain Standard Deviation and its significance.',
                '4. What is a Null Hypothesis?',
                '5. Describe the properties of a Normal Distribution.'
            ]
        },
        'ADM': {
            'summary': 'Advanced Data Management (ADM) deals with large-scale data storage and processing architectures. It covers NoSQL databases (MongoDB, Cassandra), Columnar vs Row-oriented storage, and Distributed File Systems like HDFS. Focus is on Scalability, High Availability, and CAP Theorem (Consistency, Availability, Partition Tolerance) in modern cloud systems.',
            'quiz': [
                '1. Explain the CAP Theorem in Distributed Systems.',
                '2. When would you choose a NoSQL database over a Relational one?',
                '3. What is Horizontal Scaling?',
                '4. Define Sharding in Database Architecture.',
                '5. What is the role of MapReduce in Big Data processing?'
            ]
        },
        'PP': {
            'summary': 'Python Programming (PP) is the core language for modern AI and Web development. This session covers advanced Python concepts including List Comprehensions, Decorators, Generators, and the Global Interpreter Lock (GIL). We also explore data structures like Dictionaries and Sets, and the use of libraries like NumPy and Pandas for data manipulation.',
            'quiz': [
                '1. What is a Python Decorator?',
                '2. Explain the difference between Lists and Tuples.',
                '3. What are Generators and why are they memory efficient?',
                '4. Define Global Interpreter Lock (GIL).',
                '5. How does Python handle memory management?'
            ]
        },
        'EDA': {
            'summary': 'Exploratory Data Analysis (EDA) is the critical first step in any data science project. It involves summarizing the main characteristics of a dataset, often using visual methods. Topics include Outlier detection, Handling missing values, Correlation analysis, and Feature Engineering. Key focus: Data visualization using Matplotlib and Seaborn to find patterns.',
            'quiz': [
                '1. What is the primary goal of EDA?',
                '2. How do you identify outliers in a dataset?',
                '3. Explain the difference between Univariate and Bivariate analysis.',
                '4. What is a Correlation Heatmap?',
                '5. How do you handle Null values in a dataset?'
            ]
        }
    }
    return knowledge_base.get(subject, {
        'summary': 'General curriculum review and discussion session.',
        'quiz': ['1. Discuss today\'s key concepts.', '2. Any student questions?', '3. Quick recap of previous lecture.']
    })

def get_rooms_status():
    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM rooms", conn)
    conn.close()
    return df

import socket

def mark_attendance(name, status):
    conn = get_connection()
    c = conn.cursor()
    
    # --- REAL NETWORK DETECTION ---
    try:
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        
        # Check for Private/Local IP ranges (Campus-like)
        is_campus = any(local_ip.startswith(prefix) for prefix in ["192.168.", "10.", "172.", "127."])
        network_status = "🟢 Campus-Net" if is_campus else "🏠 Remote-Session"
    except:
        local_ip = "Unknown"
        network_status = "🏠 Remote-Session"

    # Check if already marked TODAY
    today = datetime.now().strftime("%Y-%m-%d")
    c.execute("SELECT 1 FROM attendance WHERE name = ? AND timestamp LIKE ?", (name, today + "%"))
    if c.fetchone():
        conn.close()
        return False
        
    # Mark fresh attendance with Network-Guard & Real IP
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute("INSERT INTO attendance (name, timestamp, status, network_status) VALUES (?, ?, ?, ?)", 
              (name, timestamp, status, f"{network_status} ({local_ip})"))
    conn.commit()
    conn.close()
    return True

def get_attendance_logs(name=None):
    conn = get_connection()
    if name:
        query = "SELECT * FROM attendance WHERE name = ? ORDER BY timestamp DESC"
        df = pd.read_sql_query(query, conn, params=(name,))
    else:
        query = "SELECT * FROM attendance ORDER BY timestamp DESC"
        df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def update_room_device(room_no, device, status):
    conn = get_connection()
    c = conn.cursor()
    c.execute(f"UPDATE rooms SET {device} = ? WHERE room_no = ?", (status, room_no))
    conn.commit()
    conn.close()
def log_system_alert(alert_type, message, room="General"):
    conn = get_connection()
    c = conn.cursor()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute("INSERT INTO system_alerts (timestamp, alert_type, message, room) VALUES (?, ?, ?, ?)", 
              (timestamp, alert_type, message, room))
    conn.commit()
    conn.close()

def get_system_alerts(limit=5):
    conn = get_connection()
    query = "SELECT * FROM system_alerts ORDER BY timestamp DESC LIMIT ?"
    df = pd.read_sql_query(query, conn, params=(limit,))
    conn.close()
    return df
