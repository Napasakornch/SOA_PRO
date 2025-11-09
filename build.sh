# สร้าง build.sh
echo '#!/usr/bin/env bash

echo "Installing dependencies..."
pip install -r requirements.txt

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Running migrations..."
python manage.py migrate

echo "Build completed successfully!"' > build.sh

# ทำให้ build.sh สามารถ execute ได้
chmod +x build.sh