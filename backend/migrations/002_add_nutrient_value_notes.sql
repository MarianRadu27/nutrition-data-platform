-- Preserve source markers for nutrient values such as <1, <.1, and trace.
-- Numeric nutrient columns can still store 0 for calculations.

SET @sql = IF(
  (
    SELECT COUNT(*)
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_SCHEMA = DATABASE()
      AND TABLE_NAME = 'foods'
      AND COLUMN_NAME = 'nutrient_value_notes'
  ) = 0,
  'ALTER TABLE foods ADD COLUMN nutrient_value_notes JSON NULL AFTER food_description_ro',
  'DO 0'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;
