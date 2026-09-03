"""
Script untuk menambahkan Dosen Harson Kapoh ke database
Jalankan: python add_lecturer_harson.py
"""

from app.database import Database

def add_harson_kapoh():
    db = Database()
    
    try:
        # Connect to database
        if not db.connect():
            print("❌ Gagal koneksi ke database!")
            return False
        
        print("✅ Koneksi database berhasil")
        
        # Data dosen Harson Kapoh
        name = "Harson Kapoh"
        email = "harson.kapoh@example.com"  # Ganti dengan email sebenarnya
        phone = "081234567890"  # Ganti dengan nomor telepon sebenarnya
        expertise = "Teknologi Informasi"  # Ganti dengan bidang keahlian sebenarnya
        
        # Check if teacher already exists
        check_query = "SELECT * FROM teachers WHERE name = %s"
        existing = db.execute_query(check_query, (name,))
        
        if existing:
            print(f"⚠️  Dosen '{name}' sudah ada di database!")
            print(f"   ID: {existing[0]['id']}")
            print(f"   Email: {existing[0]['email']}")
            print(f"   Phone: {existing[0]['phone']}")
            print(f"   Expertise: {existing[0]['expertise']}")
            return False
        
        # Add new teacher
        print(f"\n📝 Menambahkan dosen baru:")
        print(f"   Nama: {name}")
        print(f"   Email: {email}")
        print(f"   Phone: {phone}")
        print(f"   Expertise: {expertise}")
        
        result = db.add_teacher(name, email, phone, expertise)
        
        if result:
            print(f"\n✅ Berhasil menambahkan dosen '{name}'!")
            
            # Get the newly added teacher
            new_teacher = db.execute_query(check_query, (name,))
            if new_teacher:
                print(f"\n📋 Detail dosen yang ditambahkan:")
                print(f"   ID: {new_teacher[0]['id']}")
                print(f"   Nama: {new_teacher[0]['name']}")
                print(f"   Email: {new_teacher[0]['email']}")
                print(f"   Phone: {new_teacher[0]['phone']}")
                print(f"   Expertise: {new_teacher[0]['expertise']}")
            
            return True
        else:
            print(f"❌ Gagal menambahkan dosen '{name}'")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        db.disconnect()
        print("\n🔌 Koneksi database ditutup")


def list_all_teachers():
    """Menampilkan semua dosen yang ada di database"""
    db = Database()
    
    try:
        if not db.connect():
            print("❌ Gagal koneksi ke database!")
            return
        
        teachers = db.get_all_teachers()
        
        if not teachers:
            print("📭 Belum ada dosen di database")
            return
        
        print(f"\n👥 Daftar Dosen ({len(teachers)} orang):")
        print("=" * 80)
        for idx, teacher in enumerate(teachers, 1):
            print(f"\n{idx}. ID: {teacher['id']} | Teacher ID: {teacher.get('teacher_id', '-')}")
            print(f"   Nama: {teacher['name']}")
            print(f"   Email: {teacher.get('email', '-')}")
            print(f"   Phone: {teacher.get('phone', '-')}")
            print(f"   Department: {teacher.get('department', '-')}")
            print(f"   Title: {teacher.get('title', '-')}")
            print(f"   Specialization: {teacher.get('specialization', '-')}")
        print("=" * 80)
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        db.disconnect()


def add_custom_teacher():
    """Menambahkan dosen dengan input manual"""
    db = Database()
    
    try:
        if not db.connect():
            print("❌ Gagal koneksi ke database!")
            return False
        
        print("\n📝 MASUKKAN DATA DOSEN BARU:")
        print("-" * 80)
        
        # Get last teacher_id for auto-increment
        last_id_query = "SELECT teacher_id FROM teachers ORDER BY id DESC LIMIT 1"
        last_teacher = db.execute_query(last_id_query)
        if last_teacher and last_teacher[0]['teacher_id']:
            # Extract number from teacher_id (e.g., "T001" -> 1)
            try:
                last_num = int(last_teacher[0]['teacher_id'].replace('T', ''))
                next_num = last_num + 1
            except:
                next_num = 1
        else:
            next_num = 1
        
        teacher_id = f"T{next_num:03d}"  # Format: T001, T002, etc.
        print(f"Teacher ID (auto): {teacher_id}")
        
        name = input("Nama Lengkap (contoh: Harson Kapoh): ").strip()
        if not name:
            print("❌ Nama tidak boleh kosong!")
            return False
        
        email = input("Email (contoh: harson.kapoh@university.edu): ").strip()
        if not email:
            email = f"{name.lower().replace(' ', '.')}@university.edu"
            print(f"   (Auto-generate: {email})")
        
        phone = input("Nomor Telepon (contoh: 081234567890): ").strip()
        if not phone:
            phone = None
        
        department = input("Jurusan/Department (contoh: Teknik Informatika): ").strip()
        if not department:
            department = None
        
        title = input("Gelar (contoh: Dr., Prof.): ").strip()
        if not title:
            title = None
            
        specialization = input("Spesialisasi (contoh: Machine Learning, Web Dev): ").strip()
        if not specialization:
            specialization = None
        
        # Check if teacher already exists
        check_query = "SELECT * FROM teachers WHERE name = %s OR email = %s"
        existing = db.execute_query(check_query, (name, email))
        
        if existing:
            print(f"\n⚠️  Dosen dengan nama '{name}' atau email '{email}' sudah ada di database!")
            return False
        
        # Confirmation
        print("\n" + "=" * 80)
        print("📋 KONFIRMASI DATA DOSEN:")
        print("-" * 80)
        print(f"   Teacher ID: {teacher_id}")
        print(f"   Nama: {name}")
        print(f"   Email: {email}")
        print(f"   Phone: {phone or '-'}")
        print(f"   Department: {department or '-'}")
        print(f"   Title: {title or '-'}")
        print(f"   Specialization: {specialization or '-'}")
        print("=" * 80)
        
        confirm = input("\n❓ Tambahkan dosen ini? (y/n): ").lower().strip()
        
        if confirm != 'y' and confirm != 'yes':
            print("❌ Dibatalkan")
            return False
        
        # Add teacher with correct structure
        query = """
        INSERT INTO teachers (teacher_id, name, email, phone, department, title, specialization, is_active)
        VALUES (%s, %s, %s, %s, %s, %s, %s, 1)
        """
        params = (teacher_id, name, email, phone, department, title, specialization)
        result = db.execute_query(query, params)
        
        if result:
            print(f"\n✅ Berhasil menambahkan dosen '{name}'!")
            
            # Get the newly added teacher
            new_teacher = db.execute_query("SELECT * FROM teachers WHERE teacher_id = %s", (teacher_id,))
            if new_teacher:
                t = new_teacher[0]
                print(f"\n📋 Detail dosen yang ditambahkan:")
                print(f"   ID: {t['id']}")
                print(f"   Teacher ID: {t['teacher_id']}")
                print(f"   Nama: {t['name']}")
                print(f"   Email: {t['email']}")
                print(f"   Phone: {t.get('phone', '-')}")
                print(f"   Department: {t.get('department', '-')}")
                print(f"   Title: {t.get('title', '-')}")
                print(f"   Specialization: {t.get('specialization', '-')}")
            return True
        else:
            print(f"❌ Gagal menambahkan dosen '{name}'")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        db.disconnect()


if __name__ == "__main__":
    print("=" * 80)
    print("        MENAMBAHKAN DOSEN BARU")
    print("=" * 80)
    
    # Show existing teachers first
    print("\n📋 DOSEN YANG SUDAH ADA:")
    list_all_teachers()
    
    # Add new teacher
    print("\n" + "=" * 80)
    success = add_custom_teacher()
    
    if success:
        print("\n" + "=" * 80)
        print("        DOSEN SETELAH DITAMBAHKAN")
        print("=" * 80)
        list_all_teachers()
        
        print("\n✅ SELESAI! Dosen berhasil ditambahkan.")
        print("   Sekarang Anda bisa memilih dosen ini saat menambah jadwal.")
    else:
        print("\n⚠️  Proses dibatalkan atau gagal")
