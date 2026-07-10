# Meal Nutrition Calculator

A full-stack nutrition application built with **FastAPI**, **MySQL**, and **Next.js**.

The app lets users browse foods, filter by category and food group, calculate meal nutrition from grams, add new foods from an admin page, and work with Romanian translations for food data.

## Main Features

- Browse foods from a MySQL database.
- Filter by category and food group.
- Expand and collapse grouped food rows.
- Show or hide extra nutrient columns.
- Sort and limit food results.
- Calculate meal nutrition totals from selected foods and grams.
- Add foods from an admin page.
- Import food data from Excel.
- Mark foods that should become their own food group with `own_subcategory`.
- Export, review, import, and apply Romanian translations.

## Tech Stack

### Backend

- Python
- FastAPI
- Pydantic
- PyMySQL
- MySQL
- Uvicorn

### Frontend

- Next.js
- React
- TypeScript

### Infrastructure

- Docker Compose
- MySQL container
- Adminer container

## Project Structure

```text
nutrition-data-platform/
|
|-- backend/
|   |-- app/
|   |   |-- db.py
|   |   |-- main.py
|   |   |-- repositories.py
|   |   |-- schemas.py
|   |
|   |-- data/
|   |   |-- FoodsFinal_sample.xlsx
|   |
|   |-- migrations/
|   |   |-- 000_initial_schema.sql
|   |   |-- 001_add_ro_columns.sql
|   |   |-- 002_add_nutrient_value_notes.sql
|   |
|   |-- scripts/
|   |   |-- apply_migrations.py
|   |   |-- import_data_db.py
|   |   |-- mark_own_subcategories.py
|   |   |-- smoke_test.py
|   |   |-- translation/
|   |       |-- apply_translations_to_foods_final.py
|   |       |-- export_chatgpt_batch.py
|   |       |-- export_translation_review.py
|   |       |-- import_chatgpt_batch.py
|   |       |-- import_translation_review_db.py
|   |
|   |-- .env.example
|   |-- requirements.txt
|
|-- frontend/
|   |-- app/
|   |   |-- admin/add-food/page.tsx
|   |   |-- calculator/page.tsx
|   |   |-- foods/page.tsx
|   |   |-- layout.tsx
|   |   |-- page.tsx
|   |
|   |-- .env.local.example
|   |-- package.json
|
|-- infra/
|   |-- docker-compose.yml
|
|-- .gitignore
|-- README.md
```

## Sample Data

The repository includes a small public sample file:

```text
backend/data/FoodsFinal_sample.xlsx
```

This file is intentionally small so other people can test the project without having access to the full private dataset.

The real working files, such as the full `FoodsFinal.xlsx`, generated translation review files, and CSV batches, are ignored by Git.

## Database Setup

Start MySQL and Adminer from the project root:

```powershell
docker compose -f infra/docker-compose.yml up -d
```

Default local database settings:

```text
host:     127.0.0.1
port:     3307
database: nutrition
user:     nutrition
password: nutritionpass
```

Adminer runs at:

```text
http://localhost:8080
```

## Backend Setup

Go to the backend folder:

```powershell
cd backend
```

Create and activate a virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install dependencies:

```powershell
pip install -r requirements.txt
```

Create the local backend environment file:

```powershell
Copy-Item .env.example .env
```

Apply database migrations:

```powershell
python scripts\apply_migrations.py
```

Run the backend:

```powershell
uvicorn app.main:app --reload
```

Backend URL:

```text
http://127.0.0.1:8000
```

FastAPI docs:

```text
http://127.0.0.1:8000/docs
```

## Frontend Setup

Go to the frontend folder:

```powershell
cd frontend
```

Install dependencies:

```powershell
npm install
```

Create the local frontend environment file:

```powershell
Copy-Item .env.local.example .env.local
```

Run the frontend:

```powershell
npm run dev
```

Frontend URL:

```text
http://localhost:3000
```

## Import The Sample Data

Make sure the database container is running and migrations have been applied first.

From the project root, run a dry-run import:

```powershell
python backend\scripts\import_data_db.py --excel backend\data\FoodsFinal_sample.xlsx --verbose
```

Dry-run means the script parses the Excel file and tests the SQL work, but rolls everything back at the end.

If the dry-run looks correct, commit the sample data into MySQL:

```powershell
python backend\scripts\import_data_db.py --excel backend\data\FoodsFinal_sample.xlsx --commit
```

The full local dataset can be imported the same way by changing the Excel path:

```powershell
python backend\scripts\import_data_db.py --excel backend\data\FoodsFinal.xlsx --commit
```

## Excel Import Notes

The import script reads the spreadsheet hierarchy as:

```text
Category -> Food group -> Food description
```

In the database, these map to:

```text
categories.name
subcategories.name
foods.food_description
```

If a food row should become its own food group, the Excel file can use:

```text
own_subcategory = TRUE
```

The helper script below can mark this automatically from bold Excel rows:

```powershell
python backend\scripts\mark_own_subcategories.py --input backend\data\FoodsFinal.xlsx --output backend\data\FoodsFinal_marked.xlsx
```

### Below-Limit Nutrient Values

Excel nutrient markers such as `<1`, `<.1`, `<.01`, `trace`, `t`, and `tr`
are stored as numeric `0` so the calculator can keep doing simple arithmetic.
The original marker is preserved in `foods.nutrient_value_notes`, so the UI can
show the source value instead of displaying it as an exact zero.

Empty values and `-` are treated as missing values, not as zero.

## Romanian Translation Workflow

The project supports Romanian text columns:

```text
categories.name_ro
subcategories.name_ro
foods.food_description_ro
```

The migration files are:

```text
backend/migrations/000_initial_schema.sql
backend/migrations/001_add_ro_columns.sql
backend/migrations/002_add_nutrient_value_notes.sql
```

Typical translation workflow:

```powershell
python backend\scripts\translation\export_translation_review.py
```

Export a CSV batch for ChatGPT/manual translation:

```powershell
python backend\scripts\translation\export_chatgpt_batch.py --sheet food_descriptions --limit 1000 --output backend\data\food_descriptions_ro_batch.csv
```

Import the translated CSV back into the review workbook:

```powershell
python backend\scripts\translation\import_chatgpt_batch.py --batch backend\data\food_descriptions_ro_batch.csv --output backend\data\translation_review_with_suggestions.xlsx --approve
```

Import approved translations into the database:

```powershell
python backend\scripts\translation\import_translation_review_db.py --input backend\data\translation_review_with_suggestions.xlsx --statuses approved needs_review --commit
```

Apply translations back to the Excel data file:

```powershell
python backend\scripts\translation\apply_translations_to_foods_final.py --review backend\data\translation_review_with_suggestions.xlsx --input backend\data\FoodsFinal.xlsx --output backend\data\FoodsFinal_with_ro.xlsx
```

## Application Pages

```text
/
```

Home page.

```text
/foods
```

Food browser page.

```text
/calculator
```

Meal nutrition calculator.

```text
/admin/add-food
```

Local admin page for adding a food item. It is not linked in the main navigation.
When using it, enter the `ADMIN_TOKEN` value from `backend/.env`.

## Environment Files

Example environment files are committed:

```text
backend/.env.example
frontend/.env.local.example
```

Real local environment files are ignored:

```text
backend/.env
frontend/.env.local
```

This keeps database credentials, admin tokens, and local machine settings out of Git.

Admin tokens must stay server/local only. Do not expose them with a
`NEXT_PUBLIC_` prefix in frontend environment files.

## Git Ignore Policy

The repository ignores:

- Python virtual environments.
- Node dependencies.
- Next.js build output.
- local environment files.
- private Excel and CSV data files.
- generated translation workbooks.
- Python cache files.

The sample dataset is explicitly allowed:

```text
!backend/data/FoodsFinal_sample.xlsx
```

## Useful Commands

Start database:

```powershell
docker compose -f infra/docker-compose.yml up -d
```

Apply migrations:

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
python scripts\apply_migrations.py
```

Stop database:

```powershell
docker compose -f infra/docker-compose.yml down
```

Run backend:

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload
```

Run frontend:

```powershell
cd frontend
npm run dev
```

Build frontend:

```powershell
cd frontend
npm run build
```

Run backend smoke test:

```powershell
python backend\scripts\smoke_test.py
```

Run backend smoke test plus frontend build:

```powershell
python backend\scripts\smoke_test.py --with-frontend-build
```

## Project Status

This project is in active development.

Current focus:

- improving food data quality;
- keeping the import workflow reliable;
- improving Romanian translations;
- improving the calculator and food browser UX;
- preparing the project for public GitHub presentation.

## Author

Created by **Marian Radu**.

GitHub:

```text
https://github.com/MarianRadu27/nutrition-data-platform
```

LinkedIn:

```text
https://www.linkedin.com/in/ioan-marian-radu/
```
