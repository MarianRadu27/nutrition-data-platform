-- Add Romanian display columns.
-- Written to be safe on databases restored from backups that already contain them.

SET @sql = IF(
  (
    SELECT COUNT(*)
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_SCHEMA = DATABASE()
      AND TABLE_NAME = 'categories'
      AND COLUMN_NAME = 'name_ro'
  ) = 0,
  'ALTER TABLE categories ADD COLUMN name_ro VARCHAR(255) NULL',
  'DO 0'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @sql = IF(
  (
    SELECT COUNT(*)
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_SCHEMA = DATABASE()
      AND TABLE_NAME = 'subcategories'
      AND COLUMN_NAME = 'name_ro'
  ) = 0,
  'ALTER TABLE subcategories ADD COLUMN name_ro VARCHAR(255) NULL',
  'DO 0'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @sql = IF(
  (
    SELECT COUNT(*)
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_SCHEMA = DATABASE()
      AND TABLE_NAME = 'foods'
      AND COLUMN_NAME = 'food_description_ro'
  ) = 0,
  'ALTER TABLE foods ADD COLUMN food_description_ro VARCHAR(255) NULL',
  'DO 0'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;
