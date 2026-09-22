@echo off
echo Cleaning up previous builds...
if exist package rmdir /s /q package
if exist chat.zip del chat.zip

echo Creating package directory...
mkdir package

echo Installing dependencies for Amazon Linux (using Python 3.12 explicitly)...
py -3.12 -m pip install --platform manylinux2014_x86_64 --target=package --implementation cp --python-version 3.12 --only-binary=:all: --upgrade -r requirements.txt

echo Applying AWS Lambda namespace package fix...
if exist package\google\__init__.py del package\google\__init__.py

echo Removing unused files and __pycache__...
for /d /r package %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d"
del /q /s package\*.pyc

echo Copying source files...
copy lambda_function.py package\
copy services.py package\
copy utils.py package\

echo Zipping package...
cd package
powershell -Command "Compress-Archive -Path * -DestinationPath ..\chat.zip -Force"
cd ..

echo Cleaning up...
rmdir /s /q package

echo Deployment package chat.zip generated successfully for Amazon Linux 2023.
