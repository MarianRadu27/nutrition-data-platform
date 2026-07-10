-- Seed initial canonical nutrients used by the calculator and external-source mapping.

INSERT INTO canonical_nutrients (
  canonical_code,
  name_en,
  name_ro,
  default_unit,
  nutrient_group,
  description
) VALUES
  (
    'energy_kcal',
    'Energy',
    'Energie',
    'kcal',
    'energy',
    'Energy in kilocalories.'
  ),
  (
    'protein_g',
    'Protein',
    'Proteine',
    'g',
    'macronutrient',
    'Protein in grams.'
  ),
  (
    'carbohydrate_g',
    'Carbohydrate',
    'Carbohidrati',
    'g',
    'macronutrient',
    'Available carbohydrate in grams.'
  ),
  (
    'fat_g',
    'Fat',
    'Grasimi',
    'g',
    'macronutrient',
    'Fat in grams.'
  ),
  (
    'fiber_g',
    'Fiber',
    'Fibre',
    'g',
    'macronutrient',
    'Dietary fiber in grams.'
  ),
  (
    'sugar_g',
    'Sugars',
    'Zaharuri',
    'g',
    'carbohydrate',
    'Sugars in grams.'
  ),
  (
    'salt_g',
    'Salt',
    'Sare',
    'g',
    'mineral',
    'Salt in grams.'
  ),
  (
    'sodium_mg',
    'Sodium',
    'Sodiu',
    'mg',
    'mineral',
    'Sodium in milligrams.'
  ),
  (
    'water_g',
    'Water',
    'Apa',
    'g',
    'other',
    'Water in grams.'
  )
ON DUPLICATE KEY UPDATE
  name_en = VALUES(name_en),
  name_ro = VALUES(name_ro),
  default_unit = VALUES(default_unit),
  nutrient_group = VALUES(nutrient_group),
  description = VALUES(description);
