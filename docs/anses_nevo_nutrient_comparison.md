# ANSES vs NEVO Nutrient Comparison

This document summarizes the comparison between ANSES/Ciqual nutrient
definitions and NEVO nutrient definitions.

The goal is not to import data yet. The goal is to understand how source
nutrient codes, names, units, and standard tags relate before designing the
external-source tables.

## Source Files

ANSES:

```text
temp/EuropeNutrientsDBs/anses/Table Ciqual 2025_ENG_2025_11_03.xlsx
sheet: INFOODS codes
```

NEVO:

```text
temp/EuropeNutrientsDBs/nevo/NEVO2025_v9.0_Nutrienten_Nutrients.csv
```

Comparison script:

```text
backend/scripts/external_sources/compare_anses_nevo_nutrients.py
```

## Summary

Observed counts:

```text
ANSES nutrient definitions: 74
NEVO unique nutrient definitions: 137
Direct ANSES INFDSTAG -> NEVO code matches: 34
Exact normalized name/unit matches: 27
Likely name/unit matches with different codes: 1
ANSES nutrients covered by these checks: 41
ANSES nutrients not covered: 33
```

Interpretation:

- ANSES and NEVO overlap strongly for core nutrients, minerals, several
  vitamins, and some fatty-acid groups.
- They do not use the same code system consistently.
- A direct code match is useful when ANSES `INFDSTAG` equals a NEVO
  `Nutrient-code`, but this is not enough for all nutrients.
- Some nutrients clearly match by name and unit even when the codes differ.
- Some nutrients require manual canonical mapping.

## Important Direct Code Matches

Examples where ANSES `INFDSTAG` matches the NEVO `Nutrient-code` directly:

```text
ANSES WATER -> NEVO WATER | Water | g
ANSES ASH   -> NEVO ASH   | Ash | g
ANSES NA    -> NEVO NA    | Sodium | mg
ANSES MG    -> NEVO MG    | Magnesium | mg
ANSES P     -> NEVO P     | Phosphorus | mg
ANSES K     -> NEVO K     | Potassium | mg
ANSES CA    -> NEVO CA    | Calcium | mg
ANSES FE    -> NEVO FE    | Iron | mg
ANSES CU    -> NEVO CU    | Copper | mg
ANSES ZN    -> NEVO ZN    | Zinc | mg
ANSES SE    -> NEVO SE    | Selenium | ug
ANSES ID    -> NEVO ID    | Iodine | ug
ANSES SUGAR -> NEVO SUGAR | Sugars | g
ANSES STARCH -> NEVO STARCH | Starch | g
ANSES FAT   -> NEVO FAT   | Fat | g
ANSES FASAT -> NEVO FASAT | Saturated fatty acids | g
ANSES FAPU  -> NEVO FAPU  | Polyunsaturated fatty acids | g
```

These are good candidates for early canonical mapping.

## Same Meaning, Different Codes

Some nutrients match by normalized name and unit, but use different source
codes:

```text
ANSES PROCNT / 25000 Protein (g)
NEVO  PROT          Protein total (g)

ANSES CHOAVL / 31000 Carbohydrate (g)
NEVO  CHO           Carbohydrate available (g)

ANSES CARTB / 51330 Beta-carotene (ug)
NEVO  CARTBTOT      Beta-carotene (ug)

ANSES VITD- / 52100 Vitamin D (ug)
NEVO  VITD          Vitamin D total (ug)

ANSES VITE- / 53100 Vitamin E (mg)
NEVO  VITE          Vitamin E total (mg)

ANSES CHOL- / 75100 Cholesterol (mg)
NEVO  CHORL         Cholesterol (mg)
```

There is also one high-confidence likely match:

```text
ANSES FIB- / 34100 Fibres (g)
NEVO  FIBT          Fibre dietary total (g)
```

These examples show why the project needs a canonical nutrient mapping layer.
Source codes alone are not enough.

## Nutrients That Need Manual Review

The comparison did not confidently cover 33 ANSES nutrients.

Important examples:

```text
Energy, Regulation EU No 1169/2011 (kJ)
Energy, Regulation EU No 1169/2011 (kcal)
Energy, N x Jones' factor, with fibres (kJ)
Energy, N x Jones' factor, with fibres (kcal)
Salt
Chloride
Manganese
Protein, crude, N x 6.25
Fructose
Galactose
Glucose
Lactose
Maltose
Sucrose
FA mono
Vitamin A activity, retinol equivalent
Vitamin B5 or Pantothenic acid
Vitamin B6
Vitamin B9, dietary folate equivalents
```

Many fatty-acid detail rows also need manual review because ANSES and NEVO use
different code shapes, for example:

```text
ANSES F18D1CN9
NEVO  F18:1CIS or another related fatty-acid code
```

These should not be auto-mapped only by fuzzy text similarity.

## Schema Implications

The external-source model should keep at least these concepts separate:

```text
source_nutrient_code
source_nutrient_name
unit
source_standard_tag
canonical_nutrient_id
```

For ANSES:

```text
source_nutrient_code -> ORIGCPCD
source_nutrient_name -> const_nom_eng
unit -> parsed from const_nom_eng
source_standard_tag -> INFDSTAG
```

For NEVO:

```text
source_nutrient_code -> Nutrient-code
source_nutrient_name -> Component
unit -> Eenheid/Unit
source_standard_tag -> NULL for now
```

The future canonical mapping should be reviewed manually for core nutrients
first. After the core mapping is stable, specialized vitamins, sugars, folates,
and fatty acids can be added in smaller groups.

## Recommended Next Step

Create a small canonical nutrient draft for the calculator-critical nutrients:

```text
energy_kcal
protein_g
carbohydrate_g
fat_g
fiber_g
sugar_g
salt_g
sodium_mg
water_g
```

Then map ANSES and NEVO source nutrients to those canonical nutrients manually.
This is a small enough next step to review safely before creating database
migrations.
