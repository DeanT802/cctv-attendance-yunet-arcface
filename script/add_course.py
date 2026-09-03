"""
Script untuk menambahkan Mata Kuliah baru ke database
Jalankan: python add_course.py
"""

from app.database import Database

def list_all_courses():
    """Menampilkan semua mata kuliah yang ada di database"""
    db = Database()
    
    try:
        if not db.connect():
            print("❌ Gagal koneksi ke database!")
            return
        
        courses = db.get_all_courses()
        
        if not courses:
            print("📭 Belum ada mata kuliah di database")
            return
        
        print(f"\n📚 Daftar Mata Kuliah ({len(courses)} mata kuliah):")
        print("=" * 100)
        for idx, course in enumerate(courses, 1):
            print(f"\n{idx}. ID: {course['id']} | Kode: {course['course_code']}")
            print(f"   Nama: {course['name']}")
            print(f"   SKS: {course['credits']} | Semester: {course['semester']}")
            print(f"   Tipe: {course.get('course_type', '-')} | Total Pertemuan: {course.get('total_meetings', '-')}")
            print(f"   Durasi Sesi: {course.get('session_duration_minutes', '-')} menit | Sesi per Pertemuan: {course.get('sessions_per_meeting', '-')}")
            if course.get('description'):
                print(f"   Deskripsi: {course['description'][:80]}...")
        print("=" * 100)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.disconnect()


def add_custom_course():
    """Menambahkan mata kuliah dengan input manual"""
    db = Database()
    
    try:
        if not db.connect():
            print("❌ Gagal koneksi ke database!")
            return False
        
        print("\n📝 MASUKKAN DATA MATA KULIAH BARU:")
        print("-" * 100)
        
        # Get last course_code for auto-increment
        last_code_query = "SELECT course_code FROM courses ORDER BY id DESC LIMIT 1"
        last_course = db.execute_query(last_code_query)
        if last_course and last_course[0]['course_code']:
            # Extract number from course_code (e.g., "CS101" -> 101)
            try:
                last_code = last_course[0]['course_code']
                # Try to extract number from end
                num_part = ''.join(filter(str.isdigit, last_code))
                if num_part:
                    next_num = int(num_part) + 1
                else:
                    next_num = 101
            except:
                next_num = 101
        else:
            next_num = 101
        
        # Input kode mata kuliah
        default_code = f"MK{next_num}"
        course_code_input = input(f"Kode Mata Kuliah (tekan Enter untuk '{default_code}'): ").strip().upper()
        course_code = course_code_input if course_code_input else default_code
        
        name = input("Nama Mata Kuliah (contoh: Pemrograman Web): ").strip()
        if not name:
            print("❌ Nama mata kuliah tidak boleh kosong!")
            return False
        
        credits_input = input("Jumlah SKS (default: 3): ").strip()
        credits = int(credits_input) if credits_input else 3
        
        semester_input = input("Semester (1-8, default: 1): ").strip()
        semester = int(semester_input) if semester_input else 1
        
        print("\nTipe Mata Kuliah:")
        print("  1. Theory (Teori)")
        print("  2. Practical (Praktikum)")
        print("  3. Mixed (Campuran)")
        course_type_input = input("Pilih tipe (1-3, default: 1): ").strip()
        course_type_map = {'1': 'theory', '2': 'practical', '3': 'mixed'}
        course_type = course_type_map.get(course_type_input, 'theory')
        
        total_meetings_input = input("Total Pertemuan (default: 16): ").strip()
        total_meetings = int(total_meetings_input) if total_meetings_input else 16
        
        session_duration_input = input("Durasi per Sesi (menit, default: 50): ").strip()
        session_duration_minutes = int(session_duration_input) if session_duration_input else 50
        
        sessions_per_meeting_input = input("Jumlah Sesi per Pertemuan (default: 2): ").strip()
        sessions_per_meeting = int(sessions_per_meeting_input) if sessions_per_meeting_input else 2
        
        description = input("Deskripsi (opsional): ").strip()
        if not description:
            description = None
        
        print("\nSistem Penilaian:")
        print("  1. Letter (A, B, C, D, E)")
        print("  2. Numeric (0-100)")
        print("  3. Pass/Fail (Lulus/Tidak Lulus)")
        grading_input = input("Pilih sistem (1-3, default: 1): ").strip()
        grading_map = {'1': 'letter', '2': 'numeric', '3': 'pass_fail'}
        grading_system = grading_map.get(grading_input, 'letter')
        
        # Check if course already exists
        check_query = "SELECT * FROM courses WHERE course_code = %s OR name = %s"
        existing = db.execute_query(check_query, (course_code, name))
        
        if existing:
            print(f"\n⚠️  Mata kuliah dengan kode '{course_code}' atau nama '{name}' sudah ada di database!")
            return False
        
        # Confirmation
        print("\n" + "=" * 100)
        print("📋 KONFIRMASI DATA MATA KULIAH:")
        print("-" * 100)
        print(f"   Kode: {course_code}")
        print(f"   Nama: {name}")
        print(f"   SKS: {credits}")
        print(f"   Semester: {semester}")
        print(f"   Tipe: {course_type}")
        print(f"   Total Pertemuan: {total_meetings}")
        print(f"   Durasi Sesi: {session_duration_minutes} menit")
        print(f"   Sesi per Pertemuan: {sessions_per_meeting}")
        print(f"   Total Durasi per Pertemuan: {session_duration_minutes * sessions_per_meeting} menit")
        print(f"   Sistem Penilaian: {grading_system}")
        if description:
            print(f"   Deskripsi: {description}")
        print("=" * 100)
        
        confirm = input("\n❓ Tambahkan mata kuliah ini? (y/n): ").lower().strip()
        
        if confirm != 'y' and confirm != 'yes':
            print("❌ Dibatalkan")
            return False
        
        # Add course with correct structure
        query = """
        INSERT INTO courses (
            course_code, name, credits, semester, description,
            total_meetings, session_duration_minutes, sessions_per_meeting,
            course_type, grading_system, is_active
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 1)
        """
        params = (
            course_code, name, credits, semester, description,
            total_meetings, session_duration_minutes, sessions_per_meeting,
            course_type, grading_system
        )
        result = db.execute_query(query, params)
        
        if result:
            print(f"\n✅ Berhasil menambahkan mata kuliah '{name}'!")
            
            # Get the newly added course
            new_course = db.execute_query("SELECT * FROM courses WHERE course_code = %s", (course_code,))
            if new_course:
                c = new_course[0]
                print(f"\n📋 Detail mata kuliah yang ditambahkan:")
                print(f"   ID: {c['id']}")
                print(f"   Kode: {c['course_code']}")
                print(f"   Nama: {c['name']}")
                print(f"   SKS: {c['credits']}")
                print(f"   Semester: {c['semester']}")
                print(f"   Tipe: {c['course_type']}")
                print(f"   Total Pertemuan: {c['total_meetings']}")
                print(f"   Durasi Sesi: {c['session_duration_minutes']} menit")
                print(f"   Sesi per Pertemuan: {c['sessions_per_meeting']}")
                print(f"   Sistem Penilaian: {c['grading_system']}")
            return True
        else:
            print(f"❌ Gagal menambahkan mata kuliah '{name}'")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        db.disconnect()


if __name__ == "__main__":
    print("=" * 100)
    print("        MENAMBAHKAN MATA KULIAH BARU")
    print("=" * 100)
    
    # Show existing courses first
    print("\n📋 MATA KULIAH YANG SUDAH ADA:")
    list_all_courses()
    
    # Add new course
    print("\n" + "=" * 100)
    success = add_custom_course()
    
    if success:
        print("\n" + "=" * 100)
        print("        MATA KULIAH SETELAH DITAMBAHKAN")
        print("=" * 100)
        list_all_courses()
        
        print("\n✅ SELESAI! Mata kuliah berhasil ditambahkan.")
        print("   Sekarang Anda bisa memilih mata kuliah ini saat menambah jadwal.")
    else:
        print("\n⚠️  Proses dibatalkan atau gagal")
