# Meal Nutrition Calculator

A full-stack nutrition web application built with **FastAPI**, **MySQL** and **Next.js**.

The application allows users to search food items, calculate nutritional values for meals and manage food data through an admin interface.

## Overview

This project is a practical full-stack application focused on nutrition data management and meal nutrition calculation.

The main goal is to provide a simple and reliable way to:

- search foods from a MySQL database;
- calculate nutrition values based on selected foods and quantities;
- manage food entries from an admin page;
- expose backend functionality through a FastAPI REST API;
- display the application through a Next.js frontend.

## Tech Stack

### Backend

- Python
- FastAPI
- MySQL
- Pydantic
- Uvicorn

### Frontend

- Next.js
- React
- TypeScript

### Infrastructure

- Docker Compose
- MySQL container

## Project Structure

```text
nutrition-project/
│
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── db.py
│   │   ├── repositories.py
│   │   ├── schemas.py
│   │   └── __init__.py
│   │
│   ├── migrations/
│   │   └── 001_add_ro_columns.sql
│   │
│   ├── scripts/
│   │   ├── import_tabel_alim.py
│   │   └── translation/
│   │       ├── glossary_ro.csv
│   │       └── translate_foods_step1.py
│   │
│   ├── .env.example
│   ├── requirements.txt
│   └── requirements-freeze.txt
│
├── frontend/
│   ├── app/
│   │   ├── admin/
│   │   │   └── add-food/
│   │   │       └── page.tsx
│   │   ├── calculator/
│   │   │   └── page.tsx
│   │   ├── foods/
│   │   │   └── page.tsx
│   │   ├── layout.tsx
│   │   └── page.tsx
│   │
│   ├── .env.local.example
│   ├── package.json
│   ├── package-lock.json
│   ├── tsconfig.json
│   └── next-env.d.ts
│
├── infra/
│   └── docker-compose.yml
│
├── .gitignore
└── README.md
```

## Features

### Food Search

Users can search for food items stored in the PostgreSQL database.

### Meal Nutrition Calculator

Users can select multiple foods and enter quantities in grams.

The backend calculates nutritional totals for the selected meal items.

### Admin Food Management

The frontend includes an admin page for adding food items.

### Romanian Translation Support

The backend contains scripts and glossary files used for translating food descriptions into Romanian.

### Database Migration Support

The project includes SQL migration files for database updates.

## Backend Setup

### 1. Go to the backend folder

```bash
cd backend
```

### 2. Create a virtual environment

On Windows:

```bash
python -m venv .venv
```

### 3. Activate the virtual environment

On Windows PowerShell:

```bash
.\.venv\Scripts\Activate.ps1
```

On Windows Command Prompt:

```bash
.\.venv\Scripts\activate.bat
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

### 5. Configure environment variables

Create a `.env` file inside the `backend` folder using `.env.example` as a reference.

Example:

```bash
cp .env.example .env
```

On Windows, the file can also be copied manually.

Make sure the database connection values match your PostgreSQL setup.

### 6. Run the backend server

```bash
uvicorn app.main:app --reload
```

The backend should run at:

```text
http://127.0.0.1:8000
```

FastAPI interactive documentation should be available at:

```text
http://127.0.0.1:8000/docs
```

## Frontend Setup

### 1. Go to the frontend folder

```bash
cd frontend
```

### 2. Install dependencies

```bash
npm install
```

### 3. Configure environment variables

Create a `.env.local` file using `.env.local.example` as a reference.

Example:

```bash
cp .env.local.example .env.local
```

Make sure the frontend API URL points to the backend server.

Example:

```env
NEXT_PUBLIC_API_URL=http://127.0.0.1:8000
```

### 4. Run the frontend development server

```bash
npm run dev
```

The frontend should run at:

```text
http://localhost:3000
```

## Database Setup

The project includes a Docker Compose configuration inside the `infra` folder.

From the project root, run:

```bash
docker compose -f infra/docker-compose.yml up -d
```

This starts the PostgreSQL database container.

After the database is running, make sure the backend `.env` file contains the correct database connection details.

## Useful Commands

### Run backend

```bash
cd backend
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload
```

### Run frontend

```bash
cd frontend
npm run dev
```

### Start database

```bash
docker compose -f infra/docker-compose.yml up -d
```

### Stop database

```bash
docker compose -f infra/docker-compose.yml down
```

## API Documentation

When the backend is running, FastAPI automatically provides interactive API documentation at:

```text
http://127.0.0.1:8000/docs
```

This can be used to inspect and test the available API endpoints.

## Current Application Pages

The frontend currently includes:

```text
/
```

Main application page.

```text
/foods
```

Food search page.

```text
/calculator
```

Meal nutrition calculator page.

```text
/admin/add-food
```

Admin page for adding new food items.

## Data Import and Translation Scripts

The backend includes utility scripts for working with food data.

```text
backend/scripts/import_tabel_alim.py
```

Used for importing food data into the database.

```text
backend/scripts/translation/translate_foods_step1.py
```

Used as part of the Romanian translation workflow.

```text
backend/scripts/translation/glossary_ro.csv
```

Glossary file used for Romanian nutrition-related translations.

## Environment Files

This project uses example environment files:

```text
backend/.env.example
frontend/.env.local.example
```

Actual environment files are ignored by Git:

```text
backend/.env
frontend/.env.local
```

This prevents sensitive information such as database credentials or local configuration values from being committed to the repository.

## Git Ignore Policy

The repository ignores files and folders that should not be committed, such as:

- Python virtual environments;
- Node.js dependencies;
- local environment files;
- temporary build files;
- local operating system files;
- temporary spreadsheet files.

Examples:

```text
backend/.venv/
frontend/node_modules/
frontend/.next/
backend/.env
frontend/.env.local
```

## Project Status

This project is currently in development.

Current focus:

- improving the accuracy of nutrition calculations;
- cleaning and validating food data;
- stabilizing the backend API;
- improving frontend usability;
- preparing the project for public presentation on GitHub and LinkedIn.

## Future Improvements

Planned or possible improvements:

- improve validation for meal calculation inputs;
- handle missing or incomplete food weight data;
- add better error messages in the frontend;
- improve admin food management;
- add user-friendly loading and empty states;
- add automated tests for nutrition calculations;
- improve Romanian food descriptions;
- add deployment configuration;
- improve UI design and responsiveness.

## Why This Project Matters

This project demonstrates practical full-stack development skills, including:

- backend API development;
- database connection and PostgreSQL usage;
- frontend development with Next.js;
- environment configuration;
- Docker-based infrastructure;
- data import and processing;
- nutrition calculation logic;
- project organization and Git workflow.

## Author

Created by **Marian**.

GitHub:

```text
https://github.com/MarianRadu27/nutrition-project
```

LinkedIn:

```text
https://www.linkedin.com/in/ioan-marian-radu/
```
