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
    
    def get_attendance_summary_by_class(self):
        query = """
        SELECT s.id as schedule_id, s.class_name,
               COUNT(DISTINCT st.id) as total_students,
               COUNT(CASE WHEN a.status = 'present' THEN 1 END) as present_count,
               COUNT(a.id) as total_attendance_records,
               ROUND((COUNT(CASE WHEN a.status = 'present' THEN 1 END) * 100.0 / 
                     NULLIF(COUNT(a.id), 0)), 2) as attendance_percentage
        FROM schedules s
        LEFT JOIN course_meetings cm ON s.id = cm.schedule_id
        LEFT JOIN attendance a ON cm.id = a.meeting_id
        LEFT JOIN students st ON a.student_id = st.id
        GROUP BY s.id, s.class_name
        ORDER BY s.class_name
        """
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
        SELECT c.*, t.name as teacher_name
        FROM courses c
        LEFT JOIN teachers t ON c.teacher_id = t.id
        ORDER BY c.course_name
        """
        return self.execute_query(query)
    
    def get_all_teachers(self):
        query = "SELECT * FROM teachers ORDER BY name"
        return self.execute_query(query)
    
    def get_all_schedules(self):
        query = """
        SELECT s.*, c.course_name, t.name as teacher_name
        FROM schedules s
        JOIN courses c ON s.course_id = c.id
        LEFT JOIN teachers t ON c.teacher_id = t.id
        ORDER BY s.day_of_week, s.start_time
        """
        return self.execute_query(query)
    
    def add_student(self, name, student_id, email, phone, program_study_id, face_registered=False):
        query = """
        INSERT INTO students (name, student_id, email, phone, program_study_id, face_registered)
        VALUES (%s, %s, %s, %s, %s, %s)
        """
        params = (name, student_id, email, phone, program_study_id, face_registered)
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
    
    def add_course(self, course_name, course_code, credits, teacher_id, description):
        query = """
        INSERT INTO courses (course_name, course_code, credits, teacher_id, description)
        VALUES (%s, %s, %s, %s, %s)
        """
        params = (course_name, course_code, credits, teacher_id, description)
        return self.execute_query(query, params)
    
    def get_course_by_id(self, course_id):
        query = "SELECT * FROM courses WHERE id = %s"
        result = self.execute_query(query, (course_id,))
        return result[0] if result else None
    
    def update_course(self, course_id, course_name, course_code, credits, teacher_id, description):
        query = """
        UPDATE courses 
        SET course_name = %s, course_code = %s, credits = %s, teacher_id = %s, description = %s
        WHERE id = %s
        """
        params = (course_name, course_code, credits, teacher_id, description, course_id)
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
    
    def add_schedule(self, course_id, class_name, day_of_week, start_time, end_time, room):
        query = """
        INSERT INTO schedules (course_id, class_name, day_of_week, start_time, end_time, room)
        VALUES (%s, %s, %s, %s, %s, %s)
        """
        params = (course_id, class_name, day_of_week, start_time, end_time, room)
        return self.execute_query(query, params)
    
    def get_schedule_by_id(self, schedule_id):
        query = "SELECT * FROM schedules WHERE id = %s"
        result = self.execute_query(query, (schedule_id,))
        return result[0] if result else None
    
    def update_schedule(self, schedule_id, course_id, class_name, day_of_week, start_time, end_time, room):
        query = """
        UPDATE schedules 
        SET course_id = %s, class_name = %s, day_of_week = %s, start_time = %s, end_time = %s, room = %s
        WHERE id = %s
        """
        params = (course_id, class_name, day_of_week, start_time, end_time, room, schedule_id)
        return self.execute_query(query, params)
    
    def delete_schedule(self, schedule_id):
        query = "DELETE FROM schedules WHERE id = %s"
        return self.execute_query(query, (schedule_id,))
    
    def get_today_schedules(self):
        from datetime import datetime
        today = datetime.now().weekday() + 1  # Monday is 0, but in DB Monday is 1
        if today > 7:
            today = 1
        
        query = """
        SELECT s.*, c.course_name, t.name as teacher_name
        FROM schedules s
        JOIN courses c ON s.course_id = c.id
        LEFT JOIN teachers t ON c.teacher_id = t.id
        WHERE s.day_of_week = %s
        ORDER BY s.start_time
        """
        return self.execute_query(query, (today,))
    
    def get_attendance_chart_data(self):
        query = """
        SELECT DATE(a.attendance_time) as date,
               COUNT(CASE WHEN a.status = 'present' THEN 1 END) as present,
               COUNT(CASE WHEN a.status = 'absent' THEN 1 END) as absent,
               COUNT(CASE WHEN a.status = 'late' THEN 1 END) as late,
               COUNT(CASE WHEN a.status = 'excused' THEN 1 END) as excused
        FROM attendance a
        WHERE a.attendance_time >= DATE_SUB(CURRENT_DATE, INTERVAL 7 DAY)
        GROUP BY DATE(a.attendance_time)
        ORDER BY DATE(a.attendance_time)
        """
        return self.execute_query(query)
    
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
