-- Add semester and academic_year columns to schedules table
-- Run this in phpMyAdmin or MySQL client if the columns don't exist yet

USE student_attendance;

-- Check if columns exist first, then add them if they don't
ALTER TABLE schedules 
ADD COLUMN IF NOT EXISTS semester VARCHAR(20) DEFAULT NULL AFTER room,
ADD COLUMN IF NOT EXISTS academic_year VARCHAR(20) DEFAULT NULL AFTER semester;

-- Show the updated structure
DESCRIBE schedules;
