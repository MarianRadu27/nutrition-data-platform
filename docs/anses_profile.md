# ANSES/Ciqual Dataset Profile

This document summarizes the initial profiling work for the ANSES/Ciqual 2025 dataset.

The goal of this profiling step is to understand the dataset before designing database tables or writing an importer. This follows the same workflow used for NEVO: inspect first, model second, import third.

## Source Files

Local files inspected:

```text
temp/EuropeNutrientsDBs/anses/Table Ciqual 2025_ENG_2025_11_03.xlsx
temp/EuropeNutrientsDBs/anses/Table Ciqual 2025 doc ENG_2025_11_19.pdf
```

Profiling script:

```text
backend/scripts/external_sources/profile_anses.py
```

## Workbook Structure

Main workbook:

```text
Table Ciqual 2025_ENG_2025_11_03.xlsx
```

Observed sheet names:

```text
food composition
INFOODS codes
```

The current profiling covers:

```text
food composition
INFOODS codes
```

## Food Composition Sheet

Observed profile:

```text
Rows: 3485
Columns: 84
Metadata columns: 9
Nutrient columns: 75
```

The file is in wide format:

```text
one row = one food
many nutrient columns = nutrient values for that food
```

The first 9 columns describe the food:

```text
alim_grp_code
alim_ssgrp_code
alim_ssssgrp_code
alim_grp_nom_eng
alim_ssgrp_nom_eng
alim_ssssgrp_nom_eng
alim_code
alim_nom_eng
alim_nom_sci
```

The nutrient columns begin at:

```text
Energy,
Regulation
EU No
1169
2011 (kJ
100g)
```

Observation:

The nutrient headers contain line breaks. The importer should not rely on manually typed column names more than necessary. Important column names should be stored as constants or mapped through a controlled dictionary.

## Food Identity

The main source identifier appears to be:

```text
alim_code
```

Observed profile:

```text
Unique food codes: 3484
Duplicate food codes: 0
```

Conclusion:

`alim_code` can be used as `source_food_code` for ANSES/Ciqual source foods.

Example rows:

```text
24999 | - | - | - | Dessert (average)
8406 | starters and dishes | mixed salads | - | Salad of pig's snout, with sauce, prepacked
8407 | starters and dishes | mixed salads | - | Salad of saveloy, with sauce, prepacked
25600 | starters and dishes | mixed salads | - | Celeriac salad, with remoulade sauce, prepacked
25601 | starters and dishes | mixed salads | - | Tuna salad, with vegetables, canned
```

## Categories

ANSES/Ciqual provides three English category levels:

```text
alim_grp_nom_eng
alim_ssgrp_nom_eng
alim_ssssgrp_nom_eng
```

Observed profile:

```text
Categories: 11
Subcategories: 64
Subsubcategories: 77
```

Placeholder counts:

```text
Category placeholder rows: 1
Subcategory placeholder rows: 2
Subsubcategory placeholder rows: 1450
```

The placeholder value is:

```text
-
```

Important distinction:

The placeholder should be checked with exact equality:

```text
value == "-"
```

It should not be checked with substring logic such as:

```text
"-" in value
```

Reason:

Some valid category names contain hyphens, such as `non-alcoholic beverages`. These are real category values and should not be treated as missing.

First observed categories:

```text
baby food
beverages
cereal products
fats and oils
fruits, vegetables, legumes and nuts
ice cream and sorbet
meat, egg and fish
milk and milk products
miscellaneous
starters and dishes
sugar and confectionery
```

First observed subcategories:

```text
Viennese pastries
alcoholic beverages
baby biscuits and cereals
baby deserts
baby dishes
baby milk and beverages
breads and similar
breakfast cereals
butters
cakes and pastry
cereal bars
cheese and similar
chocolate and chocolate products
condiments
cooked meat
cooking aids
cream and similar
dairy products
delicatessen meat and similar
dishes
```

First observed subsubcategories:

```text
beef and veal
beers and ciders
beverages, to reconstitute
blue cheeses
breads
canned fruits
cheese dishes
cocktails
coffee, tea, cocoa beverages, etc. ready to drink
cold sauces
cooked ham
dairy beverages
dairy desserts
dessert sauces
dried fruits
dried herbs
dry sausages
eggs, cooked
eggs, raw
fish dishes, no garnish
```

Conclusion:

The ANSES/Ciqual category model is more structured than the current local food table. It has three category levels, but the third level is not always present. Placeholder category values should be stored as `NULL` during import.

## Nutrient Completeness

The 75 nutrient columns were profiled across all 3,484 food rows.

For every nutrient:

```text
present values + missing values = 3484
```

The nutrients with the most missing values include:

```text
Vitamin K2: present=175, missing=3309
Vitamin E: present=595, missing=2889
Galactose: present=743, missing=2741
Vitamin B9, dietary folate equivalents: present=908, missing=2576
Intrinsic folate: present=912, missing=2572
Vitamin B9, total folates: present=1525, missing=1959
Vitamin D2: present=1542, missing=1942
Chloride: present=1545, missing=1939
Vitamin K1: present=1574, missing=1910
Folic acid: present=1614, missing=1870
```

The most complete columns include:

```text
Jones factor: present=3484, missing=0
Alcohol: present=3480, missing=4
Fat: present=3464, missing=20
Protein: present=3455, missing=29
Protein, crude, N x 6.25: present=3455, missing=29
Carbohydrate: present=3414, missing=70
Fibres: present=3414, missing=70
Ash: present=3382, missing=102
Energy, EU regulation, kJ: present=3341, missing=143
Energy, EU regulation, kcal: present=3341, missing=143
Salt: present=3294, missing=190
Sugars: present=3261, missing=223
```

Important observations:

- `Jones factor` is metadata used in protein calculations, not a nutrient value.
- Missing-value coverage varies considerably between nutrients.
- Core macronutrients are substantially more complete than several vitamins, fatty acids, and carbohydrate subtypes.
- A present source value is not necessarily directly numeric.

## INFOODS Codes Sheet

The workbook also contains an `INFOODS codes` sheet.

Observed profile:

```text
Rows: 75
Columns: 3
Data rows: 74
Headers: INFDSTAG, ORIGCPCD, const_nom_eng
```

The 74 data rows map ANSES nutrient names to source nutrient codes and INFOODS
tags.

Example rows:

```text
INFDSTAG | ORIGCPCD | const_nom_eng
ENERC    | 327      | Energy, Regulation EU No 1169/2011 (kJ/100g)
ENERC    | 328      | Energy, Regulation EU No 1169/2011 (kcal/100g)
WATER    | 400      | Water (g/100g)
ASH      | 10000    | Ash (g/100g)
         | 10004    | Salt (g/100g)
NA       | 10110    | Sodium (mg/100g)
```

Important mapping result:

```text
Food composition nutrient columns: 75
INFOODS data rows: 74
Food nutrient columns without INFOODS row: 1
INFOODS rows without food nutrient column: 0
```

The only `food composition` nutrient column without an `INFOODS codes` row is:

```text
Jones factor
```

This supports the earlier interpretation that `Jones factor` should be treated
as metadata, not as a normal nutrient measurement.

The `INFOODS codes` sheet is not in the same order as the nutrient columns in
`food composition`. A future importer must map by normalized nutrient name, not
by position.

Observed code behavior:

```text
Rows with empty INFDSTAG: 1
Repeated non-empty INFDSTAG codes: 2
```

The empty `INFDSTAG` row is:

```text
ORIGCPCD = 10004
const_nom_eng = Salt (g/100g)
```

Repeated `INFDSTAG` values:

```text
ENERC: 4
PROCNT: 2
```

Interpretation:

- `ORIGCPCD` appears to be the better ANSES-specific unique nutrient code.
- `INFDSTAG` should be preserved as the INFOODS tag when present.
- `INFDSTAG` should not be treated as unique.
- nutrient units can likely be parsed from `const_nom_eng`, but this should be
  done with controlled parsing and review.

## Numeric Representation

Most nutrient values are stored in the workbook as text rather than as native Excel numbers.

Examples:

```text
"1070"
"4,41"
"0,94"
```

The source uses a comma as the decimal separator. Before numeric conversion, values such as:

```text
"4,41"
```

must be normalized to:

```text
"4.41"
```

The profiling script distinguishes between:

```text
missing values
numeric values stored as numbers or numeric text
special non-numeric values
```

## Special Non-Numeric Values

The dataset contains many valid source observations that cannot be converted directly to a numeric value.

The most frequent normalized values are:

```text
< 0,01: 5443
traces: 2514
< 0,1: 1813
< 0,2: 1811
< 0,5: 1447
< 20: 1258
< 0,25: 828
< 1: 492
< 5: 438
< 0,3: 416
< 0,05: 363
< 0,08: 304
< 2: 298
< 0,15: 291
< 0,8: 252
< 0,002: 226
< 0,0002: 219
< 0,35: 181
< 30: 176
< 0,015: 174
```

Interpretation:

- Values beginning with `<` represent measurements below a detection or quantification limit.
- `traces` indicates that a nutrient is present only in trace amounts.
- These values must not automatically be converted to zero.
- The original source text should be preserved during import.

A future importer should separate the numeric component from its source qualifier. One possible representation is:

```text
raw_value = "< 0,01"
numeric_value = 0.01
value_qualifier = "less_than"
```

For `traces`, the raw value and qualifier should be preserved even if no numeric value is stored.

## Import Implications

Recommended future mapping:

```text
alim_code -> source_foods.source_food_code
alim_nom_eng -> source_foods.food_name_en
alim_nom_sci -> source_foods.scientific_name or notes
alim_grp_nom_eng -> source_foods.category_1
alim_ssgrp_nom_eng -> source_foods.category_2
alim_ssssgrp_nom_eng -> source_foods.category_3
nutrient columns -> source_food_nutrient_values.value
INFOODS codes.ORIGCPCD -> source_nutrients.source_nutrient_code
INFOODS codes.const_nom_eng -> source_nutrients.source_nutrient_name
INFOODS codes.INFDSTAG -> preserved INFOODS tag/source metadata
```

ANSES/Ciqual should be imported into external-source tables, not directly into the current `foods` table.

The import process will also need to:

- convert comma decimal separators before numeric parsing;
- preserve the original raw nutrient value;
- distinguish missing values from trace values;
- preserve less-than qualifiers;
- keep the source nutrient name and unit;
- treat `Jones factor` separately from nutrient measurements.

The current calculator should continue using the existing local Appendix H dataset until external-source data is fully modeled, validated, and reviewed.

## Next Profiling Steps

Recommended next checks:

1. Review the ANSES documentation for the exact meaning of `<` values and `traces`.
2. Decide how the external-source schema should preserve source qualifiers, raw values, and INFOODS tags.
3. Compare the ANSES/Ciqual nutrient structure with the NEVO nutrient model.
4. Define the canonical mapping needed by the external-source schema.
5. Only after that, design the external-source migrations and import scripts.
