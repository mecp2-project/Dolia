#!/usr/bin/env bash

set -e

# Ensure that the CWD is set to script's location
cd "${0%/*}"
CWD=$(pwd)

if ! command -v aws &> /dev/null
then
	echo "aws could not be found"
	echo "run:"
	echo "	brew install awscli"
	exit
fi

S3_BUCKET="mecp2-test"

echo "Will use bucket: $S3_BUCKET"

echo "If you see credentials error, run"
echo "	aws configure"

for directory in "angles" "categories" "clean" "peaks"
do
	aws s3 sync ../$directory s3://$S3_BUCKET/$directory/
	# if you want to "download" instead, change the order:
	# aws s3 sync s3://$S3_BUCKET/$directory/ ../$directory
done

echo "Done!"
