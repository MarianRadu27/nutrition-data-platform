# Work Log and Handoff

Last updated: 2026-06-16

This file is an internal handoff note for continuing the project on another PC
or in a new Codex conversation. It is written for the developer of this project,
not as public product documentation.

## Project Identity

Project name:

```text
nutrition-data-platform
```

GitHub repository:

```text
https://github.com/MarianRadu27/nutrition-data-platform
```

Local path used recently:

```text
D:\nutrition-data-platform
```

Older local path used earlier in the project:

```text
D:\nutrition-project
```

If a command fails because of the path, first check which folder exists on the
current machine.

## Project Vision

The project started as a learning project for data engineering and data
analysis. The goal is to build a visible GitHub project that shows practical
skills:

- reading and profiling real datasets;
- importing messy food/nutrition data;
- normalizing values;
- designing database tables;
- building a backend API;
- building frontend pages that consume the API;
- documenting source data and decisions.

The domain is nutrition because the project may later become a public website
for the developer's partner, who is a nutritionist. The long-term product idea
is:

- users can browse food composition data for free;
- users can use a nutrition calculator without manually entering calories,
  protein, carbs, fat, etc.;
- the website can also promote the nutritionist's services;
- source datasets are credited clearly;
- the site remains transparent about data provenance, limitations, and
  disclaimers.

The current calculator still uses the original local USDA/Appendix H-style data.
External datasets such as NEVO, ANSES/Ciqual, BLS, and Open Food Facts are being
profiled first. They should not be rushed into the current `foods` table.

More context is documented in:

```text
docs/project_vision.md
docs/data_sources.md
docs/external_source_schema_draft.md
```

## Preferred Collaboration Style

This is important for future Codex sessions.

The developer wants to learn, not just receive finished code. Default style:

- explain in Romanian;
- keep the tone friendly and practical;
- give one small next step at a time;
- avoid dumping full code unless the developer asks for it;
- when checking code, say exactly what is correct and what is wrong;
- when the developer says "verifica", inspect the actual file on disk;
- use examples only where the concept is hard;
- explain Python concepts visually when possible;
- keep comments/docstrings in code in English;
- avoid modifying files unless explicitly asked;
- when modifying files, give clickable file references afterward.

The developer often asks questions to understand fundamentals:

- `Path`, `.resolve()`, `.parents`;
- `with`;
- `open(..., "r")`;
- `encoding`, `newline`;
- `csv.DictReader`;
- `row["column"]`;
- `.items()`, `.keys()`, `.get()`;
- `zip`;
- `set`;
- `lambda`;
- `return 0` and `return 1`;
- `if __name__ == "__main__"`;
- type hints like `columns: list[str]`;
- sorting dictionaries and lists.

The developer prefers to write the code manually when learning. If stuck, give
a small concrete example, then check again.

## Git Workflow

Common commit flow:

```powershell
cd D:\nutrition-data-platform
git status
git add <files>
git status
git diff --staged
git commit -m "Message here"
git pull --rebase origin main
git push origin main
```

To exit `git diff --staged`:

```text
q
```

If the most recent commit message needs changing before push:

```powershell
git commit --amend -m "New message"
```

If already pushed, usually leave the message alone unless there is a strong
reason to rewrite history.

Recent commits at the time this file was created:

```text
4f03a6b Complete ANSES nutrient profiling
2188b6f Add initial ANSES profiling
6eaf632 Profile Nevo dataset and draft external source schema
61078f6 Profile NEVO dataset structure and relationships
4462251 Add NEVO profiling script and notes
```

At the time this file was created, the working tree was clean before adding this
file.

## Moving To A New PC

On the new PC:

```powershell
git clone https://github.com/MarianRadu27/nutrition-data-platform.git
cd nutrition-data-platform
```

Important: raw source files are not necessarily in Git. The `temp/` folder must
be copied separately if the profiling scripts should work immediately.

Important local folder:

```text
temp/EuropeNutrientsDBs
```

This contains external source datasets such as:

```text
nevo
anses
```

The `temp/` folder should stay out of Git unless the project deliberately adds
small public sample files. The source datasets are public, but keeping large raw
files out of the repo is still cleaner.

## Useful Commands

Run ANSES profiling:

```powershell
cd D:\nutrition-data-platform
py backend\scripts\external_sources\profile_anses.py
```

Run NEVO profiling:

```powershell
cd D:\nutrition-data-platform
py backend\scripts\external_sources\profile_nevo.py
```

Check Python syntax only:

```powershell
py -m py_compile backend\scripts\external_sources\profile_anses.py
```

Check whitespace issues:

```powershell
git diff --check
```

Note: `git diff --check` may report trailing whitespace. These are not runtime
errors, but should be cleaned before commit when possible.

## Current Application State

The app has:

- a backend in `backend/`;
- a frontend in `frontend/`;
- scripts for importing and profiling data;
- docs describing source data and modeling plans.

The current public-facing app still uses the original local food dataset. The
external source datasets are not yet wired into the calculator.

Known frontend areas:

```text
frontend/app/foods/page.tsx
frontend/app/calculator/page.tsx
frontend/app/admin/add-food/page.tsx
```

The foods page has grown to support:

- grouped category/food display;
- filtering;
- sorting;
- expandable extra nutrients;
- selecting how many rows to display;
- hover highlight;
- Romanian translated columns in the database and UI context.

The calculator page currently:

- lets the user select foods;
- uses grams entered by the user;
- calculates a factor based on selected grams versus source weight;
- multiplies nutrients by that factor;
- groups calculated items by gram amount in result tables.

The calculator should stay on the existing local dataset for now. Do not switch
it to NEVO/ANSES until the external-source schema and imports are designed.

## Existing Data Import Work

The original food import script was renamed:

```text
backend/scripts/import_tabel_alim.py
```

to:

```text
backend/scripts/import_data_db.py
```

A helper script was added:

```text
backend/scripts/mark_own_subcategories.py
```

Purpose:

- detect bold Excel rows that represent foods which should become their own
  subcategory;
- write or support an `own_subcategory` workflow;
- make import behavior safer and reproducible.

Important import lesson:

Some rows in the source Excel are visually bold and have an ID. They should be
treated as "food becomes its own subcategory", not as a normal food under the
previous subcategory.

Preferred future method:

- use explicit Excel columns such as `own_subcategory`;
- avoid relying only on visual formatting like bold;
- keep imports repeatable.

## Translation Work

Romanian translation workflow was created to avoid manually editing database
rows.

Relevant scripts:

```text
backend/scripts/translation/export_translation_review.py
backend/scripts/translation/export_chatgpt_batch.py
backend/scripts/translation/import_chatgpt_batch.py
backend/scripts/translation/import_translation_review_db.py
backend/scripts/translation/apply_translations_to_foods_final.py
```

Workflow summary:

1. Export review workbook.
2. Export CSV batches for ChatGPT translation.
3. Import translated CSV back into review workbook.
4. Approve/import translations into DB.
5. Optionally apply translations back to `FoodsFinal`-style Excel.

Important result:

- categories, foods, and food descriptions were translated into Romanian;
- `import_translation_review_db.py` updated DB columns successfully;
- `FoodsFinal_with_ro` was generated by applying translations to the Excel
  source.

Translation lesson:

Simple glossary replacement is dangerous. Example: replacing `raw` blindly can
corrupt words like `strawberry`. Batch translation plus review is safer.

## Data Sources

Documented in:

```text
docs/data_sources.md
```

Current sources discussed:

- current local USDA/Appendix H-style food table;
- NEVO, Netherlands;
- ANSES/Ciqual, France;
- BLS, Germany;
- Open Food Facts, planned.

Open Food Facts note:

- CSV is usually better for bulk data engineering ingestion;
- JSON is useful to learn nested data structures and for API-style records;
- no final Open Food Facts import decision has been implemented yet.

## External Source Schema Direction

Draft documented in:

```text
docs/external_source_schema_draft.md
```

High-level idea:

- do not merge all external data directly into the current `foods` table;
- keep source-specific food rows;
- keep source-specific nutrient values;
- preserve raw values and source metadata;
- later build canonical food/nutrient mapping.

Suggested conceptual tables:

```text
data_sources
source_foods
nutrients
source_nutrients
source_references
source_food_nutrient_values
canonical_foods
canonical_food_source_links
```

Important concept:

Canonical means "the project's standard internal representation".

Example:

```text
NEVO: Potatoes raw
ANSES: Potato, raw
USDA: Potatoes, raw

Canonical food: Potato, raw
```

Do not deduplicate foods too early. First preserve source data. Then design
canonical matching rules.

## NEVO Profiling Status

Script:

```text
backend/scripts/external_sources/profile_nevo.py
```

Documentation:

```text
docs/nevo_profile.md
```

NEVO source files:

```text
temp/EuropeNutrientsDBs/nevo/NEVO2025_v9.0.csv
temp/EuropeNutrientsDBs/nevo/NEVO2025_v9.0_Nutrienten_Nutrients.csv
temp/EuropeNutrientsDBs/nevo/NEVO2025_v9.0_Details.csv
```

Key findings:

- main file rows: 2328;
- main file columns: 148;
- metadata columns: 11;
- nutrient columns: 137;
- quantity values:
  - `per 100g`: 2275;
  - `per 100ml`: 53;
- unique NEVO food codes: 2328;
- duplicate NEVO food codes: 0;
- nutrient dictionary rows: 142;
- nutrient codes in main: 137;
- nutrient codes in dictionary: 137;
- main/dictionary code mismatch: 0;
- details file rows: 270810;
- details food codes: 2328;
- details nutrient codes: 137;
- details/main food code mismatch: 0;
- details/dictionary nutrient code mismatch: 0;
- duplicate food/nutrient pairs exist in details, but value conflicts are 0;
- main/details value mismatches are 0 after treating missing values consistently;
- details source/reference fields have no missing rows.

Important NEVO interpretation:

- main file is wide format and easier for common nutrient import;
- details file is long format and preserves source/reference information;
- both are useful;
- details duplicates are not necessarily bad because they can represent repeated
  source/reference rows with the same value.

Current NEVO status:

- profiling is complete enough for the next modeling/import design phase;
- no NEVO import has been implemented yet.

## ANSES Profiling Status

Script:

```text
backend/scripts/external_sources/profile_anses.py
```

Documentation:

```text
docs/anses_profile.md
```

Source files:

```text
temp/EuropeNutrientsDBs/anses/Table Ciqual 2025_ENG_2025_11_03.xlsx
temp/EuropeNutrientsDBs/anses/Table Ciqual 2025 doc ENG_2025_11_19.pdf
```

Workbook sheets:

```text
food composition
INFOODS codes
```

Completed ANSES profiling for `food composition`:

- rows: 3485;
- data rows: 3484;
- columns: 84;
- metadata columns: 9;
- nutrient columns: 75;
- food code column: `alim_code`;
- unique food codes: 3484;
- duplicate food codes: 0;
- category levels:
  - `alim_grp_nom_eng`;
  - `alim_ssgrp_nom_eng`;
  - `alim_ssssgrp_nom_eng`;
- category counts:
  - categories: 11;
  - subcategories: 64;
  - subsubcategories: 77;
- placeholder value is exactly `-`;
- use `value == "-"`, not `"-" in value`, because real values like
  `non-alcoholic beverages` contain hyphens.

ANSES nutrient completeness:

- every nutrient satisfies `present + missing = 3484`;
- most incomplete include:
  - Vitamin K2: present 175, missing 3309;
  - Vitamin E: present 595, missing 2889;
  - Galactose: present 743, missing 2741;
  - folate-related values have high missing counts;
- most complete include:
  - Jones factor: present 3484, missing 0;
  - Alcohol: present 3480, missing 4;
  - Fat: present 3464, missing 20;
  - Protein: present 3455, missing 29;
  - Carbohydrate: present 3414, missing 70;
  - Fibres: present 3414, missing 70.

Important ANSES numeric discovery:

- many numeric-looking nutrient values are stored as text;
- decimal separator is comma, e.g. `"4,41"`;
- convert comma to dot before numeric parsing;
- `0` is a valid numeric value, not missing.

Special non-numeric values discovered:

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

- `< ...` values are below a limit and should not be blindly converted to zero;
- `traces` means trace amounts;
- raw source text should be preserved;
- future import should support something like:

```text
raw_value = "< 0,01"
numeric_value = 0.01
value_qualifier = "less_than"
```

For `traces`, it may be safer to preserve raw text and a qualifier without a
numeric value.

Current ANSES status:

- `food composition` sheet profiling is complete enough for documentation;
- `INFOODS codes` sheet is not yet profiled;
- documentation has been updated in `docs/anses_profile.md`;
- latest commit pushed was:

```text
4f03a6b Complete ANSES nutrient profiling
```

## Where We Left Off

The next planned task is:

```text
Profile the ANSES `INFOODS codes` sheet.
```

Recommended next steps:

1. Open `profile_anses.py`.
2. Add a function to inspect the `INFOODS codes` sheet.
3. Print:
   - sheet name;
   - total rows;
   - total columns;
   - headers;
   - first 10 rows.
4. Determine whether `INFOODS codes` maps nutrient names to standardized
   nutrient codes.
5. Update `docs/anses_profile.md` with the findings.
6. Only after that, compare ANSES nutrient codes to NEVO nutrient codes.

Do not start import tables yet. Finish profiling and mapping first.

## Suggested Next Conversation Prompt

When starting on the new PC, paste something like:

```text
I cloned the repo on a new PC. Please read docs/work_log.md first and continue
from "Where We Left Off". I want to keep the same learning style: explain in
Romanian, give small steps, and let me write the code unless I ask you to edit.
```

Then ask:

```text
Hai sa continuam cu profilarea sheet-ului INFOODS codes din ANSES.
```

