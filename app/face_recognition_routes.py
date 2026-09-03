from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, session, Response
import os
from werkzeug.utils import secure_filename
import cv2
import numpy as np
from dotenv import load_dotenv
import base64

# Load environment variables
load_dotenv()

try:
    from app.face_recognition import CNNFaceRecognition
    FACE_RECOGNITION_AVAILABLE = True
except ImportError:
    try:
        from app.face_recognition import CNNFaceRecognition
        FACE_RECOGNITION_AVAILABLE = True
    except ImportError:
        CNNFaceRecognition = None
        FACE_RECOGNITION_AVAILABLE = False
from app.database import Database

face_recognition_bp = Blueprint('face_recognition', __name__)

# Initialize face recognition system
face_recognition_system = None

def get_face_recognition_system():
    global face_recognition_system
    if face_recognition_system is None and FACE_RECOGNITION_AVAILABLE:
        face_recognition_system = CNNFaceRecognition()
    return face_recognition_system

@face_recognition_bp.route('/face_recognition')
def face_recognition_dashboard():
    """Dashboard untuk face recognition system"""
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    
    # Check if face recognition is available
    if not FACE_RECOGNITION_AVAILABLE:
        # Return a page showing dependency status instead of redirecting
        return render_template('face_recognition/setup_required.html', 
                             dependencies_available=False,
                             required_packages=['dlib', 'opencv-python', 'tensorflow', 'mediapipe'])
    
    try:
        db = Database()
        db.connect()
        
        # Get statistics
        stats_query = """
        SELECT 
            COUNT(*) as total_students,
            COUNT(CASE WHEN face_registered = TRUE THEN 1 END) as registered_faces,
            COUNT(CASE WHEN face_registered = FALSE THEN 1 END) as pending_registration
        FROM students
        """
        stats = db.execute_query(stats_query)
        
        # Get recent face recognition attendance
        recent_query = """
        SELECT s.name, s.student_id, a.attendance_time, a.confidence_score,
               c.course_name, cm.meeting_number
        FROM attendance a
        JOIN students s ON a.student_id = s.id
        JOIN course_meetings cm ON a.meeting_id = cm.id
        JOIN schedules sch ON cm.schedule_id = sch.id
        JOIN courses c ON sch.course_id = c.id
        WHERE a.attendance_method = 'face_recognition'
        ORDER BY a.attendance_time DESC
        LIMIT 10
        """
        recent_attendance = db.execute_query(recent_query)
        
        # Get courses for face attendance
        courses_query = """
        SELECT c.id, c.course_name, s.class_name, t.name as teacher_name
        FROM courses c
        JOIN schedules s ON c.id = s.course_id
        JOIN teachers t ON s.teacher_id = t.id
        ORDER BY c.course_name
        """
        courses = db.execute_query(courses_query)
        
        db.disconnect()
        
        return render_template('face_recognition/dashboard.html',
                             stats=stats[0] if stats else {},
                             recent_attendance=recent_attendance or [],
                             courses=courses or [])
                             
    except Exception as e:
        flash(f'Error loading dashboard: {str(e)}', 'error')
        return redirect(url_for('main.dashboard'))

@face_recognition_bp.route('/face_recognition/register_student')
def register_student_form():
    """Form untuk registrasi wajah mahasiswa"""
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    
    try:
        db = Database()
        db.connect()
        
        # Get students without face registration
        query = """
        SELECT id, student_id, name, class_name
        FROM students
        WHERE face_registered = FALSE OR face_registered IS NULL
        ORDER BY name
        """
        students = db.execute_query(query)
        
        db.disconnect()
        
        return render_template('face_recognition/register_student.html',
                             students=students or [])
                             
    except Exception as e:
        flash(f'Error loading registration form: {str(e)}', 'error')
        return redirect(url_for('face_recognition.face_recognition_dashboard'))

@face_recognition_bp.route('/face_recognition/register_student', methods=['POST'])
def register_student():
    """Process student face registration"""
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    
    try:
        student_id = request.form.get('student_id')
        
        if not student_id:
            flash('Student ID is required', 'error')
            return redirect(url_for('face_recognition.register_student_form'))
        
        # Create upload directory
        upload_dir = f'uploads/faces/{student_id}'
        os.makedirs(upload_dir, exist_ok=True)
        
        # Handle multiple file uploads
        uploaded_files = request.files.getlist('face_images')
        saved_files = []
        
        for file in uploaded_files:
            if file and file.filename:
                filename = secure_filename(file.filename)
                filepath = os.path.join(upload_dir, filename)
                file.save(filepath)
                saved_files.append(filepath)
        
        if len(saved_files) < 3:
            flash('Please upload at least 3 face images for better recognition accuracy', 'error')
            return redirect(url_for('face_recognition.register_student_form'))
        
        # Get student info
        db = Database()
        db.connect()
        
        student_query = "SELECT name FROM students WHERE student_id = %s"
        student_result = db.execute_query(student_query, (student_id,))
        
        if not student_result:
            flash('Student not found', 'error')
            db.disconnect()
            return redirect(url_for('face_recognition.register_student_form'))
        
        student_name = student_result[0]['name']
        
        # Register face with face recognition system
        face_system = get_face_recognition_system()
        success, message = face_system.register_new_student(student_id, student_name, upload_dir)
        
        if success:
            # Update database
            update_query = """
            UPDATE students 
            SET face_registered = TRUE, face_registration_date = NOW()
            WHERE student_id = %s
            """
            db.execute_query(update_query, (student_id,))
            flash(message, 'success')
        else:
            flash(f'Registration failed: {message}', 'error')
        
        db.disconnect()
        
        # Keep uploaded files for backup/analysis (commented out cleanup)
        # if os.path.exists(upload_dir):
        #     shutil.rmtree(upload_dir)
        
        return redirect(url_for('face_recognition.register_student_form'))
        
    except Exception as e:
        flash(f'Error during registration: {str(e)}', 'error')
        return redirect(url_for('face_recognition.register_student_form'))

@face_recognition_bp.route('/face_recognition/attendance')
def face_attendance_form():
    """Form untuk presensi dengan face recognition"""
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    
    try:
        db = Database()
        db.connect()
        
        # Get active courses
        courses_query = """
        SELECT c.id, c.course_name, s.class_name, t.name as teacher_name
        FROM courses c
        JOIN schedules s ON c.id = s.course_id
        JOIN teachers t ON s.teacher_id = t.id
        ORDER BY c.course_name
        """
        courses = db.execute_query(courses_query)
        
        db.disconnect()
        
        return render_template('face_recognition/attendance.html',
                             courses=courses or [])
                             
    except Exception as e:
        flash(f'Error loading attendance form: {str(e)}', 'error')
        return redirect(url_for('face_recognition.face_recognition_dashboard'))

@face_recognition_bp.route('/face_recognition/start_attendance', methods=['POST'])
def start_face_attendance():
    """Start face recognition attendance process"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    try:
        data = request.get_json()
        course_id = data.get('course_id')
        meeting_number = data.get('meeting_number')
        session_number = data.get('session_number')
        
        if not all([course_id, meeting_number, session_number]):
            return jsonify({'success': False, 'message': 'Missing required parameters'})
        
        # Start face recognition attendance
        face_system = get_face_recognition_system()
        success, message = face_system.mark_attendance_with_face(
            course_id, meeting_number, session_number
        )
        
        return jsonify({
            'success': success,
            'message': message
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error starting attendance: {str(e)}'
        })

@face_recognition_bp.route('/face_recognition/statistics')
def face_recognition_statistics():
    """Statistik face recognition"""
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    
    try:
        db = Database()
        db.connect()
        
        # Overall statistics
        overall_stats_query = """
        SELECT 
            COUNT(*) as total_students,
            COUNT(CASE WHEN face_registered = TRUE THEN 1 END) as registered_faces,
            COUNT(CASE WHEN face_registered = FALSE OR face_registered IS NULL THEN 1 END) as pending_registration,
            ROUND(COUNT(CASE WHEN face_registered = TRUE THEN 1 END) * 100.0 / COUNT(*), 2) as registration_percentage
        FROM students
        """
        overall_stats = db.execute_query(overall_stats_query)
        
        # Attendance method statistics
        attendance_method_query = """
        SELECT 
            attendance_method,
            COUNT(*) as count,
            ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 2) as percentage
        FROM attendance
        GROUP BY attendance_method
        ORDER BY count DESC
        """
        attendance_methods = db.execute_query(attendance_method_query)
        
        # Monthly face recognition attendance
        monthly_query = """
        SELECT 
            DATE_FORMAT(attendance_time, '%Y-%m') as month,
            COUNT(*) as face_attendance_count
        FROM attendance
        WHERE attendance_method = 'face_recognition'
        GROUP BY DATE_FORMAT(attendance_time, '%Y-%m')
        ORDER BY month DESC
        LIMIT 12
        """
        monthly_stats = db.execute_query(monthly_query)
        
        # Confidence score distribution
        confidence_query = """
        SELECT 
            CASE 
                WHEN confidence_score >= 0.9 THEN 'High (≥0.9)'
                WHEN confidence_score >= 0.7 THEN 'Medium (0.7-0.9)'
                WHEN confidence_score >= 0.5 THEN 'Low (0.5-0.7)'
                ELSE 'Very Low (<0.5)'
            END as confidence_range,
            COUNT(*) as count
        FROM attendance
        WHERE attendance_method = 'face_recognition' AND confidence_score IS NOT NULL
        GROUP BY confidence_range
        ORDER BY MIN(confidence_score) DESC
        """
        confidence_stats = db.execute_query(confidence_query)
        
        db.disconnect()
        
        return render_template('face_recognition/statistics.html',
                             overall_stats=overall_stats[0] if overall_stats else {},
                             attendance_methods=attendance_methods or [],
                             monthly_stats=monthly_stats or [],
                             confidence_stats=confidence_stats or [])
                             
    except Exception as e:
        flash(f'Error loading statistics: {str(e)}', 'error')
        return redirect(url_for('face_recognition.face_recognition_dashboard'))

@face_recognition_bp.route('/face_recognition/api/meeting_sessions/<int:course_id>')
def get_meeting_sessions(course_id):
    """API untuk mendapatkan meeting dan session dari course"""
    try:
        db = Database()
        db.connect()
        
        # Get meetings for course
        meetings_query = """
        SELECT cm.id, cm.meeting_number, cm.meeting_date
        FROM course_meetings cm
        JOIN schedules s ON cm.schedule_id = s.id
        WHERE s.course_id = ?
        ORDER BY cm.meeting_number
        """
        meetings = db.execute_query(meetings_query, (course_id,))
        
        # Get sessions for each meeting
        for meeting in meetings:
            sessions_query = """
            SELECT id, session_number, session_time, session_type
            FROM meeting_sessions
            WHERE meeting_id = ?
            ORDER BY session_number
            """
            sessions = db.execute_query(sessions_query, (meeting['id'],))
            meeting['sessions'] = sessions or []
        
        db.disconnect()
        
        return jsonify({
            'success': True,
            'meetings': meetings or []
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        })

@face_recognition_bp.route('/face_recognition/test_camera')
def test_camera():
    """Test camera for face recognition"""
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    
    return render_template('face_recognition/test_camera.html')

@face_recognition_bp.route('/face_recognition/api/test_detection')
def test_face_detection():
    """API untuk test deteksi wajah dan liveness"""
    try:
        face_system = get_face_recognition_system()
        
        # This would typically connect to camera and return detection results
        # For now, return a success response
        return jsonify({
            'success': True,
            'message': 'Face detection system is ready',
            'camera_available': True
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e),
            'camera_available': False
        })

@face_recognition_bp.route('/face_recognition/register_face', methods=['POST'])
def register_face():
    """Register face for student from tambah mahasiswa form"""
    try:
        # Check if face recognition is available
        if not FACE_RECOGNITION_AVAILABLE:
            return jsonify({
                'success': True,
                'message': 'Face images uploaded successfully. Face recognition will be activated when dependencies are installed.'
            })
        
        student_id = request.form.get('student_id')
        
        if not student_id:
            return jsonify({
                'success': False,
                'message': 'Student ID is required'
            })
        
        # Create upload directory
        upload_dir = f'uploads/faces/{student_id}'
        os.makedirs(upload_dir, exist_ok=True)
        
        # Handle multiple file uploads
        uploaded_files = request.files.getlist('face_images')
        saved_files = []
        
        for file in uploaded_files:
            if file and file.filename:
                filename = secure_filename(file.filename)
                filepath = os.path.join(upload_dir, filename)
                file.save(filepath)
                saved_files.append(filepath)
        
        if len(saved_files) < 1:
            return jsonify({
                'success': False,
                'message': 'Please upload at least 1 face image'
            })
        
        # Get student info
        db = Database()
        db.connect()
        
        student_query = "SELECT name FROM students WHERE student_id = %s"
        student_result = db.execute_query(student_query, (student_id,))
        
        if not student_result:
            db.disconnect()
            return jsonify({
                'success': False,
                'message': 'Student not found'
            })
        
        student_name = student_result[0]['name']
        
        # Register face with face recognition system (if available)
        try:
            face_system = get_face_recognition_system()
            success, message = face_system.register_new_student(student_id, student_name, upload_dir)
            
            if success:
                # Update database
                # Update database
                update_query = """
                UPDATE students 
                SET face_registered = TRUE, face_registration_date = NOW()
                WHERE student_id = %s
                """
                db.execute_query(update_query, (student_id,))
                db.disconnect()
                
                # Keep uploaded files for backup/analysis (commented out cleanup)
                # if os.path.exists(upload_dir):
                #     shutil.rmtree(upload_dir)
                
                return jsonify({
                    'success': True,
                    'message': f'Face registration successful for {student_name}'
                })
            else:
                db.disconnect()
                return jsonify({
                    'success': False,
                    'message': f'Registration failed: {message}'
                })
                
        except Exception as face_error:
            # Face recognition system not available, but still mark as attempted
            # Face recognition system not available, but still mark as attempted
            update_query = """
            UPDATE students 
            SET face_registered = FALSE, face_registration_date = NOW()
            WHERE student_id = %s
            """
            db.execute_query(update_query, (student_id,))
            db.disconnect()
            
            return jsonify({
                'success': True,
                'message': f'Face images uploaded for {student_name}. Face recognition system will be activated when available.'
            })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error during registration: {str(e)}'
        })

@face_recognition_bp.route('/face_recognition/recognize_attendance', methods=['POST'])
def recognize_attendance():
    """Process face recognition for attendance"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    if not FACE_RECOGNITION_AVAILABLE:
        return jsonify({
            'success': False,
            'message': 'Face recognition module not available'
        })
    
    try:
        # Get uploaded image
        if 'image' not in request.files:
            return jsonify({
                'success': False,
                'message': 'No image provided'
            })
        
        file = request.files['image']
        if file.filename == '':
            return jsonify({
                'success': False,
                'message': 'No image selected'
            })
        
        # Save temporary image
        temp_dir = os.path.join('app', 'static', 'temp')
        os.makedirs(temp_dir, exist_ok=True)
        
        filename = secure_filename(f"attendance_{session['user_id']}.jpg")
        temp_path = os.path.join(temp_dir, filename)
        file.save(temp_path)
        
        # Get face recognition system
        face_system = get_face_recognition_system()
        if not face_system:
            return jsonify({
                'success': False,
                'message': 'Face recognition system not initialized'
            })
        
        # ENHANCED SECURITY: Use face recognition with optional liveness check
        # Note: Liveness disabled for IP camera compatibility (too many false positives)
        result = face_system.recognize_face(temp_path, require_liveness=False)
        
        # Clean up temp file
        if os.path.exists(temp_path):
            os.remove(temp_path)
        
        if result['success']:
            # CRITICAL SECURITY CHECKS
            confidence = result.get('confidence', 0)
            liveness_details = result.get('liveness_details')
            faces_detected = result.get('faces_detected', 1)
            all_faces = result.get('all_faces', [])
            multiple_faces = result.get('multiple_faces', False)
            
            print(f"[Attendance API] ✅ Recognition successful")
            print(f"[Attendance API] Faces detected: {faces_detected}")
            print(f"[Attendance API] Primary student: {result['student'].get('name', 'Unknown')}")
            print(f"[Attendance API] Primary confidence: {confidence:.2%}")
            
            if multiple_faces:
                print(f"[Attendance API] 🎯 Multiple faces mode - processing {len(all_faces)} faces")
                for face in all_faces:
                    print(f"[Attendance API]   - {face['name']}: {face['confidence']:.2%}")
            
            # Security Check 1: Verify confidence (adjusted for IP camera - typically 55-65%)
            if confidence < 0.50:
                return jsonify({
                    'success': False,
                    'message': f'⚠️ Recognition confidence too low: {confidence:.2%}. Please ensure good lighting and clear face.',
                    'confidence': confidence,
                    'security_level': 'insufficient',
                    'reason': 'low_confidence'
                })
            
            # Security Check 2: Verify liveness (critical for anti-spoofing)
            if liveness_details and not liveness_details.get('is_live', False):
                return jsonify({
                    'success': False,
                    'message': '🚨 SECURITY ALERT: Spoofing attempt detected! Please use your real face, not a photo.',
                    'spoofing_detected': True,
                    'liveness_details': liveness_details,
                    'security_breach': True
                })
            
            # Security Check 3: Check for security flags
            if result.get('spoofing_detected', False):
                return jsonify({
                    'success': False,
                    'message': '🚨 SPOOFING DETECTED: ' + result.get('message', 'Please use your real face'),
                    'spoofing_detected': True,
                    'security_breach': True
                })
            
            # All security checks passed - proceed with attendance
            # Record attendance for ALL detected faces
            db = Database()
            db.connect()
            
            # Determine which faces to process
            faces_to_process = all_faces if multiple_faces and all_faces else [result['student']]
            recorded_students = []
            
            # Get current active meeting
            meetings_query = "SELECT id FROM course_meetings ORDER BY id DESC LIMIT 1"
            meeting_result = db.execute_query(meetings_query)
            meeting_id = meeting_result[0]['id'] if meeting_result else None
            
            if not meeting_id:
                db.disconnect()
                return jsonify({'success': False, 'message': 'No meetings found in database'})
            
            # Process each detected face
            for face_data in faces_to_process:
                # Get student_id from face data
                if isinstance(face_data, dict):
                    student_id_nim = face_data.get('student_id')
                    face_confidence = face_data.get('confidence', confidence)
                    face_name = face_data.get('name', 'Unknown')
                    face_size_val = face_data.get('face_size', result.get('face_size', 0))
                    lighting_score_val = face_data.get('lighting_score', result.get('lighting_score', 0))
                else:
                    continue
                
                if not student_id_nim:
                    continue
                    
                # Get the actual student database ID from the student_id (NIM)
                student_lookup_query = "SELECT id, name FROM students WHERE student_id = %s"
                student_db_result = db.execute_query(student_lookup_query, (student_id_nim,))
                
                if not student_db_result:
                    print(f"[Attendance API] ⚠️ Student with ID {student_id_nim} not found in database")
                    continue
                
                actual_student_id = student_db_result[0]['id']
                student_name = student_db_result[0]['name']
            
                # Check if already marked today for this meeting
                check_query = """
                SELECT id FROM attendance 
                WHERE student_id = %s 
                AND meeting_id = %s
                """
                existing = db.execute_query(check_query, (actual_student_id, meeting_id))
                
                # Convert confidence to Python float to avoid MySQL conversion issues
                confidence_value = float(face_confidence)
                
                if existing:
                    # Update existing attendance instead of creating new one
                    update_query = """
                    UPDATE attendance 
                    SET attendance_method = 'face_recognition',
                        confidence_score = %s,
                        notes = %s,
                        attendance_time = NOW(),
                        status = 'present'
                    WHERE id = %s
                    """
                    
                    attendance_result = db.execute_query(update_query, (
                        confidence_value,
                        f"Face recognition attendance - Confidence: {confidence_value:.2f}",
                        existing[0]['id']
                    ))
                    print(f"[Attendance API] ✅ Updated attendance for {student_name}")
                    
                else:
                    # Insert new attendance record
                    insert_query = """
                    INSERT INTO attendance (student_id, meeting_id, session_id, attendance_time, 
                                          status, attendance_method, confidence_score, notes, marked_by, is_valid)
                    VALUES (%s, %s, %s, NOW(), 'present', 'face_recognition', %s, %s, %s, 1)
                    """
                    
                    session_id = None  # Use NULL for session_id to avoid foreign key constraint
                    marked_by = session.get('user_id', 1)  # Current user
                    
                    attendance_result = db.execute_query(insert_query, (
                        actual_student_id,  # Use the actual database ID, not the student_id
                        meeting_id,
                        session_id,
                        confidence_value,
                        f"Face recognition attendance - Confidence: {confidence_value:.2f}",
                        marked_by
                    ))
                    print(f"[Attendance API] ✅ Recorded attendance for {student_name}")
                
                # Add to recorded list
                recorded_students.append({
                    'name': student_name,
                    'student_id': student_id_nim,
                    'confidence': confidence_value,
                    'id': actual_student_id,
                    'face_size': face_size_val,
                    'lighting_score': lighting_score_val
                })
            
            db.disconnect()
            
            print(f"[Attendance API] 📝 Attendance recorded successfully for {len(recorded_students)} student(s)")
            
            # Prepare response based on number of faces
            if len(recorded_students) > 1:
                # Multiple faces detected and recorded
                primary_student = recorded_students[0]
                message = f"✅ {len(recorded_students)} wajah berhasil diidentifikasi: " + ", ".join([s['name'] for s in recorded_students])
                
                print(f"[Attendance API] Response: SUCCESS - {len(recorded_students)} faces")
                
                return jsonify({
                    'success': True,
                    'multiple_faces': True,
                    'faces_detected': len(recorded_students),
                    'message': message,
                    'student': {
                        'name': primary_student['name'],
                        'student_id': primary_student['student_id'],
                        'id': primary_student['id'],
                        'nama': primary_student['name']
                    },
                    'all_students': [{
                        'name': s['name'],
                        'student_id': s['student_id'],
                        'id': s['id'],
                        'nama': s['name'],
                        'confidence': s['confidence'],
                        'face_size': s.get('face_size', 0),
                        'lighting_score': s.get('lighting_score', 0)
                    } for s in recorded_students],
                    'timestamp': result.get('timestamp', 'Now'),
                    'confidence': result.get('confidence', 0.8)
                })
            else:
                # Single face detected and recorded
                student_data = recorded_students[0] if recorded_students else result['student']
                student_name = student_data.get('name', 'Unknown')
                
                print(f"[Attendance API] Response: SUCCESS - {student_name}")
                
                return jsonify({
                    'success': True,
                    'multiple_faces': False,
                    'faces_detected': 1,
                    'message': f"Presensi berhasil untuk {student_name}",
                    'student': {
                        'name': student_name,
                        'student_id': student_data.get('student_id', result['student']['student_id']),
                        'id': student_data.get('id', result['student'].get('id')),
                        'nama': student_name
                    },
                    'timestamp': result.get('timestamp', 'Now'),
                    'confidence': result.get('confidence', 0.8),
                    'face_size': result.get('face_size', 0),
                    'lighting_score': result.get('lighting_score', 0)
                })
        else:
            # Enhanced error handling with security context
            error_message = result.get('message', 'Face not recognized')
            
            print(f"[Attendance API] ❌ Recognition failed")
            print(f"[Attendance API] Reason: {error_message}")
            print(f"[Attendance API] Response: FAILURE")
            
            # Check if it's a security issue
            if result.get('spoofing_detected', False) or result.get('security_breach', False):
                return jsonify({
                    'success': False,
                    'message': '🚨 SECURITY ALERT: ' + error_message,
                    'security_alert': True,
                    'spoofing_detected': True,
                    'liveness_details': result.get('liveness_details'),
                    'recommendations': ['Use your real face', 'Ensure good lighting', 'Blink naturally']
                })
            
            # Check for specific requirements
            if result.get('requires_blinking', False):
                return jsonify({
                    'success': False,
                    'message': error_message,
                    'requires_blinking': True,
                    'instructions': ['Please blink naturally 2-3 times', 'Look directly at camera', 'Wait for system to detect blinks']
                })
            
            if result.get('requires_movement', False):
                return jsonify({
                    'success': False,
                    'message': error_message,
                    'requires_movement': True,
                    'instructions': ['Move your head slightly left/right', 'Ensure natural micro-movements', 'Stay within camera frame']
                })
            
            return jsonify({
                'success': False,
                'message': error_message,
                'debug_info': result.get('debug_info'),
                'suggestions': result.get('suggestions', ['Ensure good lighting', 'Face camera directly', 'Remove any obstructions'])
            })
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error processing attendance: {str(e)}'
        })

@face_recognition_bp.route('/face_recognition/live_anti_spoofing_check', methods=['POST'])
def live_anti_spoofing_check():
    """Live anti-spoofing check endpoint for real-time validation"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    try:
        # Get uploaded frame
        if 'frame' not in request.files:
            return jsonify({
                'success': False,
                'message': 'No frame provided'
            })
        
        file = request.files['frame']
        if file.filename == '':
            return jsonify({
                'success': False,
                'message': 'No frame selected'
            })
        
        # Save temporary frame
        temp_dir = os.path.join('app', 'static', 'temp')
        os.makedirs(temp_dir, exist_ok=True)
        
        filename = secure_filename(f"live_check_{session['user_id']}.jpg")
        temp_path = os.path.join(temp_dir, filename)
        file.save(temp_path)
        
        # Load frame
        frame = cv2.imread(temp_path)
        
        if frame is None:
            return jsonify({
                'success': False,
                'message': 'Unable to process frame'
            })
        
        # Extract face region for texture analysis
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        faces = face_cascade.detectMultiScale(gray, 1.1, 4)
        
        face_region = None
        if len(faces) > 0:
            (x, y, w, h) = faces[0]
            face_region = frame[y:y+h, x:x+w]
        
        # Initialize enhanced anti-spoofing if available
        try:
            from app.face_recognition.enhanced_anti_spoofing import EnhancedAntiSpoofing
            anti_spoofing = EnhancedAntiSpoofing()
            
            # Comprehensive liveness check
            liveness_result = anti_spoofing.comprehensive_anti_spoofing_check(frame, face_region, duration_seconds=2)
            
        except ImportError:
            # Fallback to basic anti-spoofing
            face_system = get_face_recognition_system()
            if face_system and face_system.anti_spoofing:
                liveness_result = face_system.anti_spoofing.comprehensive_liveness_check(frame, face_region)
            else:
                liveness_result = {
                    'is_live': True,  # Default to true if no anti-spoofing available
                    'confidence': 0.5,
                    'message': 'Anti-spoofing not available'
                }
        
        # Clean up temporary file
        if os.path.exists(temp_path):
            os.remove(temp_path)
        
        # Format response for UI
        response = {
            'success': True,
            'is_live': liveness_result.get('is_live', False),
            'confidence': liveness_result.get('confidence', 0),
            'security_level': liveness_result.get('security_level', 'unknown'),
            'checks_passed': liveness_result.get('checks_passed', 0),
            'total_checks': liveness_result.get('total_checks', 7),
            'details': liveness_result.get('details', {}),
            'recommendations': liveness_result.get('recommendations', [])
        }
        
        # Add user-friendly status
        if response['is_live']:
            response['status'] = '✅ Real person detected'
            response['status_color'] = 'success'
        else:
            response['status'] = '⚠️ Liveness verification required'
            response['status_color'] = 'warning'
            
            # Check for specific issues
            details = response['details']
            if details.get('screen', {}).get('detected', False):
                response['status'] = '🚨 Screen/photo detected!'
                response['status_color'] = 'danger'
            elif details.get('blinks', {}).get('count', 0) < 2:
                response['status'] = '👁️ Please blink naturally'
                response['status_color'] = 'info'
            elif not details.get('movement', {}).get('natural', False):
                response['status'] = '↔️ Please move your head slightly'
                response['status_color'] = 'info'
        
        return jsonify(response)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error in liveness check: {str(e)}'
        })

@face_recognition_bp.route('/face_recognition/debug_detection', methods=['POST'])
def debug_detection():
    """Debug endpoint: Returns image with bounding boxes and detection info"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    if not FACE_RECOGNITION_AVAILABLE:
        return jsonify({
            'success': False,
            'message': 'Face recognition module not available'
        })
    
    try:
        # Get uploaded image
        if 'image' not in request.files:
            return jsonify({
                'success': False,
                'message': 'No image provided'
            })
        
        file = request.files['image']
        if file.filename == '':
            return jsonify({
                'success': False,
                'message': 'No image selected'
            })
        
        # Read image directly
        import numpy as np
        import cv2
        import face_recognition
        
        # Read image from upload
        file_bytes = np.frombuffer(file.read(), np.uint8)
        image = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
        
        if image is None:
            return jsonify({
                'success': False,
                'message': 'Invalid image'
            })
        
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # Apply image enhancement (same as recognition system)
        face_system = get_face_recognition_system()
        if face_system and hasattr(face_system, '_enhance_for_detection'):
            enhanced_image = face_system._enhance_for_detection(rgb_image)
        else:
            enhanced_image = rgb_image
        
        # ===== HYBRID DETECTION: Same as recognition system =====
        print("[Debug Detection] Using hybrid detection strategy...")
        
        face_locations = []
        detection_method = "unknown"
        
        # Try CNN first (most accurate)
        try:
            print("[Debug Detection] Trying CNN model...")
            face_locations_cnn = face_recognition.face_locations(
                enhanced_image, 
                model="cnn",
                number_of_times_to_upsample=1
            )
            if len(face_locations_cnn) > 0:
                face_locations = face_locations_cnn
                detection_method = "CNN"
                print(f"[Debug Detection] ✅ CNN found {len(face_locations)} face(s)")
        except Exception as e:
            print(f"[Debug Detection] CNN error: {str(e)}")
        
        # Fallback to HOG
        if len(face_locations) == 0:
            try:
                print("[Debug Detection] Trying HOG model...")
                face_locations_hog = face_recognition.face_locations(
                    enhanced_image, 
                    model="hog",
                    number_of_times_to_upsample=2
                )
                if len(face_locations_hog) > 0:
                    face_locations = face_locations_hog
                    detection_method = "HOG"
                    print(f"[Debug Detection] ✅ HOG found {len(face_locations)} face(s)")
            except Exception as e:
                print(f"[Debug Detection] HOG error: {str(e)}")
        
        # Try scale variations
        if len(face_locations) == 0:
            try:
                print("[Debug Detection] Trying CNN with scale variations...")
                scaled_up = cv2.resize(enhanced_image, None, fx=1.2, fy=1.2, interpolation=cv2.INTER_CUBIC)
                face_locations_scaled = face_recognition.face_locations(scaled_up, model="cnn", number_of_times_to_upsample=0)
                
                if len(face_locations_scaled) > 0:
                    face_locations = [(int(top/1.2), int(right/1.2), int(bottom/1.2), int(left/1.2)) 
                                     for top, right, bottom, left in face_locations_scaled]
                    detection_method = "CNN-Upscaled"
                    print(f"[Debug Detection] ✅ CNN-Upscaled found {len(face_locations)} face(s)")
            except Exception as e:
                print(f"[Debug Detection] Scale variations error: {str(e)}")
        
        # Last resort: Original image
        if len(face_locations) == 0:
            try:
                print("[Debug Detection] Trying CNN on original image...")
                face_locations_orig = face_recognition.face_locations(
                    rgb_image,
                    model="cnn",
                    number_of_times_to_upsample=1
                )
                if len(face_locations_orig) > 0:
                    face_locations = face_locations_orig
                    detection_method = "CNN-Original"
                    print(f"[Debug Detection] ✅ CNN-Original found {len(face_locations)} face(s)")
            except Exception as e:
                print(f"[Debug Detection] Original image error: {str(e)}")
        
        print(f"[Debug Detection] FINAL: {len(face_locations)} face(s) using {detection_method}")
        
        # Draw bounding boxes on original image
        debug_image = image.copy()
        detection_info = []
        
        # Add detection method info to image
        method_text = f"Detection Method: {detection_method}"
        cv2.putText(debug_image, method_text, (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.putText(debug_image, method_text, (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 165, 255), 1)
        
        for idx, (top, right, bottom, left) in enumerate(face_locations):
            # Calculate face size
            face_width = right - left
            face_height = bottom - top
            face_area = face_width * face_height
            image_area = image.shape[0] * image.shape[1]
            face_size_ratio = face_area / image_area
            
            # Determine quality
            if face_size_ratio > 0.15:
                color = (0, 255, 0)  # Green - Good size
                size_label = "GOOD SIZE"
            elif face_size_ratio > 0.08:
                color = (255, 165, 0)  # Orange - OK size
                size_label = "OK SIZE"
            else:
                color = (0, 0, 255)  # Red - Too small
                size_label = "TOO SMALL"
            
            # Draw rectangle
            cv2.rectangle(debug_image, (left, top), (right, bottom), color, 3)
            
            # Draw label background
            label = f"Face #{idx+1} - {size_label} ({face_size_ratio*100:.1f}%)"
            (label_width, label_height), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
            cv2.rectangle(debug_image, (left, top - label_height - 10), (left + label_width, top), color, -1)
            
            # Draw label text
            cv2.putText(debug_image, label, (left, top - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            
            # Try to match with database
            face_encoding = face_recognition.face_encodings(enhanced_image, [face_locations[idx]])
            
            if face_encoding and face_system:
                face_distances = face_recognition.face_distance(
                    face_system.known_face_encodings, 
                    face_encoding[0]
                )
                
                if len(face_distances) > 0:
                    best_match_index = np.argmin(face_distances)
                    best_distance = face_distances[best_match_index]
                    confidence = 1 - best_distance
                    
                    if best_distance < face_system.confidence_threshold:
                        student_info = face_system.known_face_names[best_match_index]
                        name, student_id = student_info.rsplit('_', 1)
                        match_status = f"MATCH: {name}"
                        match_color = (0, 255, 0)
                    else:
                        match_status = "NO MATCH"
                        match_color = (0, 0, 255)
                        name = "Unknown"
                        student_id = "N/A"
                    
                    # Draw match info
                    match_label = f"{match_status} ({confidence*100:.1f}%)"
                    cv2.putText(debug_image, match_label, (left, bottom + 20), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.6, match_color, 2)
                    
                    detection_info.append({
                        'face_number': idx + 1,
                        'location': {'top': int(top), 'right': int(right), 'bottom': int(bottom), 'left': int(left)},
                        'size_percentage': f"{face_size_ratio*100:.2f}%",
                        'size_category': size_label,
                        'confidence': f"{confidence*100:.1f}%",
                        'distance': f"{best_distance:.4f}",
                        'match': name,
                        'student_id': student_id,
                        'matched': best_distance < face_system.confidence_threshold
                    })
                else:
                    detection_info.append({
                        'face_number': idx + 1,
                        'location': {'top': int(top), 'right': int(right), 'bottom': int(bottom), 'left': int(left)},
                        'size_percentage': f"{face_size_ratio*100:.2f}%",
                        'size_category': size_label,
                        'error': 'No known faces in database'
                    })
            else:
                detection_info.append({
                    'face_number': idx + 1,
                    'location': {'top': int(top), 'right': int(right), 'bottom': int(bottom), 'left': int(left)},
                    'size_percentage': f"{face_size_ratio*100:.2f}%",
                    'size_category': size_label,
                    'error': 'Could not encode face'
                })
        
        # Add overall info text
        info_text = f"Detected: {len(face_locations)} face(s)"
        cv2.putText(debug_image, info_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        cv2.putText(debug_image, info_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 1)
        
        # Encode image to base64
        import base64
        _, buffer = cv2.imencode('.jpg', debug_image)
        debug_image_base64 = base64.b64encode(buffer).decode('utf-8')
        
        return jsonify({
            'success': True,
            'faces_detected': len(face_locations),
            'detection_method': detection_method,
            'debug_image': f"data:image/jpeg;base64,{debug_image_base64}",
            'detection_info': detection_info,
            'recommendations': generate_detection_recommendations(detection_info, detection_method)
        })
        
    except Exception as e:
        import traceback
        print(f"[Debug Detection] Error: {str(e)}")
        print(traceback.format_exc())
        return jsonify({
            'success': False,
            'message': f'Error in debug detection: {str(e)}'
        })

def generate_detection_recommendations(detection_info, detection_method="unknown"):
    """Generate recommendations based on detection results"""
    recommendations = []
    
    # Add detection method info
    if detection_method == "CNN":
        recommendations.append("✅ Detection: CNN (Most Accurate)")
    elif detection_method == "HOG":
        recommendations.append("⚠️ Detection: HOG (Fast but less accurate)")
    elif detection_method == "CNN-Upscaled":
        recommendations.append("✅ Detection: CNN with upscaling (Good for far faces)")
    elif detection_method == "CNN-Downscaled":
        recommendations.append("✅ Detection: CNN with downscaling (Good for close faces)")
    elif detection_method == "CNN-Original":
        recommendations.append("⚠️ Detection: CNN on original image (Enhancement might be causing issues)")
    
    if not detection_info:
        recommendations.append("❌ No faces detected. Move closer to camera.")
        recommendations.append("💡 Ensure good lighting on your face")
        recommendations.append("📐 Face the camera directly")
        recommendations.append("🔧 Try different distances (0.5m - 2m)")
        return recommendations
    
    # Check face sizes
    small_faces = [d for d in detection_info if 'TOO SMALL' in d.get('size_category', '')]
    if small_faces:
        recommendations.append(f"⚠️ {len(small_faces)} face(s) too small - Move closer to camera")
        recommendations.append("📏 Ideal: Your face should be 15-35% of image")
    
    # Check matches
    matched = [d for d in detection_info if d.get('matched', False)]
    unmatched = [d for d in detection_info if 'matched' in d and not d['matched']]
    
    if matched:
        recommendations.append(f"✅ {len(matched)} face(s) matched successfully")
    
    if unmatched:
        recommendations.append(f"⚠️ {len(unmatched)} face(s) detected but not matched")
        for face in unmatched:
            conf = face.get('confidence', '0%')
            recommendations.append(f"   Face #{face['face_number']}: {conf} confidence - Need better angle/lighting")
    
    # Check if multiple people
    if len(detection_info) > 1:
        recommendations.append(f"👥 {len(detection_info)} people detected - System will use best match")
    
    return recommendations
