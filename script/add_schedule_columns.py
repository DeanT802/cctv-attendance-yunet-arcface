"""
Script to add semester and academic_year columns to schedules table
"""
import sys
sys.path.insert(0, 'c:\\Users\\Admin\\Desktop\\Project\\FINAL_DEAD\\DEAD')

from app.database import Database

def add_schedule_columns():
    db = Database()
    if not db.connect():
        print("❌ Gagal terhubung ke database!")
        return False
    
    try:
        # Try to add semester column
        query1 = """
        ALTER TABLE schedules 
        ADD COLUMN semester VARCHAR(20) DEFAULT NULL AFTER room
        """
        print("Menambahkan kolom 'semester'...")
        try:
            db.execute_query(query1)
            print("✅ Kolom 'semester' berhasil ditambahkan")
        except Exception as e:
            if "Duplicate column name" in str(e):
                print("ℹ️ Kolom 'semester' sudah ada")
            else:
                print(f"⚠️ Error saat menambahkan kolom 'semester': {e}")
        
        # Try to add academic_year column
        query2 = """
        ALTER TABLE schedules 
        ADD COLUMN academic_year VARCHAR(20) DEFAULT NULL AFTER semester
        """
        print("\nMenambahkan kolom 'academic_year'...")
        try:
            db.execute_query(query2)
            print("✅ Kolom 'academic_year' berhasil ditambahkan")
        except Exception as e:
            if "Duplicate column name" in str(e):
                print("ℹ️ Kolom 'academic_year' sudah ada")
            else:
                print(f"⚠️ Error saat menambahkan kolom 'academic_year': {e}")
        
        # Show current structure
        print("\n📋 Struktur tabel schedules saat ini:")
        result = db.execute_query("DESCRIBE schedules")
        if result:
            for col in result:
                print(f"  - {col['Field']}: {col['Type']}")
        
        print("\n✅ Selesai!")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    finally:
        db.disconnect()

if __name__ == "__main__":
    add_schedule_columns()
