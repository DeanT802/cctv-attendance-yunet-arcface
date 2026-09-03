"""Quick diagnostic to check meeting checkpoint status"""
from app.database import Database

db = Database()
db.connect()

# Check recent meetings
print("\n" + "="*60)
print("Recent Meetings Checkpoint Status")
print("="*60)

result = db.execute_query("""
    SELECT cm.id, cm.schedule_id, cm.meeting_number, cm.meeting_date,
           cm.checkpoint_enabled, cm.checkpoint_interval, cm.total_checkpoints,
           s.class_name, c.name as course_name
    FROM course_meetings cm
    JOIN schedules s ON cm.schedule_id = s.id
    JOIN courses c ON s.course_id = c.id
    ORDER BY cm.id DESC LIMIT 10
""")

if result:
    for r in result:
        enabled = "✅ YES" if r['checkpoint_enabled'] == 1 else "❌ NO"
        print(f"\nMeeting ID: {r['id']}")
        print(f"  Course: {r['course_name']} - {r['class_name']}")
        print(f"  Date: {r['meeting_date']}")
        print(f"  Checkpoint Enabled: {enabled}")
        print(f"  Interval: {r['checkpoint_interval']} min")
        print(f"  Total Checkpoints: {r['total_checkpoints']}")
else:
    print("No meetings found!")

# Check schedule_settings
print("\n" + "="*60)
print("Schedule Settings (Checkpoint Configs)")
print("="*60)

settings = db.execute_query("""
    SELECT ss.*, s.class_name, c.name as course_name
    FROM schedule_settings ss
    JOIN schedules s ON ss.schedule_id = s.id
    JOIN courses c ON s.course_id = c.id
    ORDER BY ss.schedule_id DESC
""")

if settings:
    current_schedule = None
    for s in settings:
        if current_schedule != s['schedule_id']:
            current_schedule = s['schedule_id']
            print(f"\nSchedule ID {s['schedule_id']}: {s['course_name']} - {s['class_name']}")
        print(f"  {s['setting_key']}: {s['setting_value']}")
else:
    print("No checkpoint settings found in schedule_settings table!")
    print("This means no schedule was created with checkpoint enabled.")

db.disconnect()
print("\n")
