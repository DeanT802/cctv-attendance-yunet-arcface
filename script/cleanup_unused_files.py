#!/usr/bin/env python3

import os
import shutil
import sys

# File-file yang aman untuk dihapus (tidak mengubah sistem yang berjalan)
files_to_delete = [
    # Test files
    "test_face_recognition_fix.py",
    "test_attendance_simulation.py", 
    "test_face_system_response.py",
    "test_auto_training.py",
    "test_basic_face_recognition.py",
    "test_class_validation.py",
    "test_collect_access.py",
    "test_complete_flow.py",
    "test_complete_preservation.py",
    "test_complete_system.py",
    "test_create_student.py",
    "test_current_state.py",
    "test_database.py",
    "test_database_methods.py",
    "test_dataset_collection.py",
    "test_db_params.py",
    "test_dependencies.py",
    "test_direct.py",
    "test_direct_insertion.py",
    "test_face_attendance.py",
    "test_face_recognition.py",
    "test_face_recognition_all.py",
    "test_face_recognition_import.py",
    "test_face_registration.py",
    "test_final_fix.py",
    "test_flask_startup.py",
    "test_interface_compatibility.py",
    "test_meetings.py",
    "test_meeting_creation.py",
    "test_meeting_system.py",
    "test_navigation.py",
    "test_new_attendance.py",
    "test_new_student_training.py",
    "test_print_data.py",
    "test_program_studies.py",
    "test_real_face_recognition.py",
    "test_recap_page.py",
    "test_recognize_face_fix.py",
    "test_return_format.py",
    "test_schedule_attendance_flow.py",
    "test_schedule_with_enrollment.py",
    "test_simple_face_recognition.py",
    "test_simple_recognition.py",
    "test_submit.py",
    "test_success_format.py",
    "test_time_format.py",
    "test_time_validation.py",
    "test_trained_system.py",
    "test_attendance.py",
    "test_attendance_fix.py",
    "test_admin_override_fix.py",
    "test_folder_preservation.py",
    
    # Debug files
    "debug_admin_override.py",
    "debug_face_recognition.py",
    "debug_flask_imports.py",
    "debug_meeting_id.py",
    "debug_presensi.py",
    "debug_register_form.py",
    "debug_schedule_14.py",
    "debug_session_create.py",
    "debug_students.py",
    "debug_student_error.py",
    
    # Cleanup and setup files (sudah tidak diperlukan)
    "cleanup_attendance.py",
    "cleanup_production.py", 
    "clean_and_test_attendance.py",
    "comprehensive_student_test.py",
    "create_attendance_table.py",
    "create_dataset_table.py",
    "create_meeting_1.py",
    "create_meeting_tables.py",
    "create_sample_dataset.py",
    "create_simple_solution.py",
    "detailed_attendance_check.py",
    "final_assessment.py",
    "final_face_recognition_test.py",
    "final_flow_test.py",
    "fix_enrollment.py",
    "fix_meeting_sessions.py",
    "insert_meeting_data.py",
    "insert_meeting_sessions.py",
    "install_face_recognition_deps.py",
    "install_face_recognition.bat",
    "manage_meetings.py",
    "real_data_test.py",
    "recreate_database.py",
    "reset_attendance_to_meeting_1.py",
    "retrain_face_model.py",
    "setup_fresh_database.py",
    "setup_meetings.py",
    "setup_meeting_system.py",
    "simple_flow_test.py",
    "train_face_recognition.py",
    "update_class_system.py",
    "update_database.py",
    "verify_data.py",
    "working_flow_test.py",
    "auto_enroll_students.py",
    "check_attendance_details.py",
    "check_face_modules.py",
    "check_tables.py",
    "check_table_structure.py",
    
    # Documentation files (sudah tidak relevan)
    "DATASET_COLLECTION_GUIDE.md",
    "ENROLLMENT_SOLUTION.md",
    "FACE_IMAGE_PRESERVATION_DOCS.md",
    "FACE_RECOGNITION_ATTENDANCE_FIX_COMPLETED.md",
    "FACE_RECOGNITION_DOCS.md",
    "FACE_RECOGNITION_FIX.md",
    "FACE_RECOGNITION_RESOLUTION.md",
    "FINAL_FLOW_ASSESSMENT_REPORT.md",
    "FORMAT_FIX_COMPLETED.md",
    "INTERFACE_FIX_SUMMARY.md",
    "PRODUCTION_CLEANUP_REPORT.md",
    "TESTING_REPORT_KOMPREHENSIF.md",
    "TRAINING_COMPLETED.md",
    "UPDATE_SUMMARY.md"
]

def main():
    base_path = r"c:\Users\MyBook Hype\OneDrive\Documents\WAHYU\PROJECT_TA\DEAD"
    
    print("🧹 Membersihkan file-file yang tidak diperlukan...")
    print(f"📁 Path: {base_path}")
    print()
    
    deleted_count = 0
    total_size_saved = 0
    
    for filename in files_to_delete:
        file_path = os.path.join(base_path, filename)
        
        if os.path.exists(file_path):
            try:
                # Get file size before deletion
                file_size = os.path.getsize(file_path)
                
                # Delete the file
                os.remove(file_path)
                
                print(f"✅ Deleted: {filename} ({file_size:,} bytes)")
                deleted_count += 1
                total_size_saved += file_size
                
            except Exception as e:
                print(f"❌ Failed to delete {filename}: {str(e)}")
        else:
            print(f"⚠️  File not found: {filename}")
    
    print()
    print(f"📊 Cleanup Summary:")
    print(f"   Files deleted: {deleted_count}")
    print(f"   Space saved: {total_size_saved:,} bytes ({total_size_saved / (1024*1024):.2f} MB)")
    print()
    
    # Verify system files are intact
    print("🔍 Verifying system files are intact...")
    
    critical_files = [
        "run.py",
        "requirements.txt", 
        "setup_database.py",
        "app/__init__.py",
        "app/routes.py",
        "app/database.py",
        "app/models.py"
    ]
    
    all_critical_intact = True
    for critical_file in critical_files:
        file_path = os.path.join(base_path, critical_file)
        if os.path.exists(file_path):
            print(f"✅ {critical_file} - OK")
        else:
            print(f"❌ {critical_file} - MISSING!")
            all_critical_intact = False
    
    print()
    if all_critical_intact:
        print("✅ All critical system files are intact!")
        print("🚀 System should continue working normally.")
    else:
        print("❌ Some critical files are missing! System may not work properly.")
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    if success:
        print("\n🎉 Cleanup completed successfully!")
    else:
        print("\n💥 Cleanup completed with warnings!")