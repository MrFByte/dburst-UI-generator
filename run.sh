#!/bin/bash

# Navigate to backend directory,Activate backend virtual environment and run Django server
echo "Starting backend server..."
cd backend
source .venv_dburst/bin/activate
python manage.py runserver &

# Navigate to frontend directory and run development server
echo "Starting frontend server..."
cd dburst-frontend
npm run dev