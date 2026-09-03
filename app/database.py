import mysql.connector
from mysql.connector import Error
import os
from dotenv import load_dotenv

load_dotenv()

class Database:
    def __init__(self):
        self.host = os.getenv('DB_HOST')
        self.user = os.getenv('DB_USER')
        self.password = os.getenv('DB_PASSWORD')
        self.database = os.getenv('DB_NAME')
        self.connection = None
    
    def connect(self):
        try:
            self.connection = mysql.connector.connect(
                host=self.host or 'localhost',
                user=self.user or 'root',
                password=self.password or '',
                database=self.database or 'student_attendance'
            )
            return True
        except Error as e:
            print(f"Error connecting to MySQL: {e}")
            return False
    
    def disconnect(self):
        if self.connection and self.connection.is_connected():
            self.connection.close()
    
    def execute_query(self, query, params=None):
        try:
            cursor = self.connection.cursor(dictionary=True)
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            if query.strip().upper().startswith(('INSERT', 'UPDATE', 'DELETE')):
                self.connection.commit()
                return cursor.rowcount
            else:
                return cursor.fetchall()
                
        except Error as e:
            print(f"Error executing query: {e}")
            return None
        finally:
            if cursor:
                cursor.close()
    
    def get_student_count(self):
        query = "SELECT COUNT(*) as count FROM students"
        result = self.execute_query(query)
        return result[0]['count'] if result else 0
    
    def get_course_count(self):
        query = "SELECT COUNT(*) as count FROM courses"
        result = self.execute_query(query)
        return result[0]['count'] if result else 0
    
    def get_teacher_count(self):
        query = "SELECT COUNT(*) as count FROM teachers"
        result = self.execute_query(query)
        return result[0]['count'] if result else 0
    
    def get_schedule_count(self):
        query = "SELECT COUNT(*) as count FROM schedules"
        result = self.execute_query(query)
        return result[0]['count'] if result else 0
    
    def get_recent_attendance(self):
        query = """
        SELECT st.name, s.class_name, cm.meeting_date as date, a.attendance_time as time, a.status
        FROM attendance a
        JOIN students st ON a.student_id = st.id
        JOIN course_meetings cm ON a.meeting_id = cm.id
        JOIN schedules s ON cm.schedule_id = s.id
        ORDER BY cm.meeting_date DESC, a.attendance_time DESC
        LIMIT 10
        """
        return self.execute_query(query)
    
    def get_attendance_summary_by_class(self, class_name=None, start_date=None, end_date=None):
        """Get attendance summary by class with optional filters"""
        query = """
        SELECT s.id as schedule_id, s.class_name,
               COUNT(DISTINCT st.id) as total_students,
               COUNT(CASE WHEN a.status = 'present' THEN 1 END) as present_count,
               COUNT(CASE WHEN a.status = 'absent' THEN 1 END) as absent_count,
               COUNT(CASE WHEN a.status = 'late' THEN 1 END) as late_count,
               COUNT(CASE WHEN a.status = 'excused' THEN 1 END) as excused_count,
               COUNT(a.id) as total_attendance_records,
               ROUND((COUNT(CASE WHEN a.status = 'present' THEN 1 END) * 100.0 / 
                     NULLIF(COUNT(a.id), 0)), 2) as attendance_percentage
        FROM schedules s
        LEFT JOIN course_meetings cm ON s.id = cm.schedule_id
        LEFT JOIN attendance a ON cm.id = a.meeting_id
        LEFT JOIN students st ON a.student_id = st.id
        WHERE 1=1
        """
        
        params = []
        
        if class_name:
            query += " AND s.class_name LIKE %s"
            params.append(f"%{class_name}%")
            
        if start_date:
            query += " AND DATE(a.attendance_time) >= %s"
            params.append(start_date)
            
        if end_date:
            query += " AND DATE(a.attendance_time) <= %s"
            params.append(end_date)
        
        query += """
        GROUP BY s.id, s.class_name
        ORDER BY s.class_name
        """
        
        if params:
            return self.execute_query(query, params)
        else:
            return self.execute_query(query)
    
    def get_all_students(self):
        query = """
        SELECT s.*, ps.name as program_study_name
        FROM students s
        LEFT JOIN program_studies ps ON s.program_study_id = ps.id
        ORDER BY s.name
        """
        return self.execute_query(query)
    
    def get_all_courses(self):
        query = """
        SELECT c.*
        FROM courses c
        ORDER BY c.name
        """
        return self.execute_query(query)
    
    def get_all_teachers(self):
        query = "SELECT * FROM teachers ORDER BY name"
        return self.execute_query(query)
    
    def get_all_schedules(self):
        query = """
        SELECT s.*, c.name as course_name, c.credits, c.semester, t.name as teacher_name
        FROM schedules s
        JOIN courses c ON s.course_id = c.id
        LEFT JOIN teachers t ON s.teacher_id = t.id
        ORDER BY s.day, s.time_start
        """
        return self.execute_query(query)
    
    def add_student(self, student_id, name, email, phone, class_year, program_study_id, department, semester, class_number, class_name, face_registered=False):
        query = """
        INSERT INTO students (student_id, name, email, phone, class_year, program_study_id, department, semester, class_number, class_name, face_registered)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        params = (student_id, name, email, phone, class_year, program_study_id, department, semester, class_number, class_name, face_registered)
        return self.execute_query(query, params)
    
    def update_student_face_status(self, student_id, face_registered=True):
        query = """
        UPDATE students 
        SET face_registered = %s, updated_at = CURRENT_TIMESTAMP
        WHERE id = %s
        """
        params = (face_registered, student_id)
        return self.execute_query(query, params)
    
    def get_student_by_id(self, student_id):
        query = "SELECT * FROM students WHERE id = %s"
        result = self.execute_query(query, (student_id,))
        return result[0] if result else None
    
    def delete_student(self, student_id):
        query = "DELETE FROM students WHERE id = %s"
        return self.execute_query(query, (student_id,))
    
    def add_course(self, course_name, course_code, credits, description):
        query = """
        INSERT INTO courses (name, course_code, credits, description)
        VALUES (%s, %s, %s, %s)
        """
        params = (course_name, course_code, credits, description)
        return self.execute_query(query, params)
    
    def get_course_by_id(self, course_id):
        query = "SELECT * FROM courses WHERE id = %s"
        result = self.execute_query(query, (course_id,))
        return result[0] if result else None
    
    def update_course(self, course_id, course_name, course_code, credits, description):
        query = """
        UPDATE courses 
        SET name = %s, course_code = %s, credits = %s, description = %s
        WHERE id = %s
        """
        params = (course_name, course_code, credits, description, course_id)
        return self.execute_query(query, params)
    
    def delete_course(self, course_id):
        query = "DELETE FROM courses WHERE id = %s"
        return self.execute_query(query, (course_id,))
    
    def add_teacher(self, name, email, phone, expertise):
        query = """
        INSERT INTO teachers (name, email, phone, expertise)
        VALUES (%s, %s, %s, %s)
        """
        params = (name, email, phone, expertise)
        return self.execute_query(query, params)
    
    def get_teacher_by_id(self, teacher_id):
        query = "SELECT * FROM teachers WHERE id = %s"
        result = self.execute_query(query, (teacher_id,))
        return result[0] if result else None
    
    def update_teacher(self, teacher_id, name, email, phone, expertise):
        query = """
        UPDATE teachers 
        SET name = %s, email = %s, phone = %s, expertise = %s
        WHERE id = %s
        """
        params = (name, email, phone, expertise, teacher_id)
        return self.execute_query(query, params)
    
    def delete_teacher(self, teacher_id):
        query = "DELETE FROM teachers WHERE id = %s"
        return self.execute_query(query, (teacher_id,))
    
    def add_schedule(self, course_id, teacher_id, class_name, day_of_week, start_time, end_time, room, semester=None, academic_year=None, checkpoint_enabled=False, checkpoint_interval=30, total_checkpoints=4):
        """Add new schedule with optional checkpoint settings"""
        try:
            if not self.connection or not self.connection.is_connected():
                self.connect()
            
            cursor = self.connection.cursor()
            
            # First check if schedules table has checkpoint columns
            # If not, we'll store them separately or ignore for now
            query = """
            INSERT INTO schedules (course_id, teacher_id, class_name, day, time_start, time_end, room, semester, academic_year)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            params = (course_id, teacher_id, class_name, day_of_week, start_time, end_time, room, semester, academic_year)
            cursor.execute(query, params)
            schedule_id = cursor.lastrowid
            
            # Store checkpoint settings in a separate table or as metadata
            # For now, we'll store in a JSON field or separate settings table
            # This can be applied when creating course_meetings
            if checkpoint_enabled:
                settings_query = """
                INSERT INTO schedule_settings (schedule_id, setting_key, setting_value)
                VALUES 
                    (%s, 'checkpoint_enabled', %s),
                    (%s, 'checkpoint_interval', %s),
                    (%s, 'total_checkpoints', %s)
                ON DUPLICATE KEY UPDATE setting_value = VALUES(setting_value)
                """
                try:
                    cursor.execute(settings_query, (
                        schedule_id, str(int(checkpoint_enabled)),
                        schedule_id, str(checkpoint_interval),
                        schedule_id, str(total_checkpoints)
                    ))
                except Exception as e:
                    # Table might not exist yet, skip for now
                    print(f"Note: Could not save checkpoint settings (table may not exist): {e}")
            
            self.connection.commit()
            cursor.close()
            return schedule_id
            
        except Exception as e:
            print(f"Error adding schedule: {e}")
            if self.connection:
                self.connection.rollback()
            return None
    
    def get_schedule_by_id(self, schedule_id):
        query = "SELECT * FROM schedules WHERE id = %s"
        result = self.execute_query(query, (schedule_id,))
        return result[0] if result else None
    
    def get_schedule_checkpoint_settings(self, schedule_id):
        """Get checkpoint settings for a schedule from schedule_settings table"""
        settings = {
            'checkpoint_enabled': 0,
            'checkpoint_interval': 30,
            'total_checkpoints': 1
        }
        
        try:
            query = """
            SELECT setting_key, setting_value 
            FROM schedule_settings 
            WHERE schedule_id = %s AND setting_key IN ('checkpoint_enabled', 'checkpoint_interval', 'total_checkpoints')
            """
            result = self.execute_query(query, (schedule_id,))
            
            if result:
                for row in result:
                    key = row['setting_key']
                    value = row['setting_value']
                    if key == 'checkpoint_enabled':
                        settings['checkpoint_enabled'] = int(value)
                    elif key == 'checkpoint_interval':
                        settings['checkpoint_interval'] = int(value)
                    elif key == 'total_checkpoints':
                        settings['total_checkpoints'] = int(value)
                        
            print(f"[get_schedule_checkpoint_settings] Schedule {schedule_id}: {settings}")
            return settings
            
        except Exception as e:
            print(f"Error getting checkpoint settings: {e}")
            return settings
    
    def update_schedule(self, schedule_id, course_id, teacher_id, class_name, day_of_week, start_time, end_time, room, semester=None, academic_year=None):
        query = """
        UPDATE schedules 
        SET course_id = %s, teacher_id = %s, class_name = %s, day = %s, time_start = %s, time_end = %s, room = %s, semester = %s, academic_year = %s
        WHERE id = %s
        """
        params = (course_id, teacher_id, class_name, day_of_week, start_time, end_time, room, semester, academic_year, schedule_id)
        return self.execute_query(query, params)
    
    def delete_schedule(self, schedule_id):
        query = "DELETE FROM schedules WHERE id = %s"
        return self.execute_query(query, (schedule_id,))
    
    def get_today_schedules(self):
        from datetime import datetime
        # Map weekday to Indonesian day names
        day_names = ['Senin', 'Selasa', 'Rabu', 'Kamis', 'Jumat', 'Sabtu', 'Minggu']
        today = day_names[datetime.now().weekday()]
        
        query = """
        SELECT s.*, c.name as course_name, c.credits, c.semester, t.name as teacher_name
        FROM schedules s
        JOIN courses c ON s.course_id = c.id
        LEFT JOIN teachers t ON s.teacher_id = t.id
        WHERE s.day = %s
        ORDER BY s.time_start
        """
        return self.execute_query(query, (today,))
    
    def get_program_studies(self):
        query = "SELECT * FROM program_studies ORDER BY name"
        return self.execute_query(query)
    
    def search_students(self, search_term):
        query = """
        SELECT s.*, ps.name as program_study_name
        FROM students s
        LEFT JOIN program_studies ps ON s.program_study_id = ps.id
        WHERE s.name LIKE %s OR s.student_id LIKE %s OR s.email LIKE %s
        ORDER BY s.name
        """
        search_pattern = f"%{search_term}%"
        return self.execute_query(query, (search_pattern, search_pattern, search_pattern))
    
    def get_student_attendance_stats(self, student_id):
        query = """
        SELECT 
            COUNT(*) as total_sessions,
            COUNT(CASE WHEN a.status = 'present' THEN 1 END) as present_count,
            COUNT(CASE WHEN a.status = 'late' THEN 1 END) as late_count,
            COUNT(CASE WHEN a.status = 'absent' THEN 1 END) as absent_count,
            COUNT(CASE WHEN a.status = 'excused' THEN 1 END) as excused_count,
            ROUND((COUNT(CASE WHEN a.status = 'present' THEN 1 END) * 100.0 / NULLIF(COUNT(*), 0)), 2) as attendance_percentage
        FROM attendance a
        WHERE a.student_id = %s
        """
        result = self.execute_query(query, (student_id,))
        return result[0] if result else None
    
    def get_schedules(self):
        """Get all schedules with course and teacher information"""
        query = """
        SELECT s.*, c.name as course_name, c.course_code, c.credits, c.semester, t.name as teacher_name
        FROM schedules s
        LEFT JOIN courses c ON s.course_id = c.id
        LEFT JOIN teachers t ON s.teacher_id = t.id
        ORDER BY s.day, s.time_start
        """
        return self.execute_query(query)
    
    def get_attendance_stats(self):
        """Get general attendance statistics"""
        query = """
        SELECT 
            COUNT(*) as total_attendance_records,
            COUNT(CASE WHEN status = 'present' THEN 1 END) as present_count,
            COUNT(CASE WHEN status = 'absent' THEN 1 END) as absent_count,
            COUNT(CASE WHEN status = 'late' THEN 1 END) as late_count,
            COUNT(CASE WHEN status = 'excused' THEN 1 END) as excused_count,
            ROUND((COUNT(CASE WHEN status = 'present' THEN 1 END) * 100.0 / NULLIF(COUNT(*), 0)), 2) as attendance_percentage
        FROM attendance
        WHERE DATE(attendance_time) >= DATE_SUB(CURRENT_DATE, INTERVAL 30 DAY)
        """
        result = self.execute_query(query)
        return result[0] if result else {
            'total_attendance_records': 0,
            'present_count': 0,
            'absent_count': 0, 
            'late_count': 0,
            'excused_count': 0,
            'attendance_percentage': 0
        }
    
    def get_attendance_chart_data(self):
        """Get attendance statistics per class for chart"""
        query = """
        SELECT 
            s.class_name,
            c.name as course_name,
            COUNT(a.id) as total_records,
            COUNT(CASE WHEN a.status = 'present' THEN 1 END) as present_count,
            ROUND((COUNT(CASE WHEN a.status = 'present' THEN 1 END) * 100.0 / NULLIF(COUNT(a.id), 0)), 2) as attendance_percentage
        FROM schedules s
        LEFT JOIN courses c ON s.course_id = c.id
        LEFT JOIN course_meetings cm ON cm.schedule_id = s.id
        LEFT JOIN attendance a ON a.meeting_id = cm.id
        WHERE a.attendance_time >= DATE_SUB(CURRENT_DATE, INTERVAL 30 DAY) OR a.id IS NULL
        GROUP BY s.id, s.class_name, c.name
        ORDER BY s.class_name
        """
        result = self.execute_query(query)
        return result if result else []
    
    def validate_attendance_time(self, schedule_id):
        """Validate if attendance can be taken for a schedule"""
        from datetime import datetime, time
        
        # Get schedule information
        query = """
        SELECT s.*, c.name as course_name
        FROM schedules s
        JOIN courses c ON s.course_id = c.id
        WHERE s.id = %s
        """
        schedule = self.execute_query(query, (schedule_id,))
        
        if not schedule:
            return False, "Schedule not found", None
        
        schedule = schedule[0]
        current_time = datetime.now().time()
        
        # Convert timedelta to time if needed
        time_start = schedule['time_start']
        time_end = schedule['time_end']
        
        # Handle timedelta objects from MySQL
        if hasattr(time_start, 'total_seconds'):  # It's a timedelta
            total_seconds = int(time_start.total_seconds())
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            time_start = time(hours, minutes)
            
        if hasattr(time_end, 'total_seconds'):  # It's a timedelta
            total_seconds = int(time_end.total_seconds())
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            time_end = time(hours, minutes)
        
        # Simple validation - allow attendance during the scheduled time
        if time_start <= current_time <= time_end:
            return True, "Attendance time valid", schedule
        else:
            return False, "Attendance can only be taken during scheduled class time", schedule
    
    def get_current_meeting(self, schedule_id):
        """Get current meeting for a schedule"""
        from datetime import datetime, date
        
        # Check if there's a meeting for today for this schedule
        today = date.today()
        
        query = """
        SELECT cm.*, s.course_id, c.name as course_name
        FROM course_meetings cm
        JOIN schedules s ON cm.schedule_id = s.id
        JOIN courses c ON s.course_id = c.id
        WHERE cm.schedule_id = %s AND DATE(cm.meeting_date) = %s
        ORDER BY cm.meeting_date DESC
        LIMIT 1
        """
        
        result = self.execute_query(query, (schedule_id, today))
        
        if result:
            return result[0]
        
        # If no meeting exists for today, check if we should create one
        # based on the schedule day
        schedule_query = """
        SELECT s.*, c.name as course_name
        FROM schedules s
        JOIN courses c ON s.course_id = c.id
        WHERE s.id = %s
        """
        
        schedule = self.execute_query(schedule_query, (schedule_id,))
        
        if not schedule:
            return None
            
        schedule = schedule[0]
        
        # Check if today matches the schedule day
        day_names = ['Senin', 'Selasa', 'Rabu', 'Kamis', 'Jumat', 'Sabtu', 'Minggu']
        today_day = day_names[datetime.now().weekday()]
        
        if schedule['day'] == today_day:
            # Get the next meeting number
            count_query = """
            SELECT COUNT(*) as count FROM course_meetings WHERE schedule_id = %s
            """
            count_result = self.execute_query(count_query, (schedule_id,))
            next_meeting_number = (count_result[0]['count'] if count_result else 0) + 1
            
            # Auto-create a meeting for today using create_course_meeting (with checkpoint settings!)
            print(f"[get_current_meeting] Creating new meeting for schedule {schedule_id}, meeting #{next_meeting_number}")
            meeting_id = self.create_course_meeting(
                schedule_id=schedule_id,
                meeting_number=next_meeting_number,
                meeting_date=today,
                topic=f"Pertemuan {next_meeting_number}"
            )
            
            if meeting_id:
                # Fetch the complete meeting data (including checkpoint settings)
                fetch_query = """
                SELECT cm.*, s.course_id, c.name as course_name
                FROM course_meetings cm
                JOIN schedules s ON cm.schedule_id = s.id
                JOIN courses c ON s.course_id = c.id
                WHERE cm.id = %s
                """
                new_meeting = self.execute_query(fetch_query, (meeting_id,))
                if new_meeting:
                    return new_meeting[0]
        
        return None
    
    def get_schedule_with_class_info(self, schedule_id):
        """Get schedule information with course and class details"""
        query = """
        SELECT s.*, c.name as course_name, c.course_code, c.credits, c.semester, 
               t.name as teacher_name
        FROM schedules s
        JOIN courses c ON s.course_id = c.id
        LEFT JOIN teachers t ON s.teacher_id = t.id
        WHERE s.id = %s
        """
        result = self.execute_query(query, (schedule_id,))
        return result[0] if result else None
    
    def get_students_by_schedule(self, schedule_id):
        """Get all students enrolled in a specific schedule/class"""
        # First get schedule's class_name
        schedule_query = "SELECT class_name FROM schedules WHERE id = %s"
        schedule_info = self.execute_query(schedule_query, (schedule_id,))
        
        if not schedule_info:
            return []
        
        class_name = schedule_info[0]['class_name']
        
        # Get all students from this class
        query_class = """
        SELECT s.id, s.name, s.student_id, s.email, s.class_name as student_class
        FROM students s
        WHERE s.class_name = %s
        ORDER BY s.name
        """
        
        class_students = self.execute_query(query_class, (class_name,))
        
        if class_students:
            # Auto-enroll any students not yet enrolled
            for student in class_students:
                self.enroll_student_to_schedule(student['id'], schedule_id)
        
        # Now get all enrolled students (should include newly enrolled ones)
        query_enrolled = """
        SELECT s.id, s.name, s.student_id, s.email, s.class_name as student_class
        FROM students s
        JOIN class_enrollments ce ON s.id = ce.student_id
        WHERE ce.schedule_id = %s AND ce.status = 'active'
        ORDER BY s.name
        """
        
        return self.execute_query(query_enrolled, (schedule_id,)) or []
    
    def enroll_student_to_schedule(self, student_id, schedule_id):
        """Enroll a student to a schedule if not already enrolled"""
        try:
            # Check if already enrolled
            check_query = """
            SELECT id FROM class_enrollments 
            WHERE student_id = %s AND schedule_id = %s
            """
            existing = self.execute_query(check_query, (student_id, schedule_id))
            
            if not existing:
                # Enroll the student
                enroll_query = """
                INSERT INTO class_enrollments 
                (student_id, schedule_id, enrolled_date, status, created_at, updated_at)
                VALUES (%s, %s, CURDATE(), 'active', NOW(), NOW())
                """
                cursor = self.connection.cursor()
                cursor.execute(enroll_query, (student_id, schedule_id))
                self.connection.commit()
                cursor.close()
                return True
                
        except Exception as e:
            print(f"Error enrolling student: {e}")
            return False
        
        return False
    
    def mark_meeting_attendance(self, student_id, meeting_id, status, notes=None, method=None):
        """Mark attendance for a student in a specific meeting"""
        try:
            if not self.connection or not self.connection.is_connected():
                self.connect()
            
            cursor = self.connection.cursor()
            
            # Validate that the meeting_id exists before trying to insert
            meeting_check = "SELECT id FROM course_meetings WHERE id = %s"
            cursor.execute(meeting_check, (meeting_id,))
            meeting_exists = cursor.fetchone()
            
            if not meeting_exists:
                print(f"Error: Meeting ID {meeting_id} does not exist in course_meetings table")
                return False
            
            # Check if attendance record already exists
            check_query = "SELECT id FROM attendance WHERE student_id = %s AND meeting_id = %s"
            cursor.execute(check_query, (student_id, meeting_id))
            existing = cursor.fetchone()
            
            if existing:
                # Update existing record
                update_query = """
                UPDATE attendance 
                SET status = %s, notes = %s, attendance_time = NOW(), attendance_method = %s
                WHERE student_id = %s AND meeting_id = %s
                """
                cursor.execute(update_query, (status, notes, method, student_id, meeting_id))
            else:
                # Insert new record
                insert_query = """
                INSERT INTO attendance (student_id, meeting_id, status, notes, attendance_time, attendance_method)
                VALUES (%s, %s, %s, %s, NOW(), %s)
                """
                cursor.execute(insert_query, (student_id, meeting_id, status, notes, method))
            
            self.connection.commit()
            cursor.close()
            return True
            
        except Exception as e:
            print(f"Error marking attendance: {e}")
            return False
            return True
            
        except Exception as e:
            print(f"Error marking attendance: {e}")
            if self.connection:
                self.connection.rollback()
            return False
    
    def get_meetings_by_schedule(self, schedule_id):
        """Get all meetings for a specific schedule"""
        query = """
        SELECT cm.*, s.course_id, c.name as course_name
        FROM course_meetings cm
        JOIN schedules s ON cm.schedule_id = s.id
        JOIN courses c ON s.course_id = c.id
        WHERE cm.schedule_id = %s
        ORDER BY cm.meeting_number
        """
        return self.execute_query(query, (schedule_id,))
    
    def create_course_meeting(self, schedule_id, meeting_number, meeting_date, topic=None):
        """Create a new course meeting with checkpoint settings from schedule"""
        try:
            if not self.connection or not self.connection.is_connected():
                self.connect()
            
            cursor = self.connection.cursor(dictionary=True)  # FIXED: Use dictionary cursor
            
            # Get checkpoint settings from schedule_settings if available
            checkpoint_enabled = 0
            checkpoint_interval = 30
            total_checkpoints = 1
            
            try:
                settings_query = """
                SELECT setting_key, setting_value 
                FROM schedule_settings 
                WHERE schedule_id = %s AND setting_key IN ('checkpoint_enabled', 'checkpoint_interval', 'total_checkpoints')
                """
                cursor.execute(settings_query, (schedule_id,))
                settings = cursor.fetchall()
                
                print(f"[Create Meeting] Found {len(settings)} checkpoint settings for schedule {schedule_id}")
                
                for setting in settings:
                    key = setting['setting_key']
                    value = setting['setting_value']
                    print(f"[Create Meeting]   - {key}: {value}")
                    
                    if key == 'checkpoint_enabled':
                        checkpoint_enabled = int(value)
                    elif key == 'checkpoint_interval':
                        checkpoint_interval = int(value)
                    elif key == 'total_checkpoints':
                        total_checkpoints = int(value)
                        
            except Exception as e:
                # Settings table might not exist or no settings found, use defaults
                print(f"[Create Meeting] Warning reading settings: {e}")
                pass
            
            # Create meeting with checkpoint settings
            query = """
            INSERT INTO course_meetings (schedule_id, meeting_number, meeting_date, meeting_topic, status, 
                                        checkpoint_enabled, checkpoint_interval, total_checkpoints)
            VALUES (%s, %s, %s, %s, 'scheduled', %s, %s, %s)
            """
            
            cursor.execute(query, (schedule_id, meeting_number, meeting_date, topic, 
                                  checkpoint_enabled, checkpoint_interval, total_checkpoints))
            meeting_id = cursor.lastrowid
            
            self.connection.commit()
            cursor.close()
            
            print(f"[Create Meeting] ✅ Meeting ID {meeting_id} created with checkpoints: enabled={checkpoint_enabled}, interval={checkpoint_interval}min, total={total_checkpoints}")
            
            return meeting_id
            
        except Exception as e:
            print(f"Error creating course meeting: {e}")
            import traceback
            traceback.print_exc()
            if self.connection:
                self.connection.rollback()
            return None
    
    def get_meeting_attendance(self, meeting_id):
        """Get all attendance records for a specific meeting"""
        query = """
        SELECT a.*, s.name, s.student_id as nim
        FROM attendance a
        JOIN students s ON a.student_id = s.id
        WHERE a.meeting_id = %s
        ORDER BY s.name
        """
        return self.execute_query(query, (meeting_id,))
    
    def validate_meeting_attendance_time(self, meeting_id):
        """Validate if attendance can be taken for a specific meeting"""
        from datetime import datetime, time
        
        # Get meeting and schedule information
        query = """
        SELECT cm.*, s.day, s.time_start, s.time_end, c.name as course_name
        FROM course_meetings cm
        JOIN schedules s ON cm.schedule_id = s.id
        JOIN courses c ON s.course_id = c.id
        WHERE cm.id = %s
        """
        meeting = self.execute_query(query, (meeting_id,))
        
        if not meeting:
            return False, "Meeting not found", None
        
        meeting = meeting[0]
        current_time = datetime.now().time()
        
        # Convert timedelta to time if needed
        time_start = meeting['time_start']
        time_end = meeting['time_end']
        
        # Handle timedelta objects from MySQL
        if hasattr(time_start, 'total_seconds'):  # It's a timedelta
            total_seconds = int(time_start.total_seconds())
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            time_start = time(hours, minutes)
            
        if hasattr(time_end, 'total_seconds'):  # It's a timedelta
            total_seconds = int(time_end.total_seconds())
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            time_end = time(hours, minutes)
        
        # Simple validation - allow attendance during the scheduled time
        if time_start <= current_time <= time_end:
            return True, "Attendance time valid", meeting
        else:
            return False, "Attendance can only be taken during scheduled class time", meeting
    
    def get_schedule_info(self, schedule_id):
        """Get detailed schedule information including course and teacher details"""
        query = """
        SELECT s.*, c.name as course_name, c.credits, c.description as course_description,
               t.name as teacher_name, t.email as teacher_email
        FROM schedules s
        JOIN courses c ON s.course_id = c.id
        JOIN teachers t ON s.teacher_id = t.id
        WHERE s.id = %s
        """
        result = self.execute_query(query, (schedule_id,))
        return result[0] if result else None
    
    def get_detailed_attendance_recap(self, schedule_id):
        """Get detailed attendance recap with meeting-by-meeting breakdown"""
        # First get schedule info
        schedule_query = "SELECT class_name FROM schedules WHERE id = %s"
        schedule_info = self.execute_query(schedule_query, (schedule_id,))
        
        if not schedule_info:
            return []
        
        class_name = schedule_info[0]['class_name']
        
        # Get all students from the class
        students_query = """
        SELECT 
            s.id as student_id,
            s.name as student_name, 
            s.student_id as student_number, 
            s.class_name
        FROM students s
        WHERE s.class_name = %s
        ORDER BY s.name
        """
        
        students = self.execute_query(students_query, (class_name,))
        
        if not students:
            # Return placeholder data if no students found
            return [{
                'student_name': 'No students found',
                'student_number': '-',
                'meetings': {},
                'total_meetings': 0,
                'attended_meetings': 0,
                'attendance_percentage': 0
            }]
        
        # Get all meetings for this schedule
        meetings_query = """
        SELECT 
            cm.id as meeting_id,
            cm.meeting_number
        FROM course_meetings cm
        WHERE cm.schedule_id = %s
        ORDER BY cm.meeting_number
        """
        
        meetings = self.execute_query(meetings_query, (schedule_id,))
        if not meetings:
            meetings = []
        
        # Get all attendance records
        attendance_query = """
        SELECT 
            a.student_id,
            a.meeting_id,
            a.status,
            cm.meeting_number
        FROM attendance a
        JOIN course_meetings cm ON a.meeting_id = cm.id
        WHERE cm.schedule_id = %s
        """
        
        attendance_records = self.execute_query(attendance_query, (schedule_id,))
        if not attendance_records:
            attendance_records = []
        
        # Build attendance data structure
        result = []
        for student in students:
            student_data = {
                'student_name': student['student_name'],
                'student_number': student['student_number'],
                'meetings': {},
                'total_meetings': len(meetings),
                'attended_meetings': 0,
                'attendance_percentage': 0
            }
            
            # Initialize meetings dict
            for meeting in meetings:
                student_data['meetings'][meeting['meeting_number']] = None
            
            # Fill in attendance data
            attended_count = 0
            for record in attendance_records:
                if record['student_id'] == student['student_id']:
                    meeting_num = record['meeting_number']
                    student_data['meetings'][meeting_num] = {
                        'status': record['status']
                    }
                    if record['status'] == 'present':
                        attended_count += 1
            
            student_data['attended_meetings'] = attended_count
            if len(meetings) > 0:
                student_data['attendance_percentage'] = round((attended_count / len(meetings)) * 100, 2)
            
            result.append(student_data)
        
        return result
    
    # ========== MULTIPLE CHECK-IN SYSTEM METHODS ==========
    
    def update_meeting_checkpoint_settings(self, meeting_id, checkpoint_enabled, interval_minutes, total_checkpoints):
        """Update checkpoint settings for a meeting"""
        try:
            if not self.connection or not self.connection.is_connected():
                self.connect()
            
            cursor = self.connection.cursor()
            query = """
            UPDATE course_meetings 
            SET checkpoint_enabled = %s, 
                checkpoint_interval = %s, 
                total_checkpoints = %s
            WHERE id = %s
            """
            cursor.execute(query, (checkpoint_enabled, interval_minutes, total_checkpoints, meeting_id))
            self.connection.commit()
            cursor.close()
            return True
        except Exception as e:
            print(f"Error updating checkpoint settings: {e}")
            if self.connection:
                self.connection.rollback()
            return False
    
    def get_meeting_checkpoint_settings(self, meeting_id):
        """Get checkpoint settings for a meeting"""
        try:
            if not self.connection or not self.connection.is_connected():
                self.connect()
            
            cursor = self.connection.cursor(dictionary=True)
            query = """
            SELECT checkpoint_enabled, checkpoint_interval, total_checkpoints, meeting_date
            FROM course_meetings 
            WHERE id = %s
            """
            cursor.execute(query, (meeting_id,))
            result = cursor.fetchone()
            cursor.close()
            return result
        except Exception as e:
            print(f"Error getting checkpoint settings: {e}")
            return None
    
    def mark_checkpoint_attendance(self, student_id, meeting_id, checkpoint_number, 
                                   method='face_recognition', confidence=None, notes=None):
        """Mark attendance for a specific checkpoint"""
        try:
            if not self.connection or not self.connection.is_connected():
                self.connect()
            
            cursor = self.connection.cursor()
            
            # Get or create attendance record
            check_query = "SELECT id FROM attendance WHERE student_id = %s AND meeting_id = %s"
            cursor.execute(check_query, (student_id, meeting_id))
            attendance_record = cursor.fetchone()
            
            if attendance_record:
                attendance_id = attendance_record[0]
            else:
                # Create new attendance record
                insert_query = """
                INSERT INTO attendance (student_id, meeting_id, status, attendance_time, attendance_method)
                VALUES (%s, %s, 'present', NOW(), %s)
                """
                cursor.execute(insert_query, (student_id, meeting_id, method))
                attendance_id = cursor.lastrowid
            
            # Insert or update checkpoint record
            checkpoint_query = """
            INSERT INTO attendance_checkpoints 
                (attendance_id, checkpoint_number, checkpoint_time, detection_method, confidence_score, notes)
            VALUES (%s, %s, NOW(), %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                checkpoint_time = NOW(),
                detection_method = %s,
                confidence_score = %s,
                notes = %s
            """
            cursor.execute(checkpoint_query, (
                attendance_id, checkpoint_number, method, confidence, notes,
                method, confidence, notes
            ))
            
            # Update attendance summary
            self._update_checkpoint_summary(cursor, attendance_id)
            
            self.connection.commit()
            cursor.close()
            return True
            
        except Exception as e:
            print(f"Error marking checkpoint attendance: {e}")
            if self.connection:
                self.connection.rollback()
            return False
    
    def _update_checkpoint_summary(self, cursor, attendance_id):
        """Internal method to update checkpoint summary in attendance table"""
        try:
            # Count completed checkpoints
            count_query = """
            SELECT COUNT(*), MIN(checkpoint_time), MAX(checkpoint_time)
            FROM attendance_checkpoints
            WHERE attendance_id = %s
            """
            cursor.execute(count_query, (attendance_id,))
            result = cursor.fetchone()
            checkpoints_completed = result[0]
            first_time = result[1]
            last_time = result[2]
            
            # Get total checkpoints required
            total_query = """
            SELECT cm.total_checkpoints
            FROM attendance a
            JOIN course_meetings cm ON a.meeting_id = cm.id
            WHERE a.id = %s
            """
            cursor.execute(total_query, (attendance_id,))
            total_result = cursor.fetchone()
            total_checkpoints = total_result[0] if total_result else 1
            
            # Determine status
            if checkpoints_completed == total_checkpoints:
                checkpoint_status = 'full'
            elif checkpoints_completed >= (total_checkpoints * 0.75):
                checkpoint_status = 'good'
            elif checkpoints_completed >= (total_checkpoints * 0.5):
                checkpoint_status = 'partial'
            else:
                checkpoint_status = 'poor'
            
            # Update attendance record
            update_query = """
            UPDATE attendance
            SET checkpoints_completed = %s,
                checkpoint_status = %s,
                first_checkpoint_time = %s,
                last_checkpoint_time = %s
            WHERE id = %s
            """
            cursor.execute(update_query, (
                checkpoints_completed, checkpoint_status, 
                first_time, last_time, attendance_id
            ))
            
        except Exception as e:
            print(f"Error updating checkpoint summary: {e}")
    
    def get_student_checkpoint_status(self, student_id, meeting_id):
        """Get checkpoint status for a specific student in a meeting"""
        try:
            if not self.connection or not self.connection.is_connected():
                self.connect()
            
            cursor = self.connection.cursor(dictionary=True)
            query = """
            SELECT 
                a.id as attendance_id,
                a.checkpoints_completed,
                a.checkpoint_status,
                cm.total_checkpoints,
                cm.checkpoint_interval,
                cm.checkpoint_enabled,
                GROUP_CONCAT(ac.checkpoint_number ORDER BY ac.checkpoint_number) as completed_checkpoints
            FROM attendance a
            LEFT JOIN attendance_checkpoints ac ON a.id = ac.attendance_id
            JOIN course_meetings cm ON a.meeting_id = cm.id
            WHERE a.student_id = %s AND a.meeting_id = %s
            GROUP BY a.id, a.checkpoints_completed, a.checkpoint_status, 
                     cm.total_checkpoints, cm.checkpoint_interval, cm.checkpoint_enabled
            """
            cursor.execute(query, (student_id, meeting_id))
            result = cursor.fetchone()
            cursor.close()
            return result
        except Exception as e:
            print(f"Error getting student checkpoint status: {e}")
            return None
    
    def get_current_checkpoint_number(self, meeting_id):
        """Calculate current checkpoint number based on elapsed time"""
        try:
            if not self.connection or not self.connection.is_connected():
                self.connect()
            
            cursor = self.connection.cursor(dictionary=True)
            query = """
            SELECT 
                meeting_date,
                checkpoint_interval,
                total_checkpoints,
                checkpoint_enabled,
                TIMESTAMPDIFF(MINUTE, meeting_date, NOW()) as elapsed_minutes
            FROM course_meetings
            WHERE id = %s
            """
            cursor.execute(query, (meeting_id,))
            meeting = cursor.fetchone()
            cursor.close()
            
            if not meeting or not meeting['checkpoint_enabled']:
                return 1
            
            elapsed = meeting['elapsed_minutes']
            interval = meeting['checkpoint_interval']
            total = meeting['total_checkpoints']
            
            # Calculate current checkpoint (1-based)
            current_checkpoint = (elapsed // interval) + 1
            
            # Cap at maximum
            if current_checkpoint > total:
                current_checkpoint = total
            if current_checkpoint < 1:
                current_checkpoint = 1
            
            return current_checkpoint
            
        except Exception as e:
            print(f"Error calculating current checkpoint: {e}")
            return 1
    
    def get_meeting_checkpoint_summary(self, meeting_id):
        """Get summary of all students' checkpoint status for a meeting"""
        try:
            if not self.connection or not self.connection.is_connected():
                self.connect()
            
            cursor = self.connection.cursor(dictionary=True)
            query = """
            SELECT 
                s.id as student_id,
                s.name as student_name,
                s.student_id as nim,
                COALESCE(a.checkpoints_completed, 0) as checkpoints_completed,
                COALESCE(a.checkpoint_status, 'not_started') as checkpoint_status,
                cm.total_checkpoints,
                cm.checkpoint_interval,
                cm.checkpoint_enabled,
                GROUP_CONCAT(ac.checkpoint_number ORDER BY ac.checkpoint_number) as completed_checkpoint_numbers,
                a.first_checkpoint_time,
                a.last_checkpoint_time
            FROM students s
            CROSS JOIN course_meetings cm
            LEFT JOIN attendance a ON s.id = a.student_id AND a.meeting_id = cm.id
            LEFT JOIN attendance_checkpoints ac ON a.id = ac.attendance_id
            WHERE cm.id = %s
            GROUP BY s.id, s.name, s.student_id, a.checkpoints_completed, a.checkpoint_status,
                     cm.total_checkpoints, cm.checkpoint_interval, cm.checkpoint_enabled,
                     a.first_checkpoint_time, a.last_checkpoint_time
            ORDER BY s.name
            """
            cursor.execute(query, (meeting_id,))
            result = cursor.fetchall()
            cursor.close()
            return result
        except Exception as e:
            print(f"Error getting meeting checkpoint summary: {e}")
            return []
    
    def get_attendance_details_with_checkpoints(self, class_name=None, start_date=None, end_date=None):
        """Get detailed attendance records with checkpoint information"""
        try:
            if not self.connection or not self.connection.is_connected():
                self.connect()
            
            cursor = self.connection.cursor(dictionary=True)
            
            query = """
            SELECT 
                s.student_id as nim,
                s.name as student_name,
                s.class_name,
                a.attendance_time,
                a.status,
                a.attendance_method,
                a.confidence_score,
                cm.meeting_date,
                cm.meeting_number,
                cm.meeting_topic,
                cm.checkpoint_enabled,
                cm.total_checkpoints,
                cm.checkpoint_interval,
                a.checkpoints_completed,
                a.checkpoint_status,
                a.first_checkpoint_time,
                a.last_checkpoint_time,
                c.name as course_name,
                t.name as teacher_name
            FROM attendance a
            JOIN students s ON a.student_id = s.id
            JOIN course_meetings cm ON a.meeting_id = cm.id
            JOIN schedules sch ON cm.schedule_id = sch.id
            JOIN courses c ON sch.course_id = c.id
            LEFT JOIN teachers t ON sch.teacher_id = t.id
            WHERE 1=1
            """
            
            params = []
            
            if class_name:
                query += " AND s.class_name LIKE %s"
                params.append(f"%{class_name}%")
            
            if start_date:
                query += " AND DATE(cm.meeting_date) >= %s"
                params.append(start_date)
            
            if end_date:
                query += " AND DATE(cm.meeting_date) <= %s"
                params.append(end_date)
            
            query += " ORDER BY cm.meeting_date DESC, s.name"
            
            cursor.execute(query, params if params else None)
            result = cursor.fetchall()
            cursor.close()
            
            return result
            
        except Exception as e:
            print(f"Error getting attendance details with checkpoints: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def get_checkpoint_statistics(self, class_name=None, start_date=None, end_date=None):
        """Get checkpoint statistics summary"""
        try:
            if not self.connection or not self.connection.is_connected():
                self.connect()
            
            cursor = self.connection.cursor(dictionary=True)
            
            query = """
            SELECT 
                COUNT(DISTINCT CASE WHEN cm.checkpoint_enabled = 1 THEN a.id END) as total_with_checkpoints,
                COUNT(CASE WHEN a.checkpoint_status = 'full' THEN 1 END) as full_count,
                COUNT(CASE WHEN a.checkpoint_status = 'good' THEN 1 END) as good_count,
                COUNT(CASE WHEN a.checkpoint_status = 'partial' THEN 1 END) as partial_count,
                COUNT(CASE WHEN a.checkpoint_status = 'poor' THEN 1 END) as poor_count,
                AVG(CASE WHEN cm.checkpoint_enabled = 1 THEN 
                    (a.checkpoints_completed * 100.0 / NULLIF(cm.total_checkpoints, 0))
                END) as avg_checkpoint_completion
            FROM attendance a
            JOIN course_meetings cm ON a.meeting_id = cm.id
            JOIN students s ON a.student_id = s.id
            WHERE cm.checkpoint_enabled = 1
            """
            
            params = []
            
            if class_name:
                query += " AND s.class_name LIKE %s"
                params.append(f"%{class_name}%")
            
            if start_date:
                query += " AND DATE(cm.meeting_date) >= %s"
                params.append(start_date)
            
            if end_date:
                query += " AND DATE(cm.meeting_date) <= %s"
                params.append(end_date)
            
            cursor.execute(query, params if params else None)
            result = cursor.fetchone()
            cursor.close()
            
            return result
            
        except Exception as e:
            print(f"Error getting checkpoint statistics: {e}")
            import traceback
            traceback.print_exc()
            return None
