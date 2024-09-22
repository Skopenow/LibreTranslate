#!/bin/sh
if [ -z "${AWS_LAMBDA_RUNTIME_API}" ]; then
    exec ~/.aws-lambda-rie/aws-lambda-rie /app/venv/bin/python -m awslambdaric $1
else
    exec /app/venv/bin/python -m awslambdaric $1
fi