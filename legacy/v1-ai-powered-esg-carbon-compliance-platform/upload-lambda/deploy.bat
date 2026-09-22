@echo off
set LAMBDA_NAME=carbon-upload

echo Zipping upload lambda function...
tar -a -c -f upload.zip lambda_function.py

echo Deploying to AWS Lambda (%LAMBDA_NAME%)...
aws lambda update-function-code --function-name %LAMBDA_NAME% --zip-file fileb://upload.zip

echo Deployment complete!
pause
