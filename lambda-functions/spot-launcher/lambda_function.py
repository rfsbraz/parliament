import json
import boto3
import os
import base64
import logging

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    """
    Lambda function to launch spot instances for parliament data import
    """
    try:
        # Get configuration from environment variables
        import_mode = os.environ.get('IMPORT_AUTOMATION_MODE', 'manual')
        instance_type = os.environ.get('SPOT_INSTANCE_TYPE', 't3.nano')
        timeout_minutes = int(os.environ.get('IMPORT_TIMEOUT_MINUTES', '30'))
        
        logger.info(f"Starting spot instance launcher with mode: {import_mode}")
        
        if import_mode == 'disabled':
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'message': 'Import automation is disabled',
                    'mode': import_mode
                })
            }
        
        # Initialize EC2 client
        ec2 = boto3.client('ec2')
        
        # Create user data script for the spot instance
        user_data_script = f"""#!/bin/bash
# Parliament Data Import Script
yum update -y
yum install -y python3 python3-pip git postgresql15

# Set environment variables
export PYTHONPATH="/parliament"
export DATABASE_SECRET_ARN="{os.environ.get('DATABASE_SECRET_ARN', '')}"
export IMPORT_TIMEOUT_MINUTES="{timeout_minutes}"

# Log everything
exec > >(tee /var/log/parliament-import.log)
exec 2>&1

echo "Starting Parliament data import at $(date)"
echo "Instance type: {instance_type}"
echo "Timeout: {timeout_minutes} minutes"

# Install dependencies
pip3 install boto3 psycopg2-binary requests beautifulsoup4 lxml sqlalchemy

# Clone or update parliament repository (replace with your actual repo)
cd /
if [ ! -d "parliament" ]; then
    echo "Repository setup would go here"
    echo "For now, creating placeholder import script"
fi

# Run the import with timeout
timeout {timeout_minutes}m python3 -c "
import boto3
import json
import time
import os

def get_database_credentials():
    secret_arn = os.environ.get('DATABASE_SECRET_ARN')
    if not secret_arn:
        print('No database secret ARN provided')
        return None
    
    try:
        client = boto3.client('secretsmanager')
        response = client.get_secret_value(SecretId=secret_arn)
        return json.loads(response['SecretString'])
    except Exception as e:
        print(f'Error getting credentials: {{e}}')
        return None

print('Parliament data import placeholder')
print('Database credentials check:', 'OK' if get_database_credentials() else 'FAILED')
print('Import would run here...')
time.sleep(10)  # Simulate work
print('Import completed successfully')
"

# Signal completion and shutdown
echo "Parliament data import completed at $(date)"
shutdown -h now
"""
        
        # Encode user data
        user_data_encoded = base64.b64encode(user_data_script.encode()).decode()
        
        # Launch configuration
        launch_config = {
            'ImageId': 'ami-0e9799f4d991f9aa0',  # Amazon Linux 2023
            'InstanceType': instance_type,
            'UserData': user_data_encoded,
            'SecurityGroupIds': [os.environ.get('SECURITY_GROUP_ID', '')],
            'SubnetId': os.environ.get('SUBNET_ID', ''),
            'IamInstanceProfile': {
                'Name': os.environ.get('IAM_INSTANCE_PROFILE', '')
            },
            'TagSpecifications': [
                {
                    'ResourceType': 'instance',
                    'Tags': [
                        {'Key': 'Name', 'Value': 'parliament-data-import'},
                        {'Key': 'Project', 'Value': 'Parliament'},
                        {'Key': 'Purpose', 'Value': 'automated-data-import'},
                        {'Key': 'AutoTerminate', 'Value': 'true'}
                    ]
                }
            ]
        }
        
        # Request spot instance
        response = ec2.request_spot_instances(
            SpotPrice='0.01',  # Max price for t3.nano
            InstanceCount=1,
            LaunchSpecification=launch_config
        )
        
        spot_request_id = response['SpotInstanceRequests'][0]['SpotInstanceRequestId']
        
        logger.info(f"Spot instance requested: {spot_request_id}")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Spot instance launch initiated',
                'spotRequestId': spot_request_id,
                'instanceType': instance_type,
                'timeoutMinutes': timeout_minutes,
                'mode': import_mode
            })
        }
        
    except Exception as e:
        logger.error(f"Error launching spot instance: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': 'Failed to launch spot instance',
                'message': str(e)
            })
        }