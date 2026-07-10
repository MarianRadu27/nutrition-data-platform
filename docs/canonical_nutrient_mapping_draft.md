# Canonical Nutrient Mapping Draft

This document drafts the first small canonical nutrient set for the calculator
and maps ANSES/Ciqual and NEVO source nutrients to it.

This is a review document only. It does not define database tables yet.

## Why This Exists

Different sources use different nutrient codes for the same practical nutrient.

Example:

```text
ANSES: PROCNT / ORIGCPCD 25000 / Protein (g/100g)
NEVO:  PROT / Protein total / g
```

The project should not merge source codes directly. Instead, each source
nutrient should map to a project-owned canonical nutrient.

Example:

```text
ANSES PROCNT -> protein_g
NEVO PROT    -> protein_g
```

This preserves source data while giving the calculator stable internal names.

## Draft Canonical Nutrients

| Canonical code | Display name | Default unit | Initial purpose |
| --- | --- | --- | --- |
| `energy_kcal` | Energy | kcal | calculator |
| `protein_g` | Protein | g | calculator |
| `carbohydrate_g` | Carbohydrate | g | calculator |
| `fat_g` | Fat | g | calculator |
| `fiber_g` | Fiber | g | calculator |
| `sugar_g` | Sugars | g | nutrition detail |
| `salt_g` | Salt | g | nutrition detail |
| `sodium_mg` | Sodium | mg | nutrition detail and possible salt derivation |
| `water_g` | Water | g | nutrition detail |

## ANSES Mapping

ANSES source nutrient identity should use `ORIGCPCD` as the source-specific
nutrient code. `INFDSTAG` should be preserved as a standard/source tag when it
exists, but it is not unique.

| Canonical code | ANSES ORIGCPCD | ANSES INFDSTAG | ANSES source name | Source unit | Decision |
| --- | ---: | --- | --- | --- | --- |
| `energy_kcal` | `328` | `ENERC` | Energy, Regulation EU No 1169/2011 (kcal/100g) | kcal | use for calculator kcal |
| `protein_g` | `25000` | `PROCNT` | Protein (g/100g) | g | use instead of crude protein |
| `carbohydrate_g` | `31000` | `CHOAVL` | Carbohydrate (g/100g) | g | use |
| `fat_g` | `40000` | `FAT` | Fat (g/100g) | g | use |
| `fiber_g` | `34100` | `FIB-` | Fibres (g/100g) | g | use |
| `sugar_g` | `32000` | `SUGAR` | Sugars (g/100g) | g | use |
| `salt_g` | `10004` |  | Salt (g/100g) | g | use |
| `sodium_mg` | `10110` | `NA` | Sodium (mg/100g) | mg | use |
| `water_g` | `400` | `WATER` | Water (g/100g) | g | use |

ANSES energy alternatives that should not be used for the first calculator
mapping:

| ORIGCPCD | INFDSTAG | Source name | Reason |
| ---: | --- | --- | --- |
| `327` | `ENERC` | Energy, Regulation EU No 1169/2011 (kJ/100g) | kJ, not calculator kcal |
| `332` | `ENERC` | Energy, N x Jones' factor, with fibres (kJ/100g) | alternate method and kJ |
| `333` | `ENERC` | Energy, N x Jones' factor, with fibres (kcal/100g) | alternate method |

ANSES protein alternative that should not be used for the first calculator
mapping:

| ORIGCPCD | INFDSTAG | Source name | Reason |
| ---: | --- | --- | --- |
| `25003` | `PROCNT` | Protein, crude, N x 6.25 (g/100g) | crude protein, not the first calculator protein target |

## NEVO Mapping

NEVO source nutrient identity should use `Nutrient-code`.

| Canonical code | NEVO Nutrient-code | NEVO source name | Source unit | Decision |
| --- | --- | --- | --- | --- |
| `energy_kcal` | `ENERCC` | Energy kcal | kcal | use for calculator kcal |
| `protein_g` | `PROT` | Protein total | g | use |
| `carbohydrate_g` | `CHO` | Carbohydrate available | g | use |
| `fat_g` | `FAT` | Fat total | g | use |
| `fiber_g` | `FIBT` | Fibre dietary total | g | use |
| `sugar_g` | `SUGAR` | Sugars total | g | use |
| `salt_g` |  |  |  | no direct NEVO nutrient found; derive from sodium only if the project approves a derivation rule |
| `sodium_mg` | `NA` | Sodium | mg | use |
| `water_g` | `WATER` | Water total | g | use |

NEVO energy alternative:

| Nutrient-code | Source name | Source unit | Reason |
| --- | --- | --- | --- |
| `ENERCJ` | Energy kJ | kJ | kJ, not calculator kcal |

## First Design Decisions

Use these decisions for the first external-source schema design:

- keep source nutrients separate from canonical nutrients;
- map source nutrients to canonical nutrients with a nullable
  `canonical_nutrient_id`;
- preserve ANSES `INFDSTAG` as source metadata, not as the unique source code;
- store ANSES `ORIGCPCD` as the ANSES `source_nutrient_code`;
- store NEVO `Nutrient-code` as the NEVO `source_nutrient_code`;
- do not derive `salt_g` from NEVO sodium until the derivation rule is reviewed.

## Next Step

After reviewing this draft, the next safe step is to update the external-source
schema draft with these concepts:

```text
canonical_nutrients
source_nutrients.canonical_nutrient_id
source_nutrients.source_standard_tag
```

Database migrations should wait until this mapping is reviewed.
