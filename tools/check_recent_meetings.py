"""Check recent meetings and their checkpoint status"""
import mysql.connector

# Database connection
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'student_attendance'
}

conn = mysql.connector.connect(**db_config)
cursor = conn.cursor(dictionary=True)

print("=" * 70)
print("Recent Meetings (Last 10)")
print("=" * 70)

cursor.execute("""
    SELECT cm.id, cm.schedule_id, cm.meeting_number, cm.meeting_date, 
           cm.checkpoint_enabled, cm.checkpoint_interval, cm.total_checkpoints,
           c.name as course_name, s.class_name
    FROM course_meetings cm
    JOIN schedules s ON cm.schedule_id = s.id
    JOIN courses c ON s.course_id = c.id
    ORDER BY cm.id DESC
    LIMIT 10
""")
meetings = cursor.fetchall()

for m in meetings:
    checkpoint_status = "✅ YES" if m['checkpoint_enabled'] else "❌ NO"
    print(f"\nMeeting ID: {m['id']}")
    print(f"  Course: {m['course_name']} - {m['class_name']}")
    print(f"  Schedule ID: {m['schedule_id']}")
    print(f"  Meeting #: {m['meeting_number']}")
    print(f"  Date: {m['meeting_date']}")
    print(f"  Checkpoint Enabled: {checkpoint_status}")
    print(f"  Interval: {m['checkpoint_interval']} min, Total: {m['total_checkpoints']}")

# Check schedule_settings for Machine Learning (schedule_id = 16)
print("\n" + "=" * 70)
print("Schedule Settings for Machine Learning (ID 16)")
print("=" * 70)

cursor.execute("""
    SELECT * FROM schedule_settings WHERE schedule_id = 16
""")
settings = cursor.fetchall()
for s in settings:
    print(f"  {s['setting_key']}: {s['setting_value']}")

cursor.close()
conn.close()
