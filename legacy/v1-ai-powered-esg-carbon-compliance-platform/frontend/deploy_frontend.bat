@echo off
set BUCKET_NAME=carbon-auditor-frontend-%RANDOM%
set REGION=us-east-1

echo Creating S3 bucket: %BUCKET_NAME%
aws s3api create-bucket --bucket %BUCKET_NAME% --region %REGION%

echo Disabling Block Public Access (required for static websites)...
aws s3api put-public-access-block --bucket %BUCKET_NAME% --public-access-block-configuration "BlockPublicAcls=false,IgnorePublicAcls=false,BlockPublicPolicy=false,RestrictPublicBuckets=false"

echo Enabling Static Website Hosting...
aws s3 website s3://%BUCKET_NAME%/ --index-document dashboard.html

echo Applying Public Read Policy...
echo { "Version": "2012-10-17", "Statement": [ { "Sid": "PublicReadGetObject", "Effect": "Allow", "Principal": "*", "Action": "s3:GetObject", "Resource": "arn:aws:s3:::%BUCKET_NAME%/*" } ] } > bucket-policy.json
aws s3api put-bucket-policy --bucket %BUCKET_NAME% --policy file://bucket-policy.json
del bucket-policy.json

echo Uploading Frontend Files to S3...
aws s3 sync . s3://%BUCKET_NAME%/ --exclude "deploy_frontend.bat" --exclude "deploy_frontend.sh"

echo =========================================================
echo DEPLOYMENT COMPLETE!
echo Your website is now live at:
echo http://%BUCKET_NAME%.s3-website-%REGION%.amazonaws.com/
echo =========================================================
pause
