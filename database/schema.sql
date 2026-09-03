-- =============================================================================
-- DATABASE SCHEMA: student_attendance
-- Sistem Presensi Mahasiswa Berbasis Face Recognition
-- Smart Class - Jurusan Teknik Elektro, Politeknik Negeri Manado
-- =============================================================================
-- Version: 3.0 (Clean Schema + Multiple Check-in)
-- Compatibility: MySQL 8.0+ / MariaDB 10.4+
-- =============================================================================

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+08:00";

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

-- -------------------------------------------------
-- Database
-- -------------------------------------------------
CREATE DATABASE IF NOT EXISTS `student_attendance`
  DEFAULT CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE `student_attendance`;

-- =============================================================================
-- 1. REFERENCE / LOOKUP TABLES (no foreign-key dependencies)
-- =============================================================================

-- -------------------------------------------------
-- 1a. Program Studi
-- -------------------------------------------------
CREATE TABLE `program_studies` (
  `id` INT(11) NOT NULL AUTO_INCREMENT,
  `name` VARCHAR(100) NOT NULL,
  `abbreviation` VARCHAR(10) NOT NULL,
  `department` VARCHAR(100) DEFAULT NULL,
  `is_active` TINYINT(1) DEFAULT 1,
  `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `abbreviation` (`abbreviation`),
  KEY `idx_department` (`department`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- -------------------------------------------------
-- 1b. Users (authentication)
-- -------------------------------------------------
CREATE TABLE `users` (
  `id` INT(11) NOT NULL AUTO_INCREMENT,
  `username` VARCHAR(50) NOT NULL,
  `email` VARCHAR(100) NOT NULL,
  `password_hash` VARCHAR(255) NOT NULL,
  `role` ENUM('admin','teacher','student','staff') NOT NULL,
  `is_active` TINYINT(1) DEFAULT 1,
  `last_login` TIMESTAMP NULL DEFAULT NULL,
  `login_attempts` INT(11) DEFAULT 0,
  `locked_until` TIMESTAMP NULL DEFAULT NULL,
  `password_reset_token` VARCHAR(255) DEFAULT NULL,
  `password_reset_expires` TIMESTAMP NULL DEFAULT NULL,
  `email_verified` TINYINT(1) DEFAULT 0,
  `email_verification_token` VARCHAR(255) DEFAULT NULL,
  `two_factor_enabled` TINYINT(1) DEFAULT 0,
  `two_factor_secret` VARCHAR(32) DEFAULT NULL,
  `profile_completed` TINYINT(1) DEFAULT 0,
  `preferences` JSON DEFAULT NULL,
  `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `username` (`username`),
  UNIQUE KEY `email` (`email`),
  KEY `idx_role` (`role`),
  KEY `idx_active` (`is_active`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- -------------------------------------------------
-- 1c. Courses
-- -------------------------------------------------
CREATE TABLE `courses` (
  `id` INT(11) NOT NULL AUTO_INCREMENT,
  `course_code` VARCHAR(20) NOT NULL,
  `name` VARCHAR(100) NOT NULL,
  `credits` INT(11) NOT NULL DEFAULT 3,
  `semester` INT(11) NOT NULL,
  `description` TEXT DEFAULT NULL,
  `total_meetings` INT(11) NOT NULL DEFAULT 16,
  `session_duration_minutes` INT(11) NOT NULL DEFAULT 5,
  `sessions_per_meeting` INT(11) NOT NULL DEFAULT 4,
  `prerequisite_course_id` INT(11) DEFAULT NULL,
  `is_active` TINYINT(1) DEFAULT 1,
  `course_type` ENUM('theory','practical','mixed') DEFAULT 'theory',
  `grading_system` ENUM('letter','numeric','pass_fail') DEFAULT 'letter',
  `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `course_code` (`course_code`),
  KEY `idx_semester` (`semester`),
  KEY `idx_active` (`is_active`),
  CONSTRAINT `courses_ibfk_1` FOREIGN KEY (`prerequisite_course_id`) REFERENCES `courses` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- -------------------------------------------------
-- 1d. Teachers
-- -------------------------------------------------
CREATE TABLE `teachers` (
  `id` INT(11) NOT NULL AUTO_INCREMENT,
  `teacher_id` VARCHAR(20) NOT NULL,
  `name` VARCHAR(100) NOT NULL,
  `email` VARCHAR(100) DEFAULT NULL,
  `phone` VARCHAR(20) DEFAULT NULL,
  `department` VARCHAR(100) DEFAULT NULL,
  `title` VARCHAR(50) DEFAULT NULL,
  `specialization` TEXT DEFAULT NULL,
  `is_active` TINYINT(1) DEFAULT 1,
  `hire_date` DATE DEFAULT NULL,
  `profile_photo` VARCHAR(255) DEFAULT NULL,
  `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `teacher_id` (`teacher_id`),
  UNIQUE KEY `email` (`email`),
  KEY `idx_department` (`department`),
  KEY `idx_active` (`is_active`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =============================================================================
-- 2. CORE ENTITY TABLES
-- =============================================================================

-- -------------------------------------------------
-- 2a. Students
-- -------------------------------------------------
CREATE TABLE `students` (
  `id` INT(11) NOT NULL AUTO_INCREMENT,
  `student_id` VARCHAR(20) NOT NULL,
  `name` VARCHAR(100) NOT NULL,
  `email` VARCHAR(100) DEFAULT NULL,
  `phone` VARCHAR(20) DEFAULT NULL,
  `class_year` YEAR DEFAULT NULL,
  `program_study_id` INT(11) DEFAULT NULL,
  `department` VARCHAR(100) DEFAULT NULL,
  `semester` INT(11) DEFAULT NULL,
  `class_number` INT(11) DEFAULT 1,
  `class_name` VARCHAR(10) DEFAULT NULL,
  `face_encoding` LONGBLOB DEFAULT NULL,
  `face_registered` TINYINT(1) DEFAULT 0,
  `face_registration_date` TIMESTAMP NULL DEFAULT NULL,
  `profile_photo` VARCHAR(255) DEFAULT NULL,
  `is_active` TINYINT(1) DEFAULT 1,
  `graduation_date` DATE DEFAULT NULL,
  `gpa` DECIMAL(3,2) DEFAULT NULL,
  `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `student_id` (`student_id`),
  UNIQUE KEY `email` (`email`),
  KEY `idx_class_name` (`class_name`),
  KEY `idx_program_study` (`program_study_id`),
  KEY `idx_active` (`is_active`),
  CONSTRAINT `students_ibfk_1` FOREIGN KEY (`program_study_id`) REFERENCES `program_studies` (`id`) ON DELETE SET NULL,
  CONSTRAINT `chk_students_class_number` CHECK (`class_number` >= 1 AND `class_number` <= 7)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- -------------------------------------------------
-- 2b. Schedules
-- -------------------------------------------------
CREATE TABLE `schedules` (
  `id` INT(11) NOT NULL AUTO_INCREMENT,
  `course_id` INT(11) NOT NULL,
  `teacher_id` INT(11) NOT NULL,
  `class_name` VARCHAR(50) NOT NULL,
  `day` ENUM('Senin','Selasa','Rabu','Kamis','Jumat','Sabtu','Minggu') NOT NULL,
  `time_start` TIME NOT NULL,
  `time_end` TIME NOT NULL,
  `room` VARCHAR(50) DEFAULT NULL,
  `semester` INT(11) NOT NULL,
  `academic_year` VARCHAR(10) NOT NULL,
  `max_capacity` INT(11) DEFAULT 30,
  `is_active` TINYINT(1) DEFAULT 1,
  `schedule_type` ENUM('regular','makeup','exam') DEFAULT 'regular',
  `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_class_name` (`class_name`),
  KEY `idx_day_time` (`day`,`time_start`),
  KEY `idx_academic_year` (`academic_year`),
  KEY `idx_active` (`is_active`),
  CONSTRAINT `schedules_ibfk_1` FOREIGN KEY (`course_id`) REFERENCES `courses` (`id`) ON DELETE CASCADE,
  CONSTRAINT `schedules_ibfk_2` FOREIGN KEY (`teacher_id`) REFERENCES `teachers` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- -------------------------------------------------
-- 2c. Schedule Settings (Multiple Check-in config per schedule)
-- -------------------------------------------------
CREATE TABLE `schedule_settings` (
  `id` INT(11) NOT NULL AUTO_INCREMENT,
  `schedule_id` INT(11) NOT NULL,
  `setting_key` VARCHAR(100) NOT NULL,
  `setting_value` TEXT DEFAULT NULL,
  `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `unique_setting` (`schedule_id`,`setting_key`),
  KEY `idx_setting_key` (`setting_key`),
  CONSTRAINT `schedule_settings_ibfk_1` FOREIGN KEY (`schedule_id`) REFERENCES `schedules` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- -------------------------------------------------
-- 2d. Class Enrollments
-- -------------------------------------------------
CREATE TABLE `class_enrollments` (
  `id` INT(11) NOT NULL AUTO_INCREMENT,
  `student_id` INT(11) NOT NULL,
  `schedule_id` INT(11) NOT NULL,
  `enrolled_date` DATE DEFAULT (CURRENT_DATE),
  `status` ENUM('active','dropped','completed','suspended') DEFAULT 'active',
  `final_grade` VARCHAR(5) DEFAULT NULL,
  `grade_points` DECIMAL(3,2) DEFAULT NULL,
  `attendance_percentage` DECIMAL(5,2) DEFAULT NULL,
  `dropped_date` DATE DEFAULT NULL,
  `completion_date` DATE DEFAULT NULL,
  `notes` TEXT DEFAULT NULL,
  `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `unique_enrollment` (`student_id`,`schedule_id`),
  KEY `idx_status` (`status`),
  KEY `idx_enrolled_date` (`enrolled_date`),
  KEY `idx_enrollments_schedule_status` (`schedule_id`,`status`,`enrolled_date`),
  CONSTRAINT `class_enrollments_ibfk_1` FOREIGN KEY (`student_id`) REFERENCES `students` (`id`) ON DELETE CASCADE,
  CONSTRAINT `class_enrollments_ibfk_2` FOREIGN KEY (`schedule_id`) REFERENCES `schedules` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =============================================================================
-- 3. ATTENDANCE / MEETING TABLES
-- =============================================================================

-- -------------------------------------------------
-- 3a. Course Meetings (includes multiple check-in fields)
-- -------------------------------------------------
CREATE TABLE `course_meetings` (
  `id` INT(11) NOT NULL AUTO_INCREMENT,
  `schedule_id` INT(11) NOT NULL,
  `meeting_number` INT(11) NOT NULL,
  `meeting_date` DATE NOT NULL,
  `meeting_topic` VARCHAR(200) DEFAULT NULL,
  `status` ENUM('scheduled','ongoing','completed','cancelled') DEFAULT 'scheduled',
  `started_at` DATETIME DEFAULT NULL,
  `ended_at` DATETIME DEFAULT NULL,
  `attendance_open` TINYINT(1) DEFAULT 0,
  `attendance_closed` TINYINT(1) DEFAULT 0,
  `late_threshold_minutes` INT(11) DEFAULT 15,
  `checkpoint_interval` INT(11) DEFAULT 30 COMMENT 'Minutes between checkpoints',
  `total_checkpoints` INT(11) DEFAULT 1 COMMENT 'Number of checkpoints (1-4)',
  `checkpoint_enabled` TINYINT(1) DEFAULT 0 COMMENT 'Multiple check-in enabled',
  `notes` TEXT DEFAULT NULL,
  `created_by` INT(11) DEFAULT NULL,
  `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `unique_meeting` (`schedule_id`,`meeting_number`),
  UNIQUE KEY `unique_meeting_date` (`schedule_id`,`meeting_date`),
  KEY `idx_meeting_date` (`meeting_date`),
  KEY `idx_status` (`status`),
  KEY `idx_meetings_schedule_date` (`schedule_id`,`meeting_date`,`status`),
  KEY `idx_meeting_checkpoints` (`checkpoint_enabled`,`checkpoint_interval`),
  CONSTRAINT `course_meetings_ibfk_1` FOREIGN KEY (`schedule_id`) REFERENCES `schedules` (`id`) ON DELETE CASCADE,
  CONSTRAINT `course_meetings_ibfk_2` FOREIGN KEY (`created_by`) REFERENCES `teachers` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- -------------------------------------------------
-- 3b. Meeting Sessions
-- -------------------------------------------------
CREATE TABLE `meeting_sessions` (
  `id` INT(11) NOT NULL AUTO_INCREMENT,
  `meeting_id` INT(11) NOT NULL,
  `session_number` INT(11) NOT NULL,
  `session_start_time` TIME NOT NULL,
  `session_end_time` TIME NOT NULL,
  `status` ENUM('scheduled','active','completed','skipped') DEFAULT 'scheduled',
  `attendance_count` INT(11) DEFAULT 0,
  `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `unique_session` (`meeting_id`,`session_number`),
  KEY `idx_status` (`status`),
  KEY `idx_sessions_meeting_status` (`meeting_id`,`status`,`session_number`),
  CONSTRAINT `meeting_sessions_ibfk_1` FOREIGN KEY (`meeting_id`) REFERENCES `course_meetings` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- -------------------------------------------------
-- 3c. Attendance (includes multiple check-in summary fields)
-- -------------------------------------------------
CREATE TABLE `attendance` (
  `id` INT(11) NOT NULL AUTO_INCREMENT,
  `student_id` INT(11) NOT NULL,
  `meeting_id` INT(11) NOT NULL,
  `session_id` INT(11) DEFAULT NULL,
  `status` ENUM('present','absent','late','excused') NOT NULL,
  `attendance_time` DATETIME NOT NULL,
  `attendance_method` ENUM('manual','face_recognition','qr_code','rfid','barcode') DEFAULT 'manual',
  `confidence_score` DECIMAL(5,4) DEFAULT NULL,
  `location_lat` DECIMAL(10,8) DEFAULT NULL,
  `location_lng` DECIMAL(11,8) DEFAULT NULL,
  `device_info` VARCHAR(255) DEFAULT NULL,
  `ip_address` VARCHAR(45) DEFAULT NULL,
  `notes` TEXT DEFAULT NULL,
  `marked_by` INT(11) DEFAULT NULL,
  `verified_by` INT(11) DEFAULT NULL,
  `is_valid` TINYINT(1) DEFAULT 1,
  `late_minutes` INT(11) DEFAULT 0,
  `excuse_reason` TEXT DEFAULT NULL,
  `attachment_url` VARCHAR(255) DEFAULT NULL,
  `checkpoints_completed` INT(11) DEFAULT 0,
  `checkpoint_status` VARCHAR(50) DEFAULT 'pending',
  `first_checkpoint_time` DATETIME DEFAULT NULL,
  `last_checkpoint_time` DATETIME DEFAULT NULL,
  `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `unique_attendance` (`student_id`,`meeting_id`),
  KEY `idx_status` (`status`),
  KEY `idx_attendance_time` (`attendance_time`),
  KEY `idx_method` (`attendance_method`),
  KEY `idx_valid` (`is_valid`),
  KEY `idx_attendance_student_meeting` (`student_id`,`meeting_id`,`status`),
  KEY `idx_attendance_meeting_status` (`meeting_id`,`status`,`attendance_time`),
  KEY `idx_attendance_checkpoint_status` (`checkpoint_status`,`checkpoints_completed`),
  CONSTRAINT `attendance_ibfk_1` FOREIGN KEY (`student_id`) REFERENCES `students` (`id`) ON DELETE CASCADE,
  CONSTRAINT `attendance_ibfk_2` FOREIGN KEY (`meeting_id`) REFERENCES `course_meetings` (`id`) ON DELETE CASCADE,
  CONSTRAINT `attendance_ibfk_3` FOREIGN KEY (`session_id`) REFERENCES `meeting_sessions` (`id`) ON DELETE SET NULL,
  CONSTRAINT `attendance_ibfk_4` FOREIGN KEY (`marked_by`) REFERENCES `teachers` (`id`) ON DELETE SET NULL,
  CONSTRAINT `attendance_ibfk_5` FOREIGN KEY (`verified_by`) REFERENCES `teachers` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- -------------------------------------------------
-- 3d. Attendance Checkpoints (Multiple Check-in detail)
-- -------------------------------------------------
CREATE TABLE `attendance_checkpoints` (
  `id` INT(11) NOT NULL AUTO_INCREMENT,
  `attendance_id` INT(11) NOT NULL,
  `checkpoint_number` INT(11) NOT NULL COMMENT '1, 2, 3, or 4',
  `checkpoint_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `detection_method` VARCHAR(50) DEFAULT 'face_recognition',
  `confidence_score` DECIMAL(5,2) DEFAULT NULL,
  `notes` TEXT DEFAULT NULL,
  `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `unique_checkpoint` (`attendance_id`,`checkpoint_number`),
  KEY `idx_checkpoint_number` (`checkpoint_number`),
  KEY `idx_checkpoint_time` (`checkpoint_time`),
  CONSTRAINT `attendance_checkpoints_ibfk_1` FOREIGN KEY (`attendance_id`) REFERENCES `attendance` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =============================================================================
-- 4. SUPPORTING TABLES
-- =============================================================================

-- -------------------------------------------------
-- 4a. Face Dataset (gambar wajah per mahasiswa)
-- -------------------------------------------------
CREATE TABLE `face_dataset` (
  `id` INT(11) NOT NULL AUTO_INCREMENT,
  `student_id` VARCHAR(20) NOT NULL,
  `filename` VARCHAR(255) NOT NULL,
  `filepath` VARCHAR(500) NOT NULL,
  `image_quality` FLOAT DEFAULT 0,
  `capture_timestamp` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `notes` TEXT DEFAULT NULL,
  `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_student_id` (`student_id`),
  KEY `idx_capture_timestamp` (`capture_timestamp`),
  CONSTRAINT `face_dataset_ibfk_1` FOREIGN KEY (`student_id`) REFERENCES `students` (`student_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- -------------------------------------------------
-- 4b. Attendance Settings (per mata kuliah)
-- -------------------------------------------------
CREATE TABLE `attendance_settings` (
  `id` INT(11) NOT NULL AUTO_INCREMENT,
  `course_id` INT(11) NOT NULL,
  `presensi_start_minutes_before` INT(11) DEFAULT 5,
  `presensi_end_minutes_after` INT(11) DEFAULT 0,
  `allow_late_attendance` TINYINT(1) DEFAULT 0,
  `max_late_minutes` INT(11) DEFAULT 0,
  `require_location` TINYINT(1) DEFAULT 0,
  `allowed_radius_meters` INT(11) DEFAULT 100,
  `require_face_recognition` TINYINT(1) DEFAULT 0,
  `min_confidence_score` DECIMAL(5,4) DEFAULT 0.7500,
  `auto_mark_absent` TINYINT(1) DEFAULT 1,
  `reminder_enabled` TINYINT(1) DEFAULT 1,
  `reminder_minutes_before` INT(11) DEFAULT 15,
  `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `unique_course_settings` (`course_id`),
  CONSTRAINT `attendance_settings_ibfk_1` FOREIGN KEY (`course_id`) REFERENCES `courses` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- -------------------------------------------------
-- 4c. Attendance Reports
-- -------------------------------------------------
CREATE TABLE `attendance_reports` (
  `id` INT(11) NOT NULL AUTO_INCREMENT,
  `report_type` ENUM('daily','weekly','monthly','semester','custom') NOT NULL,
  `class_name` VARCHAR(50) DEFAULT NULL,
  `course_id` INT(11) DEFAULT NULL,
  `teacher_id` INT(11) DEFAULT NULL,
  `start_date` DATE NOT NULL,
  `end_date` DATE NOT NULL,
  `total_students` INT(11) DEFAULT 0,
  `total_meetings` INT(11) DEFAULT 0,
  `average_attendance_rate` DECIMAL(5,2) DEFAULT 0.00,
  `report_data` JSON DEFAULT NULL,
  `generated_by` INT(11) DEFAULT NULL,
  `generated_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `expires_at` TIMESTAMP NULL DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_report_type` (`report_type`),
  KEY `idx_dates` (`start_date`,`end_date`),
  KEY `idx_class` (`class_name`),
  CONSTRAINT `attendance_reports_ibfk_1` FOREIGN KEY (`course_id`) REFERENCES `courses` (`id`) ON DELETE CASCADE,
  CONSTRAINT `attendance_reports_ibfk_2` FOREIGN KEY (`teacher_id`) REFERENCES `teachers` (`id`) ON DELETE SET NULL,
  CONSTRAINT `attendance_reports_ibfk_3` FOREIGN KEY (`generated_by`) REFERENCES `users` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- -------------------------------------------------
-- 4d. Notifications
-- -------------------------------------------------
CREATE TABLE `notifications` (
  `id` INT(11) NOT NULL AUTO_INCREMENT,
  `user_id` INT(11) NOT NULL,
  `title` VARCHAR(200) NOT NULL,
  `message` TEXT NOT NULL,
  `type` ENUM('info','warning','error','success') DEFAULT 'info',
  `priority` ENUM('low','medium','high','urgent') DEFAULT 'medium',
  `is_read` TINYINT(1) DEFAULT 0,
  `action_url` VARCHAR(255) DEFAULT NULL,
  `expires_at` TIMESTAMP NULL DEFAULT NULL,
  `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `read_at` TIMESTAMP NULL DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_user_unread` (`user_id`,`is_read`),
  KEY `idx_type_priority` (`type`,`priority`),
  KEY `idx_created_at` (`created_at`),
  CONSTRAINT `notifications_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- -------------------------------------------------
-- 4e. System Logs (audit trail)
-- -------------------------------------------------
CREATE TABLE `system_logs` (
  `id` INT(11) NOT NULL AUTO_INCREMENT,
  `user_id` INT(11) DEFAULT NULL,
  `action` VARCHAR(100) NOT NULL,
  `table_name` VARCHAR(50) DEFAULT NULL,
  `record_id` INT(11) DEFAULT NULL,
  `old_values` JSON DEFAULT NULL,
  `new_values` JSON DEFAULT NULL,
  `ip_address` VARCHAR(45) DEFAULT NULL,
  `user_agent` TEXT DEFAULT NULL,
  `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_user_action` (`user_id`,`action`),
  KEY `idx_table_record` (`table_name`,`record_id`),
  KEY `idx_created_at` (`created_at`),
  CONSTRAINT `system_logs_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- -------------------------------------------------
-- 4f. Performance Metrics
-- -------------------------------------------------
CREATE TABLE `performance_metrics` (
  `id` INT(11) NOT NULL AUTO_INCREMENT,
  `metric_name` VARCHAR(100) NOT NULL,
  `metric_value` DECIMAL(15,4) NOT NULL,
  `metric_unit` VARCHAR(20) DEFAULT NULL,
  `recorded_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_metric_name` (`metric_name`),
  KEY `idx_recorded_at` (`recorded_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- -------------------------------------------------
-- 4g. Schema Migrations (version tracker)
-- -------------------------------------------------
CREATE TABLE `schema_migrations` (
  `id` INT(11) NOT NULL AUTO_INCREMENT,
  `version` VARCHAR(20) NOT NULL,
  `applied_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `description` TEXT DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `version` (`version`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =============================================================================
-- 5. VIEWS
-- =============================================================================

-- Active student enrollments with course & teacher info
CREATE OR REPLACE VIEW `vw_active_enrollments` AS
SELECT
  ce.id, ce.student_id, s.name AS student_name, s.student_id AS nim,
  s.class_name, sch.id AS schedule_id, c.course_code, c.name AS course_name,
  t.name AS teacher_name, sch.day, sch.time_start, sch.time_end, sch.room,
  ce.enrolled_date, ce.attendance_percentage
FROM class_enrollments ce
JOIN students s   ON ce.student_id = s.id
JOIN schedules sch ON ce.schedule_id = sch.id
JOIN courses c    ON sch.course_id = c.id
JOIN teachers t   ON sch.teacher_id = t.id
WHERE ce.status = 'active' AND s.is_active = 1;

-- Per-meeting attendance summary
CREATE OR REPLACE VIEW `vw_attendance_summary` AS
SELECT
  a.meeting_id, cm.schedule_id, cm.meeting_number, cm.meeting_date,
  COUNT(*) AS total_records,
  SUM(CASE WHEN a.status = 'present' THEN 1 ELSE 0 END) AS present_count,
  SUM(CASE WHEN a.status = 'absent'  THEN 1 ELSE 0 END) AS absent_count,
  SUM(CASE WHEN a.status = 'late'    THEN 1 ELSE 0 END) AS late_count,
  SUM(CASE WHEN a.status = 'excused' THEN 1 ELSE 0 END) AS excused_count,
  ROUND(SUM(CASE WHEN a.status IN ('present','late') THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS attendance_rate
FROM attendance a
JOIN course_meetings cm ON a.meeting_id = cm.id
GROUP BY a.meeting_id, cm.schedule_id, cm.meeting_number, cm.meeting_date;

-- Class-level attendance stats
CREATE OR REPLACE VIEW `vw_class_attendance_stats` AS
SELECT
  sch.class_name, c.course_code, c.name AS course_name, t.name AS teacher_name,
  COUNT(DISTINCT ce.student_id)  AS total_students,
  COUNT(DISTINCT cm.id)          AS total_meetings,
  COUNT(DISTINCT a.id)           AS total_attendance_records,
  SUM(CASE WHEN a.status = 'present' THEN 1 ELSE 0 END) AS total_present,
  SUM(CASE WHEN a.status = 'absent'  THEN 1 ELSE 0 END) AS total_absent,
  SUM(CASE WHEN a.status = 'late'    THEN 1 ELSE 0 END) AS total_late,
  SUM(CASE WHEN a.status = 'excused' THEN 1 ELSE 0 END) AS total_excused,
  ROUND(AVG(CASE WHEN a.status IN ('present','late') THEN 1 ELSE 0 END) * 100, 2) AS average_attendance_rate
FROM schedules sch
JOIN courses c  ON sch.course_id = c.id
JOIN teachers t ON sch.teacher_id = t.id
LEFT JOIN class_enrollments ce ON sch.id = ce.schedule_id AND ce.status = 'active'
LEFT JOIN course_meetings cm   ON sch.id = cm.schedule_id
LEFT JOIN attendance a         ON cm.id = a.meeting_id
WHERE sch.is_active = 1
GROUP BY sch.id, sch.class_name, c.course_code, c.name, t.name;

-- Multiple check-in checkpoint summary
CREATE OR REPLACE VIEW `v_attendance_checkpoint_summary` AS
SELECT
  a.id AS attendance_id, a.student_id, a.meeting_id, a.status,
  a.checkpoints_completed, a.checkpoint_status,
  cm.total_checkpoints, cm.checkpoint_interval, cm.checkpoint_enabled,
  COUNT(ac.id) AS actual_checkpoints,
  GROUP_CONCAT(ac.checkpoint_number ORDER BY ac.checkpoint_number) AS completed_checkpoint_numbers,
  MIN(ac.checkpoint_time) AS first_checkpoint,
  MAX(ac.checkpoint_time) AS last_checkpoint,
  CASE
    WHEN cm.checkpoint_enabled = 0 THEN 'disabled'
    WHEN COUNT(ac.id) = 0 THEN 'no_checkins'
    WHEN COUNT(ac.id) = cm.total_checkpoints THEN 'full'
    WHEN COUNT(ac.id) >= CEIL(cm.total_checkpoints * 0.75) THEN 'good'
    WHEN COUNT(ac.id) >= CEIL(cm.total_checkpoints * 0.5) THEN 'partial'
    ELSE 'poor'
  END AS checkpoint_grade
FROM attendance a
LEFT JOIN attendance_checkpoints ac ON a.id = ac.attendance_id
LEFT JOIN course_meetings cm ON a.meeting_id = cm.id
GROUP BY a.id, a.student_id, a.meeting_id, a.status,
         a.checkpoints_completed, a.checkpoint_status,
         cm.total_checkpoints, cm.checkpoint_interval, cm.checkpoint_enabled;

-- =============================================================================
-- 6. STORED PROCEDURES
-- =============================================================================

DELIMITER $$

-- Mark attendance for a student
CREATE PROCEDURE `MarkStudentAttendance` (
  IN p_student_id INT,
  IN p_meeting_id INT,
  IN p_status VARCHAR(20),
  IN p_notes TEXT,
  IN p_marked_by INT
)
BEGIN
  DECLARE v_late_minutes INT DEFAULT 0;
  DECLARE v_meeting_date DATE;
  DECLARE v_time_start TIME;

  SELECT cm.meeting_date, sch.time_start
  INTO v_meeting_date, v_time_start
  FROM course_meetings cm
  JOIN schedules sch ON cm.schedule_id = sch.id
  WHERE cm.id = p_meeting_id;

  IF p_status = 'late' THEN
    SET v_late_minutes = TIMESTAMPDIFF(MINUTE,
      CONCAT(v_meeting_date, ' ', v_time_start), NOW());
    IF v_late_minutes < 0 THEN SET v_late_minutes = 0; END IF;
  END IF;

  INSERT INTO attendance (
    student_id, meeting_id, status, attendance_time,
    notes, marked_by, late_minutes
  ) VALUES (
    p_student_id, p_meeting_id, p_status, NOW(),
    p_notes, p_marked_by, v_late_minutes
  ) ON DUPLICATE KEY UPDATE
    status = p_status,
    attendance_time = NOW(),
    notes = p_notes,
    marked_by = p_marked_by,
    late_minutes = v_late_minutes,
    updated_at = CURRENT_TIMESTAMP;
END$$

-- Get attendance data by class
CREATE PROCEDURE `GetAttendanceByClass` (IN `class_name` VARCHAR(50))
BEGIN
  SELECT
    s.student_id AS nim, s.name AS student_name,
    c.course_code, c.name AS course_name,
    cm.meeting_number, cm.meeting_date,
    COALESCE(a.status, 'not_marked') AS status,
    a.attendance_time, a.late_minutes
  FROM schedules sch
  JOIN courses c ON sch.course_id = c.id
  JOIN class_enrollments ce ON sch.id = ce.schedule_id
  JOIN students s ON ce.student_id = s.id
  LEFT JOIN course_meetings cm ON sch.id = cm.schedule_id
  LEFT JOIN attendance a ON cm.id = a.meeting_id AND a.student_id = s.id
  WHERE sch.class_name = class_name AND ce.status = 'active'
  ORDER BY s.name, cm.meeting_date;
END$$

-- Mark a checkpoint (multiple check-in)
CREATE PROCEDURE `mark_checkpoint_attendance` (
  IN p_student_id INT,
  IN p_meeting_id INT,
  IN p_checkpoint_number INT,
  IN p_method VARCHAR(50),
  IN p_confidence DECIMAL(5,2),
  IN p_notes TEXT
)
BEGIN
  DECLARE v_attendance_id INT;

  SELECT id INTO v_attendance_id
  FROM attendance
  WHERE student_id = p_student_id AND meeting_id = p_meeting_id;

  IF v_attendance_id IS NULL THEN
    INSERT INTO attendance (student_id, meeting_id, status, attendance_time, attendance_method)
    VALUES (p_student_id, p_meeting_id, 'present', NOW(), p_method);
    SET v_attendance_id = LAST_INSERT_ID();
  END IF;

  INSERT INTO attendance_checkpoints
    (attendance_id, checkpoint_number, checkpoint_time, detection_method, confidence_score, notes)
  VALUES
    (v_attendance_id, p_checkpoint_number, NOW(), p_method, p_confidence, p_notes)
  ON DUPLICATE KEY UPDATE
    checkpoint_time = NOW(),
    detection_method = p_method,
    confidence_score = p_confidence,
    notes = p_notes;

  SELECT 'success' AS status, v_attendance_id AS attendance_id;
END$$

DELIMITER ;

-- =============================================================================
-- 7. TRIGGERS
-- =============================================================================

DELIMITER $$

CREATE TRIGGER `after_checkpoint_insert`
AFTER INSERT ON `attendance_checkpoints`
FOR EACH ROW
BEGIN
  DECLARE total_completed INT;
  DECLARE first_time DATETIME;
  DECLARE last_time DATETIME;
  DECLARE total_required INT;
  DECLARE new_status VARCHAR(50);

  SELECT COUNT(*), MIN(checkpoint_time), MAX(checkpoint_time)
  INTO total_completed, first_time, last_time
  FROM attendance_checkpoints
  WHERE attendance_id = NEW.attendance_id;

  SELECT cm.total_checkpoints INTO total_required
  FROM attendance a
  JOIN course_meetings cm ON a.meeting_id = cm.id
  WHERE a.id = NEW.attendance_id;

  IF total_completed = total_required THEN
    SET new_status = 'full';
  ELSEIF total_completed >= CEIL(total_required * 0.75) THEN
    SET new_status = 'good';
  ELSEIF total_completed >= CEIL(total_required * 0.5) THEN
    SET new_status = 'partial';
  ELSE
    SET new_status = 'poor';
  END IF;

  UPDATE attendance
  SET checkpoints_completed = total_completed,
      checkpoint_status = new_status,
      first_checkpoint_time = first_time,
      last_checkpoint_time = last_time
  WHERE id = NEW.attendance_id;
END$$

DELIMITER ;

-- =============================================================================
-- 8. SEED DATA (minimum data agar aplikasi bisa berjalan)
-- =============================================================================

-- Default admin user (password: 'password')
INSERT INTO `users` (`username`, `email`, `password_hash`, `role`, `is_active`, `email_verified`, `profile_completed`, `preferences`)
VALUES ('admin', 'admin@polimdo.ac.id',
  '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LwH3eFAr3SJ1W8aqy',
  'admin', 1, 1, 1,
  '{"theme": "light", "language": "id", "notifications": true}');

-- Default program studies for Politeknik Negeri Manado
INSERT INTO `program_studies` (`name`, `abbreviation`, `department`) VALUES
  ('Teknik Informatika', 'TI', 'Teknik Elektro'),
  ('Teknik Komputer', 'TK', 'Teknik Elektro'),
  ('Teknik Listrik', 'TL', 'Teknik Elektro');

-- Schema version marker
INSERT INTO `schema_migrations` (`version`, `description`) VALUES
  ('3.0', 'Clean schema with integrated multiple check-in support');

COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
