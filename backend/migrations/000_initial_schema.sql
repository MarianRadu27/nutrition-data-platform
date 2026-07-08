-- Initial application schema for the nutrition database.
-- Data is imported separately from Excel or backups.

CREATE TABLE IF NOT EXISTS categories (
  id INT UNSIGNED NOT NULL AUTO_INCREMENT,
  name VARCHAR(255) NOT NULL,
  PRIMARY KEY (id),
  UNIQUE KEY uq_categories_name (name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE IF NOT EXISTS subcategories (
  id INT UNSIGNED NOT NULL AUTO_INCREMENT,
  category_id INT UNSIGNED NOT NULL,
  name VARCHAR(255) NOT NULL,
  PRIMARY KEY (id),
  UNIQUE KEY uq_subcategories_cat_name (category_id, name),
  CONSTRAINT fk_subcategories_category
    FOREIGN KEY (category_id)
    REFERENCES categories (id)
    ON DELETE RESTRICT
    ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE IF NOT EXISTS foods (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  da_code INT UNSIGNED NOT NULL,
  subcategory_id INT UNSIGNED NULL,
  food_description VARCHAR(255) NOT NULL,
  quantity DECIMAL(10,3) NULL,
  measure VARCHAR(64) NULL,
  wt_g DECIMAL(10,2) NULL,
  h2o_g DECIMAL(10,2) NULL,
  ener_kcal DECIMAL(10,2) NULL,
  prot_g DECIMAL(10,2) NULL,
  carbo_g DECIMAL(10,2) NULL,
  fiber_g DECIMAL(10,2) NULL,
  fat_g DECIMAL(10,2) NULL,
  sat_g DECIMAL(10,2) NULL,
  mono_g DECIMAL(10,2) NULL,
  poly_g DECIMAL(10,2) NULL,
  trans_g DECIMAL(10,2) NULL,
  chol_mg DECIMAL(10,2) NULL,
  calc_mg DECIMAL(10,2) NULL,
  iron_mg DECIMAL(10,2) NULL,
  magn_mg DECIMAL(10,2) NULL,
  pota_mg DECIMAL(10,2) NULL,
  sodi_mg DECIMAL(10,2) NULL,
  zinc_mg DECIMAL(10,2) NULL,
  vit_a_ug DECIMAL(10,2) NULL,
  vit_e_mg DECIMAL(10,2) NULL,
  thia_mg DECIMAL(10,2) NULL,
  ribo_mg DECIMAL(10,2) NULL,
  niac_mg DECIMAL(10,2) NULL,
  vit_b6_mg DECIMAL(10,2) NULL,
  fola_ug DECIMAL(10,2) NULL,
  vit_c_mg DECIMAL(10,2) NULL,
  vit_b12_ug DECIMAL(10,2) NULL,
  sele_ug DECIMAL(10,2) NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uq_foods_da_code (da_code),
  KEY idx_foods_subcategory (subcategory_id),
  CONSTRAINT fk_foods_subcategory
    FOREIGN KEY (subcategory_id)
    REFERENCES subcategories (id)
    ON DELETE SET NULL
    ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
