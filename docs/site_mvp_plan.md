# Site MVP Plan - dieteticianteodora.ro

This document defines the first usable product version for
`dieteticianteodora.ro`.

The goal is to move the project from database work toward a professional
nutrition website that can be used by real visitors and by a dietitian.

## Brand

Website / domain:

```text
dieteticianteodora.ro
```

Dietitian name:

```text
Teodora Pălii
```

## Product Goal

The site should present Teodora Pălii as a professional dietitian and help
visitors take the next step toward a consultation.

The main user action should be:

```text
Schedule a consultation.
```

The food database and nutrient calculator should support this goal by giving
visitors a useful free tool and by showing that the site uses structured food
data from multiple European nutrition sources.

## Target Audience

The first version is for people who want more balance in their diet and need a
simple way to calculate nutrients.

The audience includes people who:

- want to understand their daily calorie and macronutrient intake;
- want a healthier eating routine;
- need practical nutrition guidance;
- may later book a consultation with a dietitian.

## Tone And Visual Direction

The site should feel:

- modern premium;
- medical and professional;
- calm, trustworthy, and clear;
- polished without feeling cold or overly clinical.

The design should support credibility first. The calculator and database should
feel like professional tools, not like a casual calorie counter clone.

## MVP Pages

The first version should focus on a small set of useful pages.

### Home

Purpose:

- introduce Teodora Pălii;
- explain the value of the site;
- guide the visitor toward scheduling a consultation;
- highlight the free nutrient calculator as a useful tool.

Primary call to action:

```text
Schedule a consultation
```

Secondary call to action:

```text
Try the nutrient calculator
```

### Calculator

Purpose:

- let users calculate nutrients from selected foods;
- demonstrate that the site uses multiple food composition sources.

MVP behavior:

- choose one or more data sources;
- search for a food;
- add grams;
- return a table with:
  - calories;
  - protein;
  - carbohydrates;
  - fat;
  - fiber.

Initial data sources:

```text
NEVO
ANSES_CIQUAL
```

Later behavior:

- average equivalent foods across sources;
- support more micronutrients;
- support BLS and other sources;
- save meal calculations.

### Food Database

Purpose:

- allow users to browse or search food data by source;
- make the external nutrition database visible as a site feature.

MVP behavior:

- choose source: NEVO or ANSES;
- search foods;
- view basic nutrient values for one selected food;
- show source attribution where relevant.

### Services / Pricing

Purpose:

- explain what Teodora offers;
- help visitors understand the consultation options.

Initial services:

- initial consultation;
- food plan;
- monthly monitoring.

Pricing can be added when final prices are known.

### Blog

Purpose:

- prepare the site for nutrition articles later.

MVP behavior:

- simple placeholder or simple article list page;
- no full blog CMS required in the first version unless needed.

Later behavior:

- article categories;
- article detail pages;
- admin workflow for publishing posts.

### About

Purpose:

- present Teodora Pălii;
- build trust;
- explain professional background and approach.

### Contact / Booking

Purpose:

- make it easy to schedule a consultation.

MVP behavior:

- contact details or booking call to action;
- simple contact form only if backend/email handling is ready.

## What The MVP Should Not Do Yet

To keep the first version focused, the MVP should not include:

- user accounts;
- online payments;
- automatic food matching between NEVO and ANSES;
- BLS import;
- full blog admin system;
- complex meal-plan generation;
- saved user meal history;
- automatic source averaging.

These can be added after the first professional site version is working.

## Data Scope For The MVP

The current imported sources are enough for the first public calculator:

```text
NEVO
ANSES_CIQUAL
```

Current source status:

- NEVO foods and nutrient values are imported;
- ANSES foods and nutrient values are imported;
- core canonical nutrients are mapped;
- micronutrients can be mapped later without losing the imported raw data.

The calculator MVP should use the current canonical nutrients:

- energy;
- protein;
- carbohydrate;
- fat;
- fiber;
- sugar;
- sodium;
- water;
- salt where available.

The public calculator can start with only the main displayed nutrients:

- calories;
- protein;
- carbohydrates;
- fat;
- fiber.

## Important Later Work

### Food Matching Across Sources

Food matching means identifying that two foods from different sources represent
the same or a very similar food.

Example:

```text
NEVO: Banana
ANSES: Banana, pulp, raw
```

This is not required if the user chooses a single source. It becomes important
when the site wants to average values across sources.

### Micronutrient Mapping

Micronutrients can be mapped later by adding more canonical nutrient rows and
linking existing source nutrients to them.

Examples:

- calcium;
- iron;
- potassium;
- magnesium;
- vitamin C;
- vitamin B12;
- folate.

The raw source data is already preserved, so this can be done incrementally.

