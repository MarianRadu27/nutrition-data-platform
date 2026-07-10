# External Source Schema Draft

This document outlines a future database model for importing external nutrition datasets such as NEVO, ANSES/Ciqual, BLS, Open Food Facts, and other official or public sources.

The current application still uses the existing local USDA/Appendix H-style dataset for the calculator. External sources should be modeled separately first, then validated before they are connected to user-facing calculator features.

## Design Goals

The external-source model should support:

- multiple nutrition data providers
- source-specific food identifiers
- source-specific categories and food names
- many nutrients per food
- missing nutrient values stored as missing values, not zero
- source raw nutrient values and value qualifiers such as `less_than` and `trace`
- source and reference metadata for nutrient values
- source-specific nutrients mapped to project-owned canonical nutrients
- future mapping between similar foods from different sources

The model should avoid forcing all datasets into the current `foods` table too early. Different sources have different structures, units, naming conventions, and reference systems.

## Proposed Tables

## Visual Example

The model can be understood as a set of linked tables.

```text
data_sources
    |
    |-- source_foods
    |
    |-- source_nutrients
    |        |
    |        |-- canonical_nutrients
    |
    |-- source_references

source_foods ---- source_food_nutrient_values ---- source_nutrients
                         |
                         |
                  source_references
```

Example source:

```text
data_sources

id | code | name      | country
1  | NEVO | NEVO 2025 | Netherlands
```

Example foods:

```text
source_foods

id | data_source_id | source_food_code | food_name_en      | category_en          | basis
1  | 1              | 1                | Potatoes raw      | Potatoes and tubers  | per_100g
2  | 1              | 2                | Potatoes new raw  | Potatoes and tubers  | per_100g
3  | 1              | 270              | Milk raw          | Milk and products    | per_100ml
```

Example nutrients:

```text
source_nutrients

id | data_source_id | source_nutrient_code | source_nutrient_name | unit | canonical_nutrient_id
1  | 1              | ENERCC               | Energy kcal          | kcal | 1
2  | 1              | PROT                 | Protein total        | g    | 2
3  | 1              | FAT                  | Fat total            | g    | 4
4  | 1              | FIBT                 | Fibre dietary total  | g    | 5
```

Example canonical nutrients:

```text
canonical_nutrients

id | canonical_code | name_en      | default_unit
1  | energy_kcal    | Energy       | kcal
2  | protein_g      | Protein      | g
3  | carbohydrate_g | Carbohydrate | g
4  | fat_g          | Fat          | g
5  | fiber_g        | Fiber        | g
```

Example references:

```text
source_references

id | data_source_id | source_code | reference_text
1  | 1              | REF.0472    | logical reasoning...
2  | 1              | REF.0814    | NEVO-team internal document...
```

Example nutrient values:

```text
source_food_nutrient_values

id | source_food_id | source_nutrient_id | raw_value | value | value_qualifier | unit | basis    | reference_id
1  | 1              | 1                  | 80        | 80    |                 | kcal | per_100g | 2
2  | 1              | 2                  | 2         | 2     |                 | g    | per_100g | 1
3  | 1              | 3                  | 0.1       | 0.1   |                 | g    | per_100g | 1
4  | 1              | 4                  | 1.8       | 1.8   |                 | g    | per_100g | 1
5  | 1              | 5                  | < 0,01    | 0.01  | less_than       | g    | per_100g | 1
```

This means:

```text
Potatoes raw has 80 kcal per 100g according to reference 2.
Potatoes raw has 2 g protein per 100g according to reference 1.
Potatoes raw has 0.1 g fat per 100g according to reference 1.
Potatoes raw has 1.8 g fibre per 100g according to reference 1.
```

This structure keeps foods, nutrients, values, references, and data sources separate. That makes the database easier to validate and easier to extend with more datasets later.

### data_sources

Stores one row per external dataset.

Examples:

```text
NEVO
ANSES_CIQUAL
BLS
OPEN_FOOD_FACTS
USDA_APPENDIX_H
```

Suggested fields:

```text
id
code
name
country
publisher
source_url
license_name
license_url
attribution_text
version
created_at
updated_at
```

Purpose:

This table identifies where each imported food record comes from.

### source_foods

Stores foods exactly as they appear in each source dataset.

Suggested fields:

```text
id
data_source_id
source_food_code
food_name_original
food_name_en
food_name_ro
category_original
category_en
category_ro
basis
notes
created_at
updated_at
```

NEVO examples:

```text
source_food_code -> NEVO-code
food_name_original -> Voedingsmiddelnaam/Dutch food name
food_name_en -> Engelse naam/Food name
category_en -> Food group
basis -> Hoeveelheid/Quantity, for example per 100g or per 100ml
```

Purpose:

This table keeps source foods separate from the current user-facing `foods` table. It preserves the original source identity and prevents premature deduplication.

### canonical_nutrients

Stores project-owned nutrient definitions.

Suggested fields:

```text
id
canonical_code
name_en
name_ro
default_unit
nutrient_group
description
created_at
updated_at
```

Examples:

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

Purpose:

This table gives the project a stable vocabulary for nutrients. Source-specific nutrient codes can be mapped to these canonical nutrients.

For example:

```text
ANSES PROCNT / ORIGCPCD 25000 -> protein_g
NEVO PROT                     -> protein_g
```

The calculator should eventually depend on canonical nutrient codes such as
`protein_g`, not directly on source-specific codes such as `PROCNT` or `PROT`.

### source_nutrients

Stores nutrient definitions as provided by each source.

Suggested fields:

```text
id
data_source_id
source_nutrient_code
source_nutrient_name
source_nutrient_name_ro
source_standard_tag
unit
component_group
canonical_nutrient_id
created_at
updated_at
```

NEVO examples:

```text
source_nutrient_code -> Nutrient-code
source_nutrient_name -> Component
source_nutrient_name_ro -> Romanian translation, nullable
source_standard_tag -> NULL for now
unit -> Eenheid/Unit
component_group -> Component group
```

ANSES examples:

```text
source_nutrient_code -> ORIGCPCD
source_nutrient_name -> const_nom_eng
source_nutrient_name_ro -> Romanian translation, nullable
source_standard_tag -> INFDSTAG
unit -> parsed from const_nom_eng
component_group -> NULL for now
```

Purpose:

This table separates source-specific nutrient definitions from the future canonical nutrient model.

For example, NEVO has `ENERCC`, while another source may use another code for kcal. Both can eventually map to the same canonical nutrient.

Important source-code decisions:

- ANSES `ORIGCPCD` should be stored as `source_nutrient_code`.
- ANSES `INFDSTAG` should be stored as `source_standard_tag`.
- ANSES `INFDSTAG` should not be treated as unique because values such as
  `ENERC` and `PROCNT` repeat.
- NEVO `Nutrient-code` should be stored as `source_nutrient_code`.
- NEVO does not currently provide an equivalent standard tag in the profiled
  nutrient dictionary.

### source_references

Stores source and reference metadata for nutrient values.

Suggested fields:

```text
id
data_source_id
source_code
reference_text
created_at
updated_at
```

NEVO examples:

```text
source_code -> Broncode/Source code
reference_text -> Referentie/Reference
```

Purpose:

This table avoids repeating long reference text on every nutrient-value row. It also preserves data lineage.

### source_food_nutrient_values

Stores nutrient values for source foods.

Suggested fields:

```text
id
source_food_id
source_nutrient_id
raw_value
value
value_qualifier
unit
basis
reference_id
created_at
updated_at
```

NEVO examples:

```text
source_food_id -> source_foods.id for a NEVO-code
source_nutrient_id -> source_nutrients.id for a Nutrient-code
raw_value -> original source text, when available
value -> Gehalte/Value
value_qualifier -> NULL, less_than, trace, estimated, etc.
unit -> Eenheid/Unit
basis -> per 100g or per 100ml
reference_id -> source_references.id
```

Purpose:

This is the main fact table for nutrition values.

One row means:

```text
one source food + one source nutrient + one value
```

The `raw_value` field preserves the source representation. The numeric `value`
field is for numeric calculations and comparison. The `value_qualifier` field
stores meaning that would otherwise be lost, such as "below limit" or "trace".

## Handling Missing Values

Missing nutrient values should be stored as `NULL`.

They should not be converted to zero unless the source explicitly reports zero.

Reason:

```text
missing value = unknown or unavailable
zero = known measured/reported zero
```

These are different meanings and should not be mixed.

## Handling Less-Than and Trace Values

ANSES/Ciqual contains valid non-numeric nutrient values such as:

```text
< 0,01
< 1
traces
```

These should not be treated as ordinary missing values.

Suggested storage:

```text
raw_value = "< 0,01"
value = 0.01
value_qualifier = "less_than"
```

For trace values:

```text
raw_value = "traces"
value = NULL
value_qualifier = "trace"
```

Calculator behavior can later decide whether `less_than` or `trace` values
should count as zero, a limit value, or another reviewed rule. The import layer
should preserve the source information first.

## Handling `per 100g` and `per 100ml`

NEVO has two observed bases:

```text
per 100g
per 100ml
```

The import model should preserve this basis.

Suggested normalized values:

```text
per_100g
per_100ml
```

Calculator logic should not assume that every source food is per 100 g.

## Handling Duplicate Food/Nutrient Pairs

NEVO Details contains repeated `NEVO-code + Nutrient-code` pairs because some nutrients appear in more than one component group.

Profiling showed:

```text
Food/nutrient pairs with different value or unit: 0
```

This means repeated pairs do not create conflicting nutrient values.

Possible import rule:

```text
Deduplicate NEVO values by source_food_code, source_nutrient_code, value, unit, and reference.
```

The importer should still log repeated pairs so the behavior is visible during validation.

## Future Food Deduplication

Foods from different sources should not be merged too early.

For example:

```text
banana in NEVO
banana in ANSES
banana in BLS
banana in Open Food Facts
```

These records may look similar but can have different:

- source codes
- languages
- categories
- nutrient methods
- units
- branded/generic status
- references

A future matching layer can be added later.

Possible future table:

```text
canonical_foods
```

Possible future link table:

```text
canonical_food_source_links
```

Purpose:

This would allow the application to group equivalent foods while preserving each source record.

## Recommended Import Order

For each source, the future import should happen in this order:

1. Insert `data_sources` row.
2. Insert or validate relevant `canonical_nutrients`.
3. Import `source_foods`.
4. Import `source_nutrients`.
5. Link source nutrients to canonical nutrients where the mapping has been
   reviewed.
6. Import `source_references` if the source provides references.
7. Import `source_food_nutrient_values`.
8. Run validation checks after import.

For NEVO:

```text
source_foods -> NEVO2025_v9.0.csv
source_nutrients -> NEVO2025_v9.0_Nutrienten_Nutrients.csv
source_references -> source/reference fields in NEVO2025_v9.0_Details.csv
source_food_nutrient_values -> NEVO2025_v9.0_Details.csv
```

For ANSES/Ciqual:

```text
source_foods -> food composition sheet
source_nutrients -> INFOODS codes sheet
source_food_nutrient_values -> food composition sheet nutrient columns
source_references -> not yet designed; review source documentation first
```

## Recommended Validation Checks

After importing NEVO, validate:

- number of imported foods equals 2328
- number of unique source nutrient codes equals 137
- no missing `source_food_id` links
- no missing `source_nutrient_id` links
- no missing source/reference metadata
- kcal/protein/carbs/fat/fibre values match the profiled main file
- missing values remain `NULL`
- `per 100g` and `per 100ml` are preserved

After importing ANSES/Ciqual, validate:

- number of imported foods equals 3484
- number of imported source nutrients equals 74 from `INFOODS codes`
- `Jones factor` is not imported as a normal source nutrient unless explicitly
  modeled as metadata
- ANSES `ORIGCPCD` values are used as source nutrient codes
- ANSES `INFDSTAG` values are preserved as `source_standard_tag`
- values such as `< 0,01` and `traces` preserve their raw value and qualifier
- calculator-critical mappings match `docs/canonical_nutrient_mapping_draft.md`

## Current Decision

The current calculator should continue using the existing local dataset.

External sources should be imported into separate tables first. After profiling, validation, and review, the project can decide how to expose those sources in the UI.

The next implementation step should not be a full import yet. The safer next
step is to turn this draft into a small migration for external-source tables
after reviewing the schema fields above.
