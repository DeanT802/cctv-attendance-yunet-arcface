"""
Script to apply Multiple Check-in Schema to Database
Run this once to enable the multiple check-in feature
"""

import mysql.connector
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

def apply_schema():
    """Apply the multiple check-in schema to database"""
    
    # Database connection from .env
    db_config = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'user': os.getenv('DB_USER', 'root'),
        'password': os.getenv('DB_PASSWORD', ''),
        'database': os.getenv('DB_NAME', 'student_attendance')
    }
    
    print("=" * 60)
    print("Multiple Check-in Schema Installer")
    print("=" * 60)
    print(f"\nConnecting to database: {db_config['database']}@{db_config['host']}")
    
    try:
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()
        
        print("✅ Connected to database successfully!\n")
        
        # Step 0: Create schedule_settings table
        print("[Step 0] Creating schedule_settings table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS schedule_settings (
                id INT AUTO_INCREMENT PRIMARY KEY,
                schedule_id INT NOT NULL,
                setting_key VARCHAR(100) NOT NULL,
                setting_value TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                UNIQUE KEY unique_setting (schedule_id, setting_key),
                INDEX idx_setting_key (setting_key)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)
        print("   ✅ schedule_settings table ready")
        
        # Step 1: Add columns to course_meetings
        print("\n[Step 1] Adding checkpoint columns to course_meetings...")
        
        # Check if columns exist first
        cursor.execute("SHOW COLUMNS FROM course_meetings LIKE 'checkpoint_enabled'")
        if not cursor.fetchone():
            cursor.execute("""
                ALTER TABLE course_meetings
                ADD COLUMN checkpoint_interval INT DEFAULT 30,
                ADD COLUMN total_checkpoints INT DEFAULT 1,
                ADD COLUMN checkpoint_enabled TINYINT(1) DEFAULT 0
            """)
            print("   ✅ Added checkpoint columns to course_meetings")
        else:
            print("   ⏭️ Checkpoint columns already exist in course_meetings")
        
        # Step 2: Create attendance_checkpoints table
        print("\n[Step 2] Creating attendance_checkpoints table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS attendance_checkpoints (
                id INT AUTO_INCREMENT PRIMARY KEY,
                attendance_id INT NOT NULL,
                checkpoint_number INT NOT NULL,
                checkpoint_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                detection_method VARCHAR(50) DEFAULT 'face_recognition',
                confidence_score DECIMAL(5,2) DEFAULT NULL,
                notes TEXT DEFAULT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE KEY unique_checkpoint (attendance_id, checkpoint_number),
                INDEX idx_checkpoint_number (checkpoint_number),
                INDEX idx_checkpoint_time (checkpoint_time)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)
        print("   ✅ attendance_checkpoints table ready")
        
        # Step 3: Add columns to attendance table
        print("\n[Step 3] Adding checkpoint summary columns to attendance...")
        
        cursor.execute("SHOW COLUMNS FROM attendance LIKE 'checkpoints_completed'")
        if not cursor.fetchone():
            try:
                cursor.execute("""
                    ALTER TABLE attendance
                    ADD COLUMN checkpoints_completed INT DEFAULT 0,
                    ADD COLUMN checkpoint_status VARCHAR(50) DEFAULT 'pending',
                    ADD COLUMN first_checkpoint_time DATETIME DEFAULT NULL,
                    ADD COLUMN last_checkpoint_time DATETIME DEFAULT NULL
                """)
                print("   ✅ Added checkpoint columns to attendance")
            except mysql.connector.Error as e:
                if "Duplicate column" in str(e):
                    print("   ⏭️ Some columns already exist, skipping...")
                else:
                    raise e
        else:
            print("   ⏭️ Checkpoint columns already exist in attendance")
        
        # Commit all changes
        connection.commit()
        
        print("\n" + "=" * 60)
        print("✅ SCHEMA APPLIED SUCCESSFULLY!")
        print("=" * 60)
        
        # Verify by showing table structures
        print("\n📋 Verification:")
        
        # Check course_meetings columns
        cursor.execute("""
            SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = %s AND TABLE_NAME = 'course_meetings'
            AND COLUMN_NAME IN ('checkpoint_enabled', 'checkpoint_interval', 'total_checkpoints')
        """, (db_config['database'],))
        columns = [row[0] for row in cursor.fetchall()]
        print(f"   course_meetings checkpoint columns: {columns}")
        
        # Check attendance columns
        cursor.execute("""
            SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = %s AND TABLE_NAME = 'attendance'
            AND COLUMN_NAME IN ('checkpoints_completed', 'checkpoint_status')
        """, (db_config['database'],))
        columns = [row[0] for row in cursor.fetchall()]
        print(f"   attendance checkpoint columns: {columns}")
        
        # Check tables exist
        cursor.execute("SHOW TABLES LIKE '%checkpoint%'")
        tables = [row[0] for row in cursor.fetchall()]
        print(f"   checkpoint tables: {tables}")
        
        cursor.execute("SHOW TABLES LIKE 'schedule_settings'")
        tables = [row[0] for row in cursor.fetchall()]
        print(f"   schedule_settings table: {'exists' if tables else 'missing'}")
        
        cursor.close()
        connection.close()
        
        print("\n🎉 You can now use the Multiple Check-in feature!")
        print("   1. Restart the Flask application")
        print("   2. Create a new schedule with checkpoint enabled")
        print("   3. The checkpoint UI will appear on attendance page")
        
        return True
        
    except mysql.connector.Error as e:
        print(f"\n❌ Database error: {e}")
        return False
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    apply_schema()
