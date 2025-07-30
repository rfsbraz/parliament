# Serverless Flask with Aurora Serverless v2 using AWS Lambda Web Adapter
FROM public.ecr.aws/lambda/python:3.12

# Install Lambda Web Adapter
COPY --from=public.ecr.aws/awsguru/aws-lambda-adapter:0.8.1 /lambda-adapter ${LAMBDA_RUNTIME_DIR}

# Copy application code (NO embedded database)
COPY app/ ${LAMBDA_TASK_ROOT}/app/
COPY config/ ${LAMBDA_TASK_ROOT}/config/
COPY requirements.txt ${LAMBDA_TASK_ROOT}/

# Install dependencies + MySQL client
RUN pip install -r requirements.txt gunicorn pymysql cryptography

# Environment variables for Lambda Web Adapter
ENV AWS_LWA_INVOKE_MODE=response_stream
ENV AWS_LWA_PORT=8000
ENV PYTHONPATH=${LAMBDA_TASK_ROOT}

# Database configuration for Aurora
ENV DATABASE_TYPE=mysql
ENV DATABASE_HOST_SECRET_ARN=""  # Will be set by Terraform
ENV DATABASE_NAME=parliament

# Your Flask app runs exactly as before, but connects to Aurora!
CMD ["python", "-m", "gunicorn", "--bind", "0.0.0.0:8000", "app.main:app"]