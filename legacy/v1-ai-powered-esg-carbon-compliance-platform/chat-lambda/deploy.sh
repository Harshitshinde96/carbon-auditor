#!/bin/bash
echo "Cleaning up previous builds..."
rm -rf package chat.zip

echo "Creating package directory..."
mkdir package

echo "Installing dependencies for Amazon Linux..."
pip3.12 install --platform manylinux2014_x86_64 --target=package --implementation cp --python-version 3.12 --only-binary=:all: --upgrade -r requirements.txt

echo "Applying AWS Lambda namespace package fix..."
rm -f package/google/__init__.py

echo "Removing __pycache__..."
find package -type d -name "__pycache__" -exec rm -rf {} +

echo "Copying source files..."
cp lambda_function.py package/
cp services.py package/
cp utils.py package/

echo "Zipping package..."
cd package
zip -r ../chat.zip .
cd ..

echo "Cleaning up..."
rm -rf package

echo "Deployment package chat.zip generated successfully."
