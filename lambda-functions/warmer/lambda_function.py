import json
import urllib3
import os
import logging

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    """
    Lambda function to keep the main backend Lambda warm
    """
    try:
        # Get the Lambda Function URL from environment
        function_url = os.environ.get('BACKEND_FUNCTION_URL', '')
        
        if not function_url:
            logger.warning("No BACKEND_FUNCTION_URL provided")
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'error': 'No backend function URL configured'
                })
            }
        
        # Create HTTP client
        http = urllib3.PoolManager()
        
        # Make a request to the health endpoint
        health_url = f"{function_url.rstrip('/')}/api/health"
        
        logger.info(f"Warming up backend at: {health_url}")
        
        # Make the request
        response = http.request('GET', health_url, timeout=10)
        
        # Parse response
        if response.status == 200:
            response_data = json.loads(response.data.decode('utf-8'))
            logger.info(f"Backend warmed successfully: {response_data.get('status', 'unknown')}")
            
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'message': 'Backend warmed successfully',
                    'backend_status': response_data.get('status', 'unknown'),
                    'backend_service': response_data.get('service', 'unknown'),
                    'timestamp': context.aws_request_id
                })
            }
        else:
            logger.warning(f"Backend health check failed with status: {response.status}")
            return {
                'statusCode': 502,
                'body': json.dumps({
                    'error': 'Backend health check failed',
                    'status_code': response.status,
                    'timestamp': context.aws_request_id
                })
            }
            
    except Exception as e:
        logger.error(f"Error warming backend: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': 'Failed to warm backend',
                'message': str(e),
                'timestamp': context.aws_request_id
            })
        }