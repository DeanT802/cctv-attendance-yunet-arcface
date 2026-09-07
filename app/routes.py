from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify, Response, current_app
from app.database import Database
import bcrypt
import cv2
import numpy as np
import os
import time
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

main = Blueprint('main', __name__)

@main.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('main.dashboard'))
    return redirect(url_for('main.login'))

@main.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Simple authentication (you should implement proper user authentication)
        if username == 'admin' and password == 'password':
            session['user_id'] = 1
            session['username'] = username
            flash('Login berhasil!', 'success')
            return redirect(url_for('main.dashboard'))
        else:
            flash('Username atau password salah!', 'error')
    
    return render_template('login.html')

@main.route('/logout')
def logout():
    session.clear()
    flash('Logout berhasil!', 'success')
    return redirect(url_for('main.login'))

@main.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    
    db = Database()
    if not db.connect():
        flash('Gagal terhubung ke database!', 'error')
        return render_template('dashboard.html', error=True)
    
    try:
        # Get statistics
        student_count = db.get_student_count()
        course_count = db.get_course_count()
        teacher_count = db.get_teacher_count()
        
        # Get schedules
        schedules = db.get_schedules()
        
        # Get attendance statistics per class
        attendance_stats = db.get_attendance_summary_by_class()
        
        db.disconnect()
        
        return render_template('dashboard.html',
                             student_count=student_count,
                             course_count=course_count,
                             teacher_count=teacher_count,
                             schedules=schedules,
                             attendance_stats=attendance_stats)
    except Exception as e:
        db.disconnect()
        flash(f'Error: {str(e)}', 'error')
        return render_template('dashboard.html', error=True)

@main.route('/mahasiswa')
def mahasiswa():
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    
    db = Database()
    if not db.connect():
        flash('Gagal terhubung ke database!', 'error')
        return render_template('mahasiswa.html', students=[], error=True)
    
    try:
        students = db.get_all_students()
        db.disconnect()
        return render_template('mahasiswa.html', students=students)
    except Exception as e:
        db.disconnect()
        flash(f'Error: {str(e)}', 'error')
        return render_template('mahasiswa.html', students=[], error=True)

@main.route('/mahasiswa/tambah', methods=['GET', 'POST'])
def tambah_mahasiswa():
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    
    if request.method == 'POST':
        student_id = request.form['student_id']
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']
        class_year = request.form['class_year']
        program_study_id = request.form['program_study_id']
        department = request.form['department']
        semester = request.form['semester']
        class_number = request.form['class_number']
        class_name = request.form['class_name']

        try:
            class_number_int = int(class_number)
        except (TypeError, ValueError):
            flash('Nomor kelas tidak valid. Gunakan angka 1 sampai 7.', 'error')
            return render_template('tambah_mahasiswa.html')

        if class_number_int < 1 or class_number_int > 7:
            flash('Nomor kelas harus antara 1 sampai 7.', 'error')
            return render_template('tambah_mahasiswa.html')
        
        db = Database()
        if not db.connect():
            flash('Gagal terhubung ke database!', 'error')
            return render_template('tambah_mahasiswa.html')
        
        try:
            success = db.add_student(student_id, name, email, phone, class_year, program_study_id, department, semester, class_number, class_name, False)
            db.disconnect()
            
            if success:
                flash('Mahasiswa berhasil ditambahkan!', 'success')
                return redirect(url_for('main.mahasiswa'))
            else:
                flash('Gagal menambahkan mahasiswa!', 'error')
                
        except Exception as e:
            db.disconnect()
            flash(f'Error: {str(e)}', 'error')
    
    return render_template('tambah_mahasiswa.html')

@main.route('/jadwal')
def jadwal():
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    
    db = Database()
    if not db.connect():
        flash('Gagal terhubung ke database!', 'error')
        return render_template('jadwal.html', schedules=[], courses=[], teachers=[], error=True)
    
    try:
        schedules = db.get_all_schedules()
        courses = db.get_all_courses()
        teachers = db.get_all_teachers()
        
        # Get available classes from students
        available_classes_result = db.execute_query("SELECT DISTINCT class_name FROM students ORDER BY class_name")
        available_classes = [row['class_name'] for row in available_classes_result] if available_classes_result else []
        
        db.disconnect()
        return render_template('jadwal.html', 
                             schedules=schedules, 
                             courses=courses, 
                             teachers=teachers, 
                             available_classes=available_classes)
    except Exception as e:
        db.disconnect()
        flash(f'Error: {str(e)}', 'error')
        return render_template('jadwal.html', schedules=[], courses=[], teachers=[], available_classes=[], error=True)

@main.route('/jadwal/tambah', methods=['GET', 'POST'])
def tambah_jadwal():
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    
    db = Database()
    if not db.connect():
        flash('Gagal terhubung ke database!', 'error')
        return render_template('tambah_jadwal.html', courses=[], teachers=[], available_classes=[])
    
    try:
        courses = db.get_all_courses()
        teachers = db.get_all_teachers()
        
        # Get available classes from students
        available_classes_result = db.execute_query("SELECT DISTINCT class_name FROM students ORDER BY class_name")
        available_classes = [row['class_name'] for row in available_classes_result] if available_classes_result else []
        
        if request.method == 'POST':
            course_id = request.form['course_id']
            teacher_id = request.form['teacher_id']
            class_name = request.form['class_name']
            day = request.form['day']
            time_start = request.form['time_start']
            time_end = request.form['time_end']
            room = request.form['room']
            semester = request.form['semester']
            academic_year = request.form['academic_year']
            
            # Checkpoint settings (optional)
            checkpoint_enabled = request.form.get('checkpoint_enabled') == '1'
            checkpoint_interval = int(request.form.get('checkpoint_interval', 30))
            total_checkpoints = int(request.form.get('total_checkpoints', 4))
            
            success = db.add_schedule(
                course_id, teacher_id, class_name, day, time_start, time_end, room, 
                semester, academic_year, checkpoint_enabled, checkpoint_interval, total_checkpoints
            )
            db.disconnect()
            
            if success:
                checkpoint_msg = f' dengan {total_checkpoints} checkpoint setiap {checkpoint_interval} menit' if checkpoint_enabled else ''
                flash(f'Jadwal berhasil ditambahkan{checkpoint_msg}!', 'success')
                return redirect(url_for('main.jadwal'))
            else:
                flash('Gagal menambahkan jadwal!', 'error')
        else:
            db.disconnect()
            
    except Exception as e:
        db.disconnect()
        flash(f'Error: {str(e)}', 'error')
    
    return render_template('tambah_jadwal.html', courses=courses, teachers=teachers, available_classes=available_classes)

@main.route('/jadwal/hapus/<int:schedule_id>')
def hapus_jadwal(schedule_id):
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    
    db = Database()
    if not db.connect():
        flash('Gagal terhubung ke database!', 'error')
        return redirect(url_for('main.jadwal'))
    
    try:
        success = db.delete_schedule(schedule_id)
        db.disconnect()
        
        if success:
            flash('Jadwal berhasil dihapus!', 'success')
        else:
            flash('Gagal menghapus jadwal!', 'error')
            
    except Exception as e:
        db.disconnect()
        flash(f'Error: {str(e)}', 'error')
    
    return redirect(url_for('main.jadwal'))

@main.route('/mahasiswa/hapus/<int:student_id>')
def hapus_mahasiswa(student_id):
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    
    db = Database()
    if not db.connect():
        flash('Gagal terhubung ke database!', 'error')
        return redirect(url_for('main.mahasiswa'))
    
    try:
        # Get student details before deletion
        student = db.get_student_by_id(student_id)
        if not student:
            db.disconnect()
            flash('Data mahasiswa tidak ditemukan!', 'error')
            return redirect(url_for('main.mahasiswa'))
            
        nim = str(student.get('student_id', '')).strip()
        profile_photo = student.get('profile_photo')
        
        success = db.delete_student(student_id)
        db.disconnect()
        
        if success:
            import os
            import shutil
            import stat
            import gc
            
            # Release any latent file handles on Windows
            gc.collect()
            
            base_dir = current_app.config.get('BASE_DIR', os.path.abspath(os.path.join(current_app.root_path, '..')))
            
            # 1. Delete profile photo if exists (check multiple possible paths)
            if profile_photo:
                photo_candidates = [
                    profile_photo,
                    os.path.join(base_dir, profile_photo),
                    os.path.join(base_dir, 'uploads', profile_photo),
                    os.path.join(os.getcwd(), profile_photo)
                ]
                for p in photo_candidates:
                    if os.path.exists(p) and os.path.isfile(p):
                        try:
                            os.chmod(p, stat.S_IWRITE)
                            os.remove(p)
                        except Exception as e:
                            print(f"[Warning] Error removing profile photo {p}: {e}")
            
            # 2. Delete face images folder (resolve canonical paths across base_dir and CWD)
            if nim:
                def _handle_remove_readonly(func, path, exc_info):
                    try:
                        os.chmod(path, stat.S_IWRITE)
                        func(path)
                    except Exception:
                        pass

                potential_dirs = [
                    os.path.join(base_dir, 'uploads', 'faces', nim),
                    os.path.join(base_dir, 'uploads', nim),
                    os.path.join(os.getcwd(), 'uploads', 'faces', nim),
                    os.path.join(os.getcwd(), 'uploads', nim),
                    os.path.join(os.getcwd(), 'DEAD', 'uploads', 'faces', nim),
                    os.path.join(os.getcwd(), 'DEAD', 'uploads', nim),
                ]
                
                unique_dirs = []
                for d in potential_dirs:
                    norm = os.path.abspath(d)
                    if norm not in unique_dirs:
                        unique_dirs.append(norm)

                for target_dir in unique_dirs:
                    if os.path.exists(target_dir) and os.path.isdir(target_dir):
                        try:
                            shutil.rmtree(target_dir, onerror=_handle_remove_readonly)
                            print(f"[Success] Removed student directory: {target_dir}")
                        except Exception as e:
                            print(f"[Warning] rmtree failed for {target_dir}: {e}. Retrying file-by-file...")
                            try:
                                for root_f, dirs_f, files_f in os.walk(target_dir, topdown=False):
                                    for f in files_f:
                                        fp = os.path.join(root_f, f)
                                        try:
                                            os.chmod(fp, stat.S_IWRITE)
                                            os.remove(fp)
                                        except Exception:
                                            pass
                                    for sf in dirs_f:
                                        try:
                                            os.rmdir(os.path.join(root_f, sf))
                                        except Exception:
                                            pass
                                os.rmdir(target_dir)
                                print(f"[Success] Removed student directory via fallback: {target_dir}")
                            except Exception as e2:
                                print(f"[Error] Failed to remove directory {target_dir}: {e2}")
                        
                # 3. Remove from ArcFace embeddings
                try:
                    from app.face_recognition_routes import get_face_recognition_system
                    fr_system = get_face_recognition_system()
                    if fr_system:
                        fr_system.remove_student(str(nim))
                except Exception as e:
                    print(f"Error removing from face recognition system: {e}")

                # 4. Remove from legacy face_encodings.pkl and face_encodings_enhanced.pkl if present
                for enc_filename in ['face_encodings.pkl', 'face_encodings_enhanced.pkl']:
                    for p_model in [
                        os.path.join(base_dir, 'models', enc_filename),
                        os.path.join(os.getcwd(), 'models', enc_filename),
                        os.path.join(os.getcwd(), 'DEAD', 'models', enc_filename),
                    ]:
                        if os.path.exists(p_model):
                            try:
                                import pickle
                                with open(p_model, 'rb') as f:
                                    enc_data = pickle.load(f)
                                if isinstance(enc_data, dict) and 'names' in enc_data and 'encodings' in enc_data:
                                    names = enc_data['names']
                                    encs = enc_data['encodings']
                                    filtered_names = []
                                    filtered_encs = []
                                    changed = False
                                    for n, enc in zip(names, encs):
                                        if n.endswith(f'_{nim}') or n == str(nim):
                                            changed = True
                                        else:
                                            filtered_names.append(n)
                                            filtered_encs.append(enc)
                                    if changed:
                                        enc_data['names'] = filtered_names
                                        enc_data['encodings'] = filtered_encs
                                        with open(p_model, 'wb') as f:
                                            pickle.dump(enc_data, f)
                                        print(f"[Success] Removed {nim} from {p_model}")
                            except Exception as e:
                                print(f"Error cleaning legacy model {p_model}: {e}")
                    
            flash('Mahasiswa beserta seluruh data dan foto wajahnya berhasil dihapus!', 'success')
        else:
            flash('Gagal menghapus mahasiswa!', 'error')
            
    except Exception as e:
        db.disconnect()
        flash(f'Error: {str(e)}', 'error')
    
    return redirect(url_for('main.mahasiswa'))

@main.route('/api/attendance-chart')
def attendance_chart_api():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    db = Database()
    if not db.connect():
        return jsonify({'error': 'Database connection failed'}), 500
    
    try:
        attendance_stats = db.get_attendance_chart_data()
        db.disconnect()
        
        chart_data = {
            'labels': [stat['class_name'] for stat in attendance_stats],
            'data': [float(stat['attendance_percentage'] or 0) for stat in attendance_stats]
        }
        
        return jsonify(chart_data)
    except Exception as e:
        db.disconnect()
        return jsonify({'error': str(e)}), 500

@main.route('/presensi')
def presensi():
    """Halaman utama presensi"""
    db = Database()
    try:
        db.connect()
        
        # Get all schedules for selection
        schedules = db.get_all_schedules()
        
        # Add validation status to each schedule
        schedules_with_validation = []
        for schedule in schedules:
            is_valid, message, _ = db.validate_attendance_time(schedule['id'])
            schedule['validation_status'] = {
                'is_valid': is_valid,
                'message': message
            }
            schedules_with_validation.append(schedule)
        
        # Get attendance summary
        attendance_summary = db.get_attendance_summary_by_class()
        
        db.disconnect()
        return render_template('presensi.html', 
                             schedules=schedules_with_validation, 
                             attendance_summary=attendance_summary)
    except Exception as e:
        print(f"Error in presensi route: {e}")
        if db.connection:
            db.disconnect()
        return render_template('presensi.html', schedules=[], attendance_summary=[], error=True)

@main.route('/presensi/ambil/<int:schedule_id>')
def ambil_presensi(schedule_id):
    """Halaman untuk mengambil presensi berdasarkan jadwal"""
    from datetime import date
    
    # Check for admin override
    admin_override = request.args.get('override') == 'admin'
    
    db = Database()
    try:
        db.connect()
        
        # Validate attendance time first (unless admin override)
        if not admin_override:
            # Get current meeting first
            current_meeting = db.get_current_meeting(schedule_id)
            
            if not current_meeting:
                flash('Tidak ada pertemuan yang dijadwalkan untuk hari ini.', 'warning')
                return redirect(url_for('main.presensi'))
            
            # Validate meeting attendance time
            is_valid, message, meeting_info = db.validate_meeting_attendance_time(current_meeting['id'])
            
            if not is_valid:
                flash(f'{message}', 'warning')
                # Show option for admin override
                flash('Admin dapat menggunakan override dengan menambahkan ?override=admin pada URL', 'info')
                return redirect(url_for('main.presensi'))
        else:
            # Admin override - get meeting or create temp
            current_meeting = db.get_current_meeting(schedule_id)
            # Admin override - just get schedule info
            schedule = db.get_schedule_with_class_info(schedule_id)
            if not schedule:
                flash('Jadwal tidak ditemukan!', 'error')
                return redirect(url_for('main.presensi'))
            message = "Mode Admin Override - Validasi waktu diabaikan"
        
        # Get today's date
        today = date.today()
        
        # Get schedule info
        schedule = db.get_schedule_with_class_info(schedule_id)
        if not schedule:
            flash('Jadwal tidak ditemukan!', 'error')
            return redirect(url_for('main.presensi'))
        
        # Get current meeting for today
        if not admin_override:
            current_meeting = db.get_current_meeting(schedule_id)
        else:
            current_meeting = db.get_current_meeting(schedule_id)
        
        if not current_meeting and not admin_override:
            flash('Tidak ada pertemuan yang dijadwalkan untuk hari ini.', 'warning')
            return redirect(url_for('main.presensi'))
        
        # If no meeting for today but admin override, create a temp meeting structure
        if not current_meeting and admin_override:
            # For admin override, find or create a meeting
            from datetime import date
            today = date.today()
            
            # Check existing meetings for this schedule
            existing_meetings = db.get_meetings_by_schedule(schedule_id)
            
            if existing_meetings:
                # Use the last existing meeting for admin override
                last_meeting = existing_meetings[-1]
                current_meeting = {
                    'id': last_meeting['id'], 
                    'meeting_number': last_meeting['meeting_number'], 
                    'meeting_topic': f"Pertemuan {last_meeting['meeting_number']} (Admin Override)",
                    'meeting_date': last_meeting.get('meeting_date', today),
                    # Copy checkpoint settings from last meeting
                    'checkpoint_enabled': last_meeting.get('checkpoint_enabled', 0),
                    'checkpoint_interval': last_meeting.get('checkpoint_interval', 30),
                    'total_checkpoints': last_meeting.get('total_checkpoints', 1)
                }
                print(f"Admin override: Using existing meeting ID {last_meeting['id']}")
            else:
                # Create first meeting if none exist
                meeting_id = db.create_course_meeting(
                    schedule_id, 1, today, 
                    "Pertemuan 1 (Admin Override)"
                )
                if meeting_id:
                    # Fetch the newly created meeting with checkpoint settings
                    new_meeting = db.execute_query(
                        "SELECT * FROM course_meetings WHERE id = %s", (meeting_id,)
                    )
                    if new_meeting:
                        current_meeting = new_meeting[0]
                    else:
                        current_meeting = {
                            'id': meeting_id, 
                            'meeting_number': 1, 
                            'meeting_topic': 'Pertemuan 1 (Admin Override)',
                            'meeting_date': today
                        }
                    print(f"Admin override: Created new meeting ID {meeting_id}")
                else:
                    current_meeting = {'id': None, 'meeting_number': 0, 'meeting_topic': 'Admin Override Session'}
                    print("Admin override: Failed to create meeting, using None")
        
        # IMPORTANT: For admin override, always get checkpoint settings from schedule_settings
        # This ensures checkpoint is available even if meeting doesn't have it
        if admin_override and current_meeting:
            checkpoint_settings = db.get_schedule_checkpoint_settings(schedule_id)
            if checkpoint_settings.get('checkpoint_enabled'):
                current_meeting['checkpoint_enabled'] = checkpoint_settings['checkpoint_enabled']
                current_meeting['checkpoint_interval'] = checkpoint_settings['checkpoint_interval']
                current_meeting['total_checkpoints'] = checkpoint_settings['total_checkpoints']
                print(f"Admin override: Applied checkpoint settings from schedule: enabled={checkpoint_settings['checkpoint_enabled']}, interval={checkpoint_settings['checkpoint_interval']}, total={checkpoint_settings['total_checkpoints']}")
            
            # Get students enrolled in this schedule
            students = db.get_students_by_schedule(schedule_id)
            attendance_dict = {}
        else:
            # Get students enrolled in this schedule
            students = db.get_students_by_schedule(schedule_id)
            
            # Get existing attendance for this meeting
            if current_meeting:
                existing_attendance = db.get_meeting_attendance(current_meeting['id'])
                attendance_dict = {att['student_id']: att for att in existing_attendance}
            else:
                attendance_dict = {}
        
        # Final validation: ensure we have a valid meeting for admin override
        if admin_override and current_meeting and current_meeting.get('id') is None:
            flash('Tidak dapat membuat pertemuan untuk admin override. Silakan coba lagi.', 'error')
            db.disconnect()
            return redirect(url_for('main.presensi'))
        
        db.disconnect()
        return render_template('ambil_presensi.html',
                             schedule=schedule,
                             students=students,
                             attendance_dict=attendance_dict,
                             attendance_date=today,
                             validation_message=message,
                             admin_override=admin_override,
                             current_meeting=current_meeting)
    except Exception as e:
        print(f"Error in ambil_presensi route: {e}")
        if db.connection:
            db.disconnect()
        flash('Terjadi kesalahan dalam mengambil data!', 'error')
        return redirect(url_for('main.presensi'))

@main.route('/presensi/simpan', methods=['POST'])
def simpan_presensi():
    """Simpan data presensi"""
    from datetime import date
    
    # Check for admin override
    admin_override = request.form.get('admin_override') == 'true'
    
    db = Database()
    try:
        db.connect()
        
        schedule_id = request.form.get('schedule_id')
        attendance_date = request.form.get('attendance_date', date.today())
        meeting_id = request.form.get('meeting_id')  # New field for meeting ID
        
        if not schedule_id:
            flash('Data jadwal tidak valid!', 'error')
            return redirect(url_for('main.presensi'))
        
        # Get current meeting (for both normal and admin override)
        if not meeting_id:
            print(f"No meeting_id from form, searching for current meeting for schedule {schedule_id}")
        else:
            print(f"Meeting_id from form: {meeting_id}")
            
        if not meeting_id:
            print(f"No meeting_id from form, searching for current meeting for schedule {schedule_id}")
            current_meeting = db.get_current_meeting(schedule_id)
            if current_meeting:
                meeting_id = current_meeting['id']
                print(f"Found current meeting with ID: {meeting_id}")
            elif admin_override:
                print("Admin override mode - finding or creating meeting")
                # For admin override, create a temporary meeting for today if none exists
                from datetime import date
                today = date.today()
                
                # Check how many meetings already exist for this schedule
                existing_meetings = db.get_meetings_by_schedule(schedule_id)
                next_meeting_number = len(existing_meetings) + 1
                
                if next_meeting_number <= 16:
                    # Create a new meeting for today
                    meeting_id = db.create_course_meeting(
                        schedule_id, next_meeting_number, today, 
                        f"Pertemuan {next_meeting_number} (Admin Override)"
                    )
                    print(f"Admin override: Created new meeting with ID {meeting_id}")
                else:
                    # Use the last meeting if already at 16
                    meeting_id = existing_meetings[-1]['id'] if existing_meetings else None
                    print(f"Admin override: Using last meeting with ID {meeting_id}")
            
            if not meeting_id:
                flash('Tidak dapat membuat atau menemukan pertemuan untuk presensi!', 'error')
                return redirect(url_for('main.presensi'))
            
            # Additional safety check: ensure meeting_id exists in database
            meeting_exists = db.execute_query("SELECT id FROM course_meetings WHERE id = %s", (meeting_id,))
            if not meeting_exists:
                print(f"ERROR: meeting_id {meeting_id} does not exist in database!")
                flash(f'Meeting ID {meeting_id} tidak ditemukan dalam database!', 'error')
                return redirect(url_for('main.presensi'))
        
        # Validate attendance time before saving (unless admin override)
        if not admin_override and meeting_id:
            is_valid, message, meeting_info = db.validate_meeting_attendance_time(meeting_id)
            
            if not is_valid:
                flash(f'Presensi tidak dapat disimpan: {message}', 'error')
                return redirect(url_for('main.presensi'))
        
        # Get all students for this schedule
        students = db.get_students_by_schedule(schedule_id)
        
        success_count = 0
        error_count = 0
        
        for student in students:
            student_id = student['id']
            status = request.form.get(f'status_{student_id}')
            notes = request.form.get(f'notes_{student_id}', '').strip()
            
            if status:
                try:
                    # Always use meeting system (whether admin override or not)
                    success = db.mark_meeting_attendance(
                        student_id, meeting_id, status, 
                        notes if notes else None, 
                        'admin' if admin_override else None
                    )
                    if success:
                        success_count += 1
                    else:
                        error_count += 1
                except Exception as e:
                    print(f"Error marking attendance for student {student_id}: {e}")
                    error_count += 1
        
        db.disconnect()
        
        if success_count > 0:
            flash(f'Presensi berhasil disimpan untuk {success_count} mahasiswa!', 'success')
        if error_count > 0:
            flash(f'Gagal menyimpan presensi untuk {error_count} mahasiswa!', 'error')
        
        return redirect(url_for('main.ambil_presensi', schedule_id=schedule_id))
        
    except Exception as e:
        print(f"Error in simpan_presensi route: {e}")
        if db.connection:
            db.disconnect()
        flash('Terjadi kesalahan dalam menyimpan presensi!', 'error')
        return redirect(url_for('main.presensi'))

@main.route('/presensi/laporan')
def laporan_presensi():
    """Halaman laporan presensi"""
    db = Database()
    try:
        db.connect()
        
        # Get filter parameters
        class_name = request.args.get('class_name', '')
        start_date = request.args.get('start_date', '')
        end_date = request.args.get('end_date', '')
        
        # Get available classes for filter
        available_classes_result = db.execute_query("SELECT DISTINCT class_name FROM students ORDER BY class_name")
        available_classes = [row['class_name'] for row in available_classes_result] if available_classes_result else []
        
        # Get attendance summary with filters
        attendance_summary = db.get_attendance_summary_by_class(
            class_name if class_name else None,
            start_date if start_date else None,
            end_date if end_date else None
        )
        
        # Get checkpoint statistics
        checkpoint_stats = db.get_checkpoint_statistics(
            class_name if class_name else None,
            start_date if start_date else None,
            end_date if end_date else None
        )
        
        # Get detailed attendance with checkpoints
        attendance_details = db.get_attendance_details_with_checkpoints(
            class_name if class_name else None,
            start_date if start_date else None,
            end_date if end_date else None
        )
        
        db.disconnect()
        return render_template('laporan_presensi.html',
                             attendance_summary=attendance_summary,
                             checkpoint_stats=checkpoint_stats,
                             attendance_details=attendance_details,
                             available_classes=available_classes,
                             selected_class=class_name,
                             start_date=start_date,
                             end_date=end_date)
    except Exception as e:
        print(f"Error in laporan_presensi route: {e}")
        if db.connection:
            db.disconnect()
        return render_template('laporan_presensi.html', 
                             attendance_summary=[], 
                             available_classes=[], 
                             error=True)

@main.route('/presensi/rekapitulasi')
def rekapitulasi_presensi():
    """Halaman rekapitulasi presensi per mata kuliah per kelas"""
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    
    db = Database()
    if not db.connect():
        flash('Gagal terhubung ke database!', 'error')
        return render_template('rekapitulasi_presensi.html', schedules=[], error=True)
    
    try:
        # Get all schedules grouped by course and class
        schedules = db.get_all_schedules()
        db.disconnect()
        
        return render_template('rekapitulasi_presensi.html', schedules=schedules)
    except Exception as e:
        db.disconnect()
        flash(f'Error: {str(e)}', 'error')
        return render_template('rekapitulasi_presensi.html', schedules=[], error=True)

@main.route('/presensi/rekapitulasi/<int:schedule_id>')
def detail_rekapitulasi_presensi(schedule_id):
    """Halaman detail rekapitulasi presensi untuk mata kuliah tertentu"""
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    
    db = Database()
    if not db.connect():
        flash('Gagal terhubung ke database!', 'error')
        return render_template('detail_rekapitulasi_presensi.html', 
                             error=True, 
                             schedule_info=None, 
                             attendance_recap=[])
    
    try:
        # Get schedule info
        schedule_info = db.get_schedule_info(schedule_id)
        if not schedule_info:
            flash('Jadwal tidak ditemukan!', 'error')
            db.disconnect()
            return redirect(url_for('main.rekapitulasi_presensi'))
        
        # Get detailed attendance recap for this schedule
        attendance_recap = db.get_detailed_attendance_recap(schedule_id)
        
        db.disconnect()
        
        return render_template('detail_rekapitulasi_presensi.html', 
                             schedule_info=schedule_info,
                             attendance_recap=attendance_recap or [])
    except Exception as e:
        db.disconnect()
        flash(f'Error: {str(e)}', 'error')
        return render_template('detail_rekapitulasi_presensi.html', 
                             error=True,
                             schedule_info=None,
                             attendance_recap=[])

@main.route('/presensi/rekapitulasi/<int:schedule_id>/print')
def print_rekapitulasi_presensi(schedule_id):
    """Halaman cetak rekapitulasi presensi untuk mata kuliah tertentu"""
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    
    db = Database()
    if not db.connect():
        flash('Gagal terhubung ke database!', 'error')
        return render_template('print_rekapitulasi_presensi.html', 
                             error=True,
                             schedule_info=None,
                             attendance_recap=[],
                             current_date='')
    
    try:
        # Get schedule info
        schedule_info = db.get_schedule_info(schedule_id)
        if not schedule_info:
            flash('Jadwal tidak ditemukan!', 'error')
            db.disconnect()
            return redirect(url_for('main.rekapitulasi_presensi'))
        
        # Get detailed attendance recap for this schedule
        attendance_recap = db.get_detailed_attendance_recap(schedule_id)
        
        # Get current date for header
        from datetime import date
        current_date = date.today().strftime('%d %B %Y')
        
        db.disconnect()
        
        return render_template('print_rekapitulasi_presensi.html', 
                             schedule_info=schedule_info,
                             attendance_recap=attendance_recap or [],
                             current_date=current_date)
    except Exception as e:
        db.disconnect()
        flash(f'Error: {str(e)}', 'error')
        return render_template('print_rekapitulasi_presensi.html', 
                             error=True,
                             schedule_info=None,
                             attendance_recap=[],
                             current_date='')

@main.route('/test-print')
def test_print():
    """Test print template"""
    return render_template('test_print.html')

@main.route('/api/attendance/today')
def api_attendance_today():
    """API endpoint untuk mendapatkan riwayat presensi hari ini"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    try:
        db = Database()
        db.connect()
        
        # Get today's attendance
        query = """
        SELECT a.attendance_time, s.name as nama, s.student_id as nim,
               a.status, a.attendance_method, a.confidence_score
        FROM attendance a
        JOIN students s ON a.student_id = s.id
        WHERE DATE(a.attendance_time) = CURDATE()
        ORDER BY a.attendance_time DESC
        """
        
        attendance = db.execute_query(query)
        
        # Format the data
        formatted_attendance = []
        if attendance:
            for record in attendance:
                formatted_attendance.append({
                    'waktu': record['attendance_time'].strftime('%H:%M:%S') if record['attendance_time'] else 'N/A',
                    'nama': record['nama'],
                    'nim': record['nim'],
                    'status': record['status'],
                    'method': record['attendance_method'],
                    'confidence': record['confidence_score'] if record['confidence_score'] else 'N/A'
                })
        
        db.disconnect()
        
        return jsonify({
            'success': True,
            'attendance': formatted_attendance
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error loading attendance: {str(e)}'
        })

@main.route('/api/record_checkpoint', methods=['POST'])
def api_record_checkpoint():
    """API endpoint untuk mencatat checkpoint attendance"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['student_id', 'meeting_id', 'checkpoint_number']
        for field in required_fields:
            if field not in data:
                return jsonify({'success': False, 'error': f'Missing required field: {field}'}), 400
        
        student_id = data['student_id']  # NIM
        meeting_id = data['meeting_id']
        checkpoint_number = data['checkpoint_number']
        confidence = data.get('confidence', None)
        method = data.get('method', 'face_recognition')
        notes = data.get('notes', f'Checkpoint {checkpoint_number} - Auto-detected')
        
        print(f"[API Checkpoint] Recording checkpoint {checkpoint_number} for student {student_id} in meeting {meeting_id}")
        
        db = Database()
        if not db.connect():
            return jsonify({'success': False, 'error': 'Database connection failed'}), 500
        
        # Get student database ID from NIM
        student_query = "SELECT id FROM students WHERE student_id = %s"
        student_result = db.execute_query(student_query, (student_id,))
        
        if not student_result or len(student_result) == 0:
            db.disconnect()
            return jsonify({'success': False, 'error': f'Student not found: {student_id}'}), 404
        
        student_db_id = student_result[0]['id']
        
        # Record checkpoint using database method
        success = db.mark_checkpoint_attendance(
            student_db_id, 
            meeting_id, 
            checkpoint_number,
            method=method, 
            confidence=confidence,
            notes=notes
        )
        
        if success:
            # Get updated checkpoint status
            checkpoint_status = db.get_student_checkpoint_status(student_db_id, meeting_id)
            
            db.disconnect()
            
            return jsonify({
                'success': True,
                'message': f'Checkpoint {checkpoint_number} recorded successfully',
                'checkpoints_completed': checkpoint_status.get('checkpoints_completed', 0) if checkpoint_status else 0,
                'total_checkpoints': checkpoint_status.get('total_checkpoints', 1) if checkpoint_status else 1,
                'checkpoint_status': checkpoint_status.get('checkpoint_status', 'pending') if checkpoint_status else 'pending'
            })
        else:
            db.disconnect()
            return jsonify({'success': False, 'error': 'Failed to record checkpoint'}), 500
        
    except Exception as e:
        print(f"[API Checkpoint] Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': f'Error recording checkpoint: {str(e)}'
        }), 500

@main.route('/presensi_face')
def presensi_face():
    """Halaman presensi dengan face recognition"""
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    
    return render_template('presensi_face.html')


# IP Camera Support for Presensi Face with FRAME BUFFER ARCHITECTURE
# This solves the freeze issue by separating frame capture from frame consumption
ip_camera_stream_presensi = None
ip_camera_connection_count = 0  # Track active connections
import threading
stream_lock_presensi = threading.Lock()

# SHARED FRAME BUFFER: Stores the latest frame from camera
# Video stream and recognition read from this buffer, NOT directly from camera
latest_frame_presensi = None
frame_buffer_lock = threading.Lock()  # Protects buffer updates only
capture_thread_presensi = None
capture_thread_running = False

# ASYNC RECOGNITION ARCHITECTURE: Store recognition results
# Prevents CNN processing from blocking Flask worker threads
recognition_jobs = {}  # job_id -> {'status': 'processing/completed', 'result': {...}}
recognition_jobs_lock = threading.Lock()
job_counter = 0
active_recognition_jobs = 0  # Track concurrent jobs
MAX_CONCURRENT_JOBS = 2  # Limit concurrent recognition to prevent overload


def _parse_bool_env(var_name, default=False):
    """Parse boolean env vars safely."""
    value = os.getenv(var_name)
    if value is None:
        return default
    return str(value).strip().lower() in ('1', 'true', 'yes', 'on')


def _parse_float_env(var_name, default):
    """Parse float env vars safely with fallback."""
    value = os.getenv(var_name)
    if value is None or str(value).strip() == '':
        return default
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def _parse_int_env(var_name, default, min_value=None, max_value=None):
    """Parse integer env vars safely with optional clamping."""
    value = os.getenv(var_name)
    if value is None or str(value).strip() == '':
        result = default
    else:
        try:
            result = int(value)
        except (ValueError, TypeError):
            result = default

    if min_value is not None:
        result = max(min_value, result)
    if max_value is not None:
        result = min(max_value, result)
    return result


def _apply_face_roi_if_enabled(frame):
    """
    Apply optional ROI crop for distant-face optimization.
    ROI values are normalized [0..1] of full frame dimensions.

    Env vars:
      FACE_ROI_ENABLED=true|false
      FACE_ROI_X=0.20
      FACE_ROI_Y=0.15
      FACE_ROI_W=0.60
      FACE_ROI_H=0.70
    """
    if frame is None:
        return frame, None

    if not _parse_bool_env('FACE_ROI_ENABLED', False):
        return frame, None

    h, w = frame.shape[:2]

    x = _parse_float_env('FACE_ROI_X', 0.20)
    y = _parse_float_env('FACE_ROI_Y', 0.15)
    rw = _parse_float_env('FACE_ROI_W', 0.60)
    rh = _parse_float_env('FACE_ROI_H', 0.70)

    # Clamp normalized values
    x = max(0.0, min(x, 1.0))
    y = max(0.0, min(y, 1.0))
    rw = max(0.05, min(rw, 1.0))
    rh = max(0.05, min(rh, 1.0))

    # Convert to pixels and keep inside frame
    x1 = int(round(x * w))
    y1 = int(round(y * h))
    x2 = int(round(min(1.0, x + rw) * w))
    y2 = int(round(min(1.0, y + rh) * h))

    # Minimal ROI sanity
    if x2 <= x1 or y2 <= y1 or (x2 - x1) < 64 or (y2 - y1) < 64:
        print("[Capture Frame] ⚠️ FACE_ROI invalid/too small, using full frame")
        return frame, {
            'enabled': True,
            'applied': False,
            'reason': 'invalid_or_too_small'
        }

    roi_frame = frame[y1:y2, x1:x2].copy()
    print(f"[Capture Frame] 🎯 FACE_ROI applied: x={x1}:{x2}, y={y1}:{y2}, size={roi_frame.shape[1]}x{roi_frame.shape[0]}")

    return roi_frame, {
        'enabled': True,
        'applied': True,
        'x1': x1,
        'y1': y1,
        'x2': x2,
        'y2': y2,
        'width': int(roi_frame.shape[1]),
        'height': int(roi_frame.shape[0])
    }


def _prepare_frame_for_recognition(frame):
    """Apply ROI (if enabled) and resize for recognition pipeline."""
    if frame is None:
        return None, None

    frame, roi_info = _apply_face_roi_if_enabled(frame)

    target_width = _parse_int_env('RECOGNITION_FRAME_WIDTH', 480, min_value=320, max_value=1280)
    if frame.shape[1] > target_width:
        scale_factor = target_width / frame.shape[1]
        new_width = target_width
        new_height = int(frame.shape[0] * scale_factor)
        frame = cv2.resize(frame, (new_width, new_height), interpolation=cv2.INTER_AREA)

    return frame, roi_info


def _collect_ip_burst_frames(initial_frame):
    """
    Collect multiple frames from shared buffer for voting-based recognition.
    Returns (frames, burst_meta).
    """
    frames = [initial_frame]

    burst_enabled = _parse_bool_env('RECOGNITION_BURST_ENABLED', True)
    burst_count = _parse_int_env('RECOGNITION_BURST_FRAMES', 3, min_value=1, max_value=5)
    burst_interval_ms = _parse_int_env('RECOGNITION_BURST_INTERVAL_MS', 120, min_value=50, max_value=500)

    if not burst_enabled or burst_count <= 1:
        return frames, {
            'enabled': burst_enabled,
            'target_frames': 1,
            'captured_frames': 1,
            'interval_ms': burst_interval_ms
        }

    for _ in range(burst_count - 1):
        time.sleep(burst_interval_ms / 1000.0)
        with frame_buffer_lock:
            if latest_frame_presensi is None:
                continue
            next_frame = latest_frame_presensi.copy()

        next_frame, _ = _prepare_frame_for_recognition(next_frame)
        if next_frame is not None:
            frames.append(next_frame)

    return frames, {
        'enabled': True,
        'target_frames': burst_count,
        'captured_frames': len(frames),
        'interval_ms': burst_interval_ms
    }


def _analyze_lighting(frame):
    """Compute simple brightness/contrast metrics and classify lighting label."""
    if frame is None:
        return {
            'brightness': None,
            'contrast': None,
            'label': 'unknown'
        }

    try:
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        brightness = float(np.mean(gray))
        contrast = float(np.std(gray))

        # Simple label heuristic
        if brightness < 80 or contrast < 25:
            label = 'low'
        elif brightness > 180 and contrast < 35:
            label = 'low'
        elif brightness < 110:
            label = 'medium'
        else:
            label = 'good'

        return {
            'brightness': round(brightness, 2),
            'contrast': round(contrast, 2),
            'label': label
        }
    except Exception:
        return {
            'brightness': None,
            'contrast': None,
            'label': 'unknown'
        }


def _face_size_category(face_size_ratio):
    if face_size_ratio is None:
        return 'unknown'
    if face_size_ratio > 0.15:
        return 'near'
    if face_size_ratio > 0.08:
        return 'medium'
    return 'far'


def _log_runtime_result(result_data, metrics, source):
    """Append recognition runtime logs for later accuracy analysis."""
    try:
        log_dir = os.path.join('outputs', 'runtime_logs')
        os.makedirs(log_dir, exist_ok=True)
        log_path = os.path.join(log_dir, f"runtime_log_{datetime.now().strftime('%Y%m%d')}.csv")

        is_new = not os.path.exists(log_path)

        student = result_data.get('student') or {}
        row = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'source': source,
            'success': result_data.get('success', False),
            'student_id': student.get('student_id') or student.get('id') or '',
            'name': student.get('name') or student.get('nama') or '',
            'confidence': result_data.get('confidence'),
            'faces_detected': result_data.get('faces_detected'),
            'lighting_label': metrics.get('lighting', {}).get('label'),
            'brightness': metrics.get('lighting', {}).get('brightness'),
            'contrast': metrics.get('lighting', {}).get('contrast'),
            'face_size_ratio': metrics.get('face_size_ratio'),
            'distance_category': metrics.get('distance_category'),
            'message': result_data.get('message', '')
        }

        import csv
        with open(log_path, 'a', newline='', encoding='utf-8') as handle:
            writer = csv.DictWriter(handle, fieldnames=list(row.keys()))
            if is_new:
                writer.writeheader()
            writer.writerow(row)
    except Exception as e:
        print(f"[Runtime Log] ⚠️ Failed to log runtime data: {e}")

def start_frame_capture_thread(custom_rtsp_url=None):
    """Background thread that continuously captures frames to buffer"""
    global latest_frame_presensi, capture_thread_running, capture_thread_presensi
    
    rtsp_url = custom_rtsp_url or os.getenv('RTSP_URL', '')
    if not rtsp_url:
        print("[Frame Capture Thread] ERROR: No RTSP URL provided")
        return
        
    # Check if already running with the same URL
    if capture_thread_running:
        if getattr(start_frame_capture_thread, 'current_rtsp_url', None) == rtsp_url:
            print("[Frame Capture Thread] Already running with this URL, skipping...")
            return
        else:
            print("[Frame Capture Thread] URL changed, stopping existing thread...")
            capture_thread_running = False
            if capture_thread_presensi:
                capture_thread_presensi.join(timeout=2.0)
                
    start_frame_capture_thread.current_rtsp_url = rtsp_url
    
    def capture_loop():
        global latest_frame_presensi, capture_thread_running
        
        print("[Frame Capture Thread] Starting background capture...")
        
        # Create dedicated camera connection for background capture
        capture_camera = cv2.VideoCapture(rtsp_url, cv2.CAP_FFMPEG)
        capture_camera.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        capture_camera.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, 10000)
        capture_camera.set(cv2.CAP_PROP_READ_TIMEOUT_MSEC, 10000)
        
        if not capture_camera.isOpened():
            print("[Frame Capture Thread] ERROR: Failed to open camera")
            capture_thread_running = False
            return
        
        print("[Frame Capture Thread] ✅ Camera opened, starting capture loop...")
        capture_thread_running = True
        frame_count = 0
        error_count = 0
        max_errors = 10
        
        while capture_thread_running:
            try:
                ret, frame = capture_camera.read()
                
                if not ret or frame is None:
                    error_count += 1
                    if error_count >= max_errors:
                        print("[Frame Capture Thread] Too many errors, stopping")
                        break
                    continue
                
                # Reset error count on success
                error_count = 0
                frame_count += 1
                
                # Update shared buffer (FAST - just pointer update)
                with frame_buffer_lock:
                    latest_frame_presensi = frame.copy()
                
                # Log every 100 frames
                if frame_count % 100 == 0:
                    print(f"[Frame Capture Thread] Captured {frame_count} frames to buffer")
                
                # Small sleep to control frame rate (~30 FPS)
                import time
                time.sleep(0.033)
                
            except Exception as e:
                print(f"[Frame Capture Thread] Exception: {e}")
                error_count += 1
                if error_count >= max_errors:
                    break
        
        capture_camera.release()
        capture_thread_running = False
        print("[Frame Capture Thread] Stopped")
    
    # Start capture thread
    capture_thread_presensi = threading.Thread(target=capture_loop, daemon=True)
    capture_thread_presensi.start()
    print("[Frame Capture Thread] Background thread started")


def process_recognition_async(job_id, frame_input, meeting_id=None, source='ip_camera'):
    """
    Process face recognition in background thread (NON-BLOCKING!)
    This prevents CNN processing from freezing the video stream
    """
    global recognition_jobs, active_recognition_jobs
    
    # Increment active jobs counter
    with recognition_jobs_lock:
        active_recognition_jobs += 1
        current_active = active_recognition_jobs
    
    try:
        from app.face_recognition import CNNFaceRecognition
        
        print(f"[Async Recognition {job_id}] 🚀 Starting background processing... (active jobs: {current_active}/{MAX_CONCURRENT_JOBS})")
        
        # Resolve input frame (numpy array for IP camera, base64 for webcam compatibility)
        if isinstance(frame_input, np.ndarray):
            frame = frame_input
        elif isinstance(frame_input, str):
            import base64
            frame_bytes = base64.b64decode(frame_input)
            np_arr = np.frombuffer(frame_bytes, np.uint8)
            frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        else:
            frame = None
        
        if frame is None:
            with recognition_jobs_lock:
                recognition_jobs[job_id] = {
                    'status': 'completed',
                    'success': False,
                    'message': 'Failed to decode frame'
                }
            return
        
        # Get face recognition system
        face_system = CNNFaceRecognition()

        # Build frame list for voting (IP camera only)
        if source == 'ip_camera':
            frames_to_process, burst_meta = _collect_ip_burst_frames(frame)
        else:
            frames_to_process = [frame]
            burst_meta = {
                'enabled': False,
                'target_frames': 1,
                'captured_frames': 1,
                'interval_ms': 0
            }

        print(
            f"[Async Recognition {job_id}] 🔍 Running recognition on "
            f"{len(frames_to_process)} frame(s) (burst={burst_meta.get('enabled')})..."
        )

        successful_results = []
        failed_messages = []

        for idx, frame_item in enumerate(frames_to_process, start=1):
            result = face_system.recognize_face(frame_item, require_liveness=False)

            if result.get('success'):
                successful_results.append(result)
                student_name = result.get('student', {}).get('name', 'Unknown')
                confidence = result.get('confidence', 0)
                print(f"[Async Recognition {job_id}]   Frame #{idx}: ✅ {student_name} ({confidence:.2%})")
            else:
                msg = result.get('message', 'No face detected')
                failed_messages.append(msg)
                print(f"[Async Recognition {job_id}]   Frame #{idx}: ❌ {msg}")

        if not successful_results:
            fallback_msg = failed_messages[-1] if failed_messages else 'No face detected'
            with recognition_jobs_lock:
                recognition_jobs[job_id] = {
                    'status': 'completed',
                    'success': False,
                    'message': fallback_msg,
                    'burst': burst_meta
                }
            return

        # Voting by student_id, tie-break by highest confidence
        vote_table = {}
        for item in successful_results:
            student = item.get('student', {})
            student_id = student.get('student_id') or student.get('id') or 'unknown'
            confidence = float(item.get('confidence', 0) or 0)

            if student_id not in vote_table:
                vote_table[student_id] = {
                    'votes': 0,
                    'best_confidence': confidence,
                    'best_result': item
                }

            vote_table[student_id]['votes'] += 1
            if confidence > vote_table[student_id]['best_confidence']:
                vote_table[student_id]['best_confidence'] = confidence
                vote_table[student_id]['best_result'] = item

        winner = sorted(
            vote_table.values(),
            key=lambda x: (x['votes'], x['best_confidence']),
            reverse=True
        )[0]

        min_votes = _parse_int_env('RECOGNITION_MIN_VOTES', 1, min_value=1, max_value=5)
        if winner['votes'] < min_votes:
            with recognition_jobs_lock:
                recognition_jobs[job_id] = {
                    'status': 'completed',
                    'success': False,
                    'message': (
                        f"Recognition unstable ({winner['votes']} vote(s) < min {min_votes}). "
                        "Please hold steady and try again."
                    ),
                    'burst': burst_meta
                }
            return

        best_result = winner['best_result']

        # Recognition successful - prepare response
        response_data = {
            'status': 'completed',
            'success': True,
            'student': best_result.get('student', {}),
            'confidence': best_result.get('confidence', 0),
            'faces_detected': best_result.get('faces_detected', 1),
            'all_faces': best_result.get('all_faces', []),
            'multiple_faces': best_result.get('multiple_faces', False),
            'message': 'Face recognized successfully',
            'burst': {
                **burst_meta,
                'successful_frames': len(successful_results),
                'min_votes_required': min_votes,
                'winner_votes': winner['votes']
            }
        }
        
        # Store result
        with recognition_jobs_lock:
            recognition_jobs[job_id] = response_data
            
        print(f"[Async Recognition {job_id}] ✅ Result stored, job complete")
        
    except Exception as e:
        print(f"[Async Recognition {job_id}] ❌ Exception: {e}")
        import traceback
        traceback.print_exc()
        
        with recognition_jobs_lock:
            recognition_jobs[job_id] = {
                'status': 'completed',
                'success': False,
                'message': f'Error: {str(e)}'
            }
    
    finally:
        # CRITICAL: Always decrement active jobs counter
        with recognition_jobs_lock:
            active_recognition_jobs -= 1
            print(f"[Async Recognition {job_id}] 🔓 Job completed, active jobs now: {active_recognition_jobs}/{MAX_CONCURRENT_JOBS}")

def get_ip_camera_stream_presensi():
    """Get or create IP camera stream for presensi (THREAD-SAFE with singleton pattern)"""
    global ip_camera_stream_presensi, ip_camera_connection_count
    rtsp_url = os.getenv('RTSP_URL', '')
    
    if not rtsp_url:
        print("[IP Stream] ERROR: No RTSP URL configured")
        return None
    
    # Use lock to prevent multiple simultaneous connections
    with stream_lock_presensi:
        # Check if stream exists and is opened
        if ip_camera_stream_presensi is None or not ip_camera_stream_presensi.isOpened():
            try:
                ip_camera_connection_count += 1
                print(f"[IP Stream] Creating connection #{ip_camera_connection_count} to: {rtsp_url}")
                ip_camera_stream_presensi = cv2.VideoCapture(rtsp_url, cv2.CAP_FFMPEG)
                
                # Set properties for better connection and stability
                ip_camera_stream_presensi.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                ip_camera_stream_presensi.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, 10000)
                ip_camera_stream_presensi.set(cv2.CAP_PROP_READ_TIMEOUT_MSEC, 10000)
                
                # Force H.264 codec (more stable than H.265)
                ip_camera_stream_presensi.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'H264'))
                
                if not ip_camera_stream_presensi.isOpened():
                    print("[IP Stream] ERROR: Failed to open stream")
                    ip_camera_stream_presensi = None
                    return None
                else:
                    print("[IP Stream] ✅ SUCCESS: Stream opened and ready")
            except Exception as e:
                print(f"[IP Stream] EXCEPTION: {e}")
                import traceback
                traceback.print_exc()
                ip_camera_stream_presensi = None
                return None
        else:
            # Stream already exists and is open - reuse it (NO NEW CONNECTION!)
            print("[IP Stream] ♻️ REUSING existing connection")
    
    return ip_camera_stream_presensi


def generate_ip_camera_frames_presensi(custom_rtsp_url=None):
    """Generator function to stream IP camera frames for presensi - READS FROM BUFFER"""
    global latest_frame_presensi
    
    # Start capture thread if not running
    start_frame_capture_thread(custom_rtsp_url)
    
    # Wait for first frame to be available
    import time
    max_wait = 10  # seconds
    wait_count = 0
    while latest_frame_presensi is None and wait_count < max_wait:
        print(f"[IP Stream] Waiting for first frame... ({wait_count}s)")
        time.sleep(1)
        wait_count += 1
    
    if latest_frame_presensi is None:
        # Return error frame
        error_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        cv2.putText(error_frame, 'IP Camera Not Available', (50, 240),
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        _, buffer = cv2.imencode('.jpg', error_frame)
        frame = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
        return
    
    print("[IP Stream] ✅ Frame buffer ready, starting video stream...")
    frame_count = 0
    
    while True:
        try:
            # READ FROM BUFFER (NO LOCK CONTENTION - SUPER FAST!)
            # This is the KEY FIX: video stream never waits for camera.read()
            with frame_buffer_lock:
                if latest_frame_presensi is None:
                    continue
                frame = latest_frame_presensi.copy()
            
            frame_count += 1
            
            # FRAME SKIPPING: Skip every other frame to reduce load (30 FPS -> 15 FPS)
            if frame_count % 2 != 0:
                continue  # Skip odd frames for better performance
            
            # OPTIMIZED: Resize frame to reduce bandwidth (2K -> 640px for smooth display)
            # Smaller resolution = less lag, faster encoding, smaller payload
            target_width = 640  # Balanced size for display
            if frame.shape[1] > target_width:
                scale_factor = target_width / frame.shape[1]
                new_width = target_width
                new_height = int(frame.shape[0] * scale_factor)
                frame = cv2.resize(frame, (new_width, new_height), interpolation=cv2.INTER_AREA)
            
            # OPTIMIZED: Encode frame as JPEG with aggressive compression for speed
            encode_param = [cv2.IMWRITE_JPEG_QUALITY, 70]  # Optimized quality for display
            success_encode, buffer = cv2.imencode('.jpg', frame, encode_param)
            
            if not success_encode:
                print(f"[IP Stream] Failed to encode frame")
                continue
            
            frame_bytes = buffer.tobytes()
            
            # Log every 30 frames
            if frame_count % 30 == 0:
                print(f"[IP Stream] Streaming from buffer... frame {frame_count}, size: {len(frame_bytes)} bytes")
            
            # Yield frame in multipart format
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            
            # Small sleep to control frame rate
            time.sleep(0.033)  # ~30 FPS
                   
        except cv2.error as e:
            print(f"[IP Stream] OpenCV ERROR: {e}")
            import time
            time.sleep(0.2)
        except Exception as e:
            print(f"[IP Stream] EXCEPTION in stream generation: {e}")
            import time
            time.sleep(0.2)


@main.route('/presensi_face/ip_camera_feed')
def ip_camera_feed_presensi():
    """Video streaming route for IP camera in presensi face"""
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    rtsp_url = request.args.get('rtsp_url')
    return Response(generate_ip_camera_frames_presensi(rtsp_url),
                   mimetype='multipart/x-mixed-replace; boundary=frame')


@main.route('/presensi_face/check_ip_camera')
def check_ip_camera_presensi():
    """Check if IP camera is available for presensi"""
    try:
        rtsp_url = request.args.get('rtsp_url') or os.getenv('RTSP_URL', '')
        
        print(f"[IP Camera Check] Checking RTSP URL: {rtsp_url}")
        
        if not rtsp_url:
            print("[IP Camera Check] ERROR: RTSP_URL not configured in .env file")
            return jsonify({
                'available': False,
                'message': 'RTSP URL not configured in .env file'
            })
        
        # Fast socket probe before OpenCV to prevent thread blocking (max 0.8s)
        import re, socket
        match = re.search(r'@([^:/]+)(?::(\d+))?', rtsp_url)
        if not match:
            match = re.search(r'rtsp://([^:/]+)(?::(\d+))?', rtsp_url)
        
        if match:
            host = match.group(1)
            port = int(match.group(2)) if match.group(2) else 554
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(0.8)  # 800ms non-blocking check
                conn_res = sock.connect_ex((host, port))
                sock.close()
                if conn_res != 0:
                    print(f"[IP Camera Check] Socket {host}:{port} unreachable (error code: {conn_res})")
                    return jsonify({
                        'available': False,
                        'message': f'IP Camera ({host}:{port}) offline atau tidak terjangkau di jaringan ini.'
                    })
            except Exception as se:
                print(f"[IP Camera Check] Socket error: {se}")
                return jsonify({
                    'available': False,
                    'message': f'IP Camera host unreachable: {host}'
                })

        # Socket reached, now test OpenCV with short timeout
        print(f"[IP Camera Check] Socket reached! Testing video capture: {rtsp_url}")
        test_camera = cv2.VideoCapture(rtsp_url, cv2.CAP_FFMPEG)
        test_camera.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, 2000)  # 2s timeout
        test_camera.set(cv2.CAP_PROP_READ_TIMEOUT_MSEC, 2000)
        
        if test_camera.isOpened():
            ret, frame = test_camera.read()
            test_camera.release()
            
            if ret and frame is not None:
                print(f"[IP Camera Check] SUCCESS! Frame size: {frame.shape}")
                return jsonify({
                    'available': True,
                    'message': 'IP Camera connected successfully',
                    'url': rtsp_url.split('@')[-1] if '@' in rtsp_url else 'configured'
                })
            else:
                return jsonify({
                    'available': False,
                    'message': 'Connected but cannot read frames from camera.'
                })
        else:
            return jsonify({
                'available': False,
                'message': 'Cannot open camera stream from URL'
            })
            
    except Exception as e:
        print(f"[IP Camera Check] EXCEPTION: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'available': False,
            'message': f'Error checking IP camera: {str(e)}'
        })


@main.route('/presensi_face/capture_ip_frame', methods=['POST'])
def capture_ip_frame_presensi():
    """
    START async face recognition job (NON-BLOCKING!)
    Returns immediately with job_id, recognition runs in background
    """
    try:
        import base64
        global latest_frame_presensi, job_counter
        
        # Get meeting_id and rtsp_url from request
        meeting_id = None
        rtsp_url = None
        if request.is_json:
            data = request.get_json()
            meeting_id = data.get('meeting_id')
            rtsp_url = data.get('rtsp_url')
            print(f"[Capture Frame] 📋 Meeting ID: {meeting_id}")
            if rtsp_url:
                print(f"[Capture Frame] 📷 Custom RTSP URL provided")
        
        # Start capture thread if not running (or if URL changed)
        start_frame_capture_thread(rtsp_url)
        
        # READ FROM BUFFER (INSTANT - NO WAIT!)
        with frame_buffer_lock:
            if latest_frame_presensi is None:
                return jsonify({
                    'success': False,
                    'message': 'IP camera not available - no frame in buffer'
                })
            frame = latest_frame_presensi.copy()
        
        print("[Capture Frame] ✅ Got frame from buffer instantly")
        
        # Optional ROI + resize for recognition
        frame, roi_info = _prepare_frame_for_recognition(frame)
        if frame is None:
            return jsonify({
                'success': False,
                'message': 'Failed to prepare frame for recognition'
            })
        
        # CHECK: Limit concurrent jobs to prevent overload
        import time
        with recognition_jobs_lock:
            if active_recognition_jobs >= MAX_CONCURRENT_JOBS:
                print(f"[Capture Frame] ⚠️ Job limit reached ({active_recognition_jobs}/{MAX_CONCURRENT_JOBS}), skipping this frame")
                return jsonify({
                    'success': False,
                    'message': f'Too many concurrent jobs ({active_recognition_jobs}/{MAX_CONCURRENT_JOBS}), try again'
                })
            
            job_counter += 1
            job_id = f"job_{job_counter}_{int(time.time() * 1000)}"
            
            # Initialize job status
            recognition_jobs[job_id] = {
                'status': 'processing',
                'message': 'Recognition in progress...'
            }
        
        # START BACKGROUND THREAD FOR RECOGNITION (NON-BLOCKING!)
        # This is the KEY FIX: CNN processing doesn't block Flask worker
        recognition_thread = threading.Thread(
            target=process_recognition_async,
            args=(job_id, frame, meeting_id, 'ip_camera'),
            daemon=True
        )
        recognition_thread.start()
        
        print(f"[Capture Frame] 🚀 Started async job {job_id} (meeting_id: {meeting_id})")
        
        # RETURN IMMEDIATELY (Don't wait for recognition!)
        return jsonify({
            'success': True,
            'job_id': job_id,
            'message': 'Recognition started in background',
            'roi': roi_info
        })
        
    except cv2.error as e:
        print(f"[Capture Frame] OpenCV ERROR: {e}")
        return jsonify({
            'success': False,
            'message': f'OpenCV error: {str(e)}'
        })
    except Exception as e:
        print(f"[Capture Frame] EXCEPTION: {e}")
        return jsonify({
            'success': False,
            'message': f'Error capturing frame: {str(e)}'
        })


@main.route('/presensi_face/capture_webcam_frame', methods=['POST'])
def capture_webcam_frame():
    """
    Capture and process webcam frame for face recognition (for presensi page)
    Similar to capture_ip_frame_presensi but accepts frame from client
    """
    global active_recognition_jobs
    
    try:
        print("[Webcam Capture] ========== CAPTURE WEBCAM FRAME ==========")
        
        # Get meeting_id from request (if provided)
        meeting_id = None
        frame_base64 = None
        
        if request.is_json:
            data = request.get_json()
            meeting_id = data.get('meeting_id')
            frame_base64 = data.get('frame')
            print(f"[Webcam Capture] 📋 Meeting ID: {meeting_id}")
        
        if not frame_base64:
            return jsonify({
                'success': False,
                'message': 'No frame data provided'
            })
        
        # Check job limit
        if active_recognition_jobs >= MAX_CONCURRENT_JOBS:
            print(f"[Webcam Capture] ⚠️ Too many jobs! Current: {active_recognition_jobs}/{MAX_CONCURRENT_JOBS}")
            return jsonify({
                'success': False,
                'message': f'Too many recognition jobs running ({active_recognition_jobs}/{MAX_CONCURRENT_JOBS}). Please wait...'
            })
        
        # Validate base64 frame (decode to check if valid)
        try:
            import base64
            frame_data = base64.b64decode(frame_base64)
            nparr = np.frombuffer(frame_data, np.uint8)
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if frame is None:
                return jsonify({
                    'success': False,
                    'message': 'Invalid image data'
                })
            
            print(f"[Webcam Capture] ✅ Frame decoded: {frame.shape}")
            
        except Exception as e:
            print(f"[Webcam Capture] ❌ Frame decode error: {e}")
            return jsonify({
                'success': False,
                'message': f'Failed to decode frame: {str(e)}'
            })
        
        # Generate job ID
        job_id = f"webcam_{int(time.time() * 1000)}"
        
        # Initialize job status
        recognition_jobs[job_id] = {
            'status': 'processing',
            'message': 'Recognition in progress...'
        }
        
        # Start background thread for recognition
        recognition_thread = threading.Thread(
            target=process_recognition_async,
            args=(job_id, frame_base64, meeting_id, 'webcam'),
            daemon=True
        )
        recognition_thread.start()
        
        print(f"[Webcam Capture] 🚀 Started async job {job_id} (meeting_id: {meeting_id})")
        
        return jsonify({
            'success': True,
            'job_id': job_id,
            'message': 'Recognition started in background'
        })
        
    except Exception as e:
        print(f"[Webcam Capture] EXCEPTION: {e}")
        return jsonify({
            'success': False,
            'message': f'Error processing webcam frame: {str(e)}'
        })


@main.route('/presensi_face/get_recognition_result/<job_id>')
def get_recognition_result(job_id):
    """
    Poll for recognition result (NON-BLOCKING!)
    Frontend calls this to check if recognition is complete
    """
    try:
        with recognition_jobs_lock:
            if job_id not in recognition_jobs:
                return jsonify({
                    'success': False,
                    'message': 'Job not found'
                })
            
            job_data = recognition_jobs[job_id].copy()
        
        # If completed, clean up old job (keep jobs for 30 seconds)
        if job_data['status'] == 'completed':
            # Return result and remove from memory after client retrieves it
            # We'll keep it for one more request in case of network issues
            pass
        
        return jsonify(job_data)
        
    except Exception as e:
        print(f"[Get Result] Exception: {e}")
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        })




from app.camera_discovery import find_camera_url

@main.route('/api/connect_camera', methods=['POST'])
def api_connect_camera():
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 401
    
    data = request.json
    room_name = data.get('room_name')
    verification_code = data.get('verification_code')
    
    if not room_name:
        return jsonify({'status': 'error', 'message': 'Room name required'}), 400
        
    result = find_camera_url(room_name, provided_code=verification_code)
    return jsonify(result)


@main.route('/uploads/<path:filename>')
def uploaded_file(filename):
    """Serve uploaded face photos securely"""
    from flask import send_from_directory, current_app
    upload_dir = current_app.config.get('UPLOAD_FOLDER', os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads'))
    return send_from_directory(upload_dir, filename)


@main.route('/api/student_photo/<student_id>')
def api_student_photo(student_id):
    """Get sample photo for registered student"""
    from flask import send_from_directory, current_app, abort
    faces_dir = current_app.config.get('FACES_FOLDER', os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads', 'faces'))
    student_dir = os.path.join(faces_dir, student_id)
    if os.path.exists(student_dir):
        files = [f for f in os.listdir(student_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
        if files:
            return send_from_directory(student_dir, files[0])
    abort(404)

