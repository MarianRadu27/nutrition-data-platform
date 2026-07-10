-- Create tables for external nutrition data sources such as NEVO and ANSES.
-- These tables keep source data separate from the current local foods table.

CREATE TABLE IF NOT EXISTS data_sources (
  id INT UNSIGNED NOT NULL AUTO_INCREMENT,
  code VARCHAR(64) NOT NULL,
  name VARCHAR(255) NOT NULL,
  country VARCHAR(100) NULL,
  publisher VARCHAR(255) NULL,
  source_url VARCHAR(1000) NULL,
  license_name VARCHAR(255) NULL,
  license_url VARCHAR(1000) NULL,
  attribution_text TEXT NULL,
  version VARCHAR(100) NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uq_data_sources_code (code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE IF NOT EXISTS canonical_nutrients (
  id INT UNSIGNED NOT NULL AUTO_INCREMENT,
  canonical_code VARCHAR(100) NOT NULL,
  name_en VARCHAR(255) NOT NULL,
  name_ro VARCHAR(255) NULL,
  default_unit VARCHAR(32) NULL,
  nutrient_group VARCHAR(100) NULL,
  description TEXT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uq_canonical_nutrients_code (canonical_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE IF NOT EXISTS source_foods (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  data_source_id INT UNSIGNED NOT NULL,
  source_food_code VARCHAR(100) NOT NULL,
  food_name_original VARCHAR(500) NULL,
  food_name_en VARCHAR(500) NULL,
  food_name_ro VARCHAR(500) NULL,
  category_original VARCHAR(255) NULL,
  category_en VARCHAR(255) NULL,
  category_ro VARCHAR(255) NULL,
  basis VARCHAR(32) NULL,
  notes TEXT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uq_source_foods_source_code (data_source_id, source_food_code),
  KEY idx_source_foods_data_source (data_source_id),
  KEY idx_source_foods_name_en (food_name_en),
  KEY idx_source_foods_name_ro (food_name_ro),
  CONSTRAINT fk_source_foods_data_source
    FOREIGN KEY (data_source_id)
    REFERENCES data_sources (id)
    ON DELETE RESTRICT
    ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE IF NOT EXISTS source_nutrients (
  id INT UNSIGNED NOT NULL AUTO_INCREMENT,
  data_source_id INT UNSIGNED NOT NULL,
  source_nutrient_code VARCHAR(100) NOT NULL,
  source_nutrient_name VARCHAR(500) NOT NULL,
  source_nutrient_name_ro VARCHAR(500) NULL,
  source_standard_tag VARCHAR(100) NULL,
  unit VARCHAR(32) NULL,
  component_group VARCHAR(255) NULL,
  canonical_nutrient_id INT UNSIGNED NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uq_source_nutrients_source_code (data_source_id, source_nutrient_code),
  KEY idx_source_nutrients_data_source (data_source_id),
  KEY idx_source_nutrients_canonical (canonical_nutrient_id),
  KEY idx_source_nutrients_standard_tag (source_standard_tag),
  CONSTRAINT fk_source_nutrients_data_source
    FOREIGN KEY (data_source_id)
    REFERENCES data_sources (id)
    ON DELETE RESTRICT
    ON UPDATE CASCADE,
  CONSTRAINT fk_source_nutrients_canonical
    FOREIGN KEY (canonical_nutrient_id)
    REFERENCES canonical_nutrients (id)
    ON DELETE SET NULL
    ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE IF NOT EXISTS source_references (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  data_source_id INT UNSIGNED NOT NULL,
  source_code VARCHAR(100) NOT NULL,
  reference_text TEXT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uq_source_references_source_code (data_source_id, source_code),
  KEY idx_source_references_data_source (data_source_id),
  CONSTRAINT fk_source_references_data_source
    FOREIGN KEY (data_source_id)
    REFERENCES data_sources (id)
    ON DELETE RESTRICT
    ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE IF NOT EXISTS source_food_nutrient_values (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  source_food_id BIGINT UNSIGNED NOT NULL,
  source_nutrient_id INT UNSIGNED NOT NULL,
  raw_value VARCHAR(100) NULL,
  value DECIMAL(20,8) NULL,
  value_qualifier VARCHAR(50) NULL,
  unit VARCHAR(32) NULL,
  basis VARCHAR(32) NULL,
  reference_id BIGINT UNSIGNED NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY idx_source_values_food (source_food_id),
  KEY idx_source_values_nutrient (source_nutrient_id),
  KEY idx_source_values_food_nutrient (source_food_id, source_nutrient_id),
  KEY idx_source_values_reference (reference_id),
  CONSTRAINT fk_source_values_food
    FOREIGN KEY (source_food_id)
    REFERENCES source_foods (id)
    ON DELETE CASCADE
    ON UPDATE CASCADE,
  CONSTRAINT fk_source_values_nutrient
    FOREIGN KEY (source_nutrient_id)
    REFERENCES source_nutrients (id)
    ON DELETE RESTRICT
    ON UPDATE CASCADE,
  CONSTRAINT fk_source_values_reference
    FOREIGN KEY (reference_id)
    REFERENCES source_references (id)
    ON DELETE SET NULL
    ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
