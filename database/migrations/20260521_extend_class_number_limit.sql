-- Migration: Extend class_number limit to 7
-- Date: 2026-05-21

-- Add a check constraint to allow class_number 1..7 (idempotent)
SET @constraint_exists := (
    SELECT COUNT(*)
    FROM information_schema.table_constraints
    WHERE constraint_schema = DATABASE()
      AND table_name = 'students'
      AND constraint_name = 'chk_students_class_number'
      AND constraint_type = 'CHECK'
);

SET @sql := IF(
    @constraint_exists = 0,
    'ALTER TABLE students ADD CONSTRAINT chk_students_class_number CHECK (class_number >= 1 AND class_number <= 7)',
    'SELECT "Constraint already exists"'
);

PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;
