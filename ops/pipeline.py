"""
Pipeline orchestration commands for Parliament Operations CLI.

Handles remote triggering of data import pipelines via Lambda/Spot instances.
"""

import json
import time
from datetime import datetime
from typing import Optional

import click

try:
    import boto3
    HAS_BOTO3 = True
except ImportError:
    HAS_BOTO3 = False

try:
    import urllib.request
    import urllib.error
    HAS_URLLIB = True
except ImportError:
    HAS_URLLIB = False

from .config import get_config, Config


def invoke_lambda_url(url: str, payload: dict) -> dict:
    """Invoke Lambda function via Function URL."""
    if not HAS_URLLIB:
        raise click.ClickException("urllib not available")

    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(url, data=data, method='POST')
    req.add_header('Content-Type', 'application/json')

    try:
        with urllib.request.urlopen(req, timeout=120) as response:
            return json.loads(response.read().decode())
    except urllib.error.HTTPError as e:
        error_body = e.read().decode()
        raise click.ClickException(f"Lambda invocation failed: {e.code} - {error_body}")
    except urllib.error.URLError as e:
        raise click.ClickException(f"Connection failed: {e.reason}")


def invoke_lambda_direct(function_name: str, payload: dict, region: str, profile: str = None) -> dict:
    """Invoke Lambda function directly via boto3."""
    if not HAS_BOTO3:
        raise click.ClickException("boto3 not installed. Run: pip install boto3")

    session = boto3.Session(profile_name=profile, region_name=region) if profile else boto3.Session(region_name=region)
    client = session.client('lambda')

    response = client.invoke(
        FunctionName=function_name,
        InvocationType='RequestResponse',
        Payload=json.dumps(payload)
    )

    response_payload = json.loads(response['Payload'].read())

    if response.get('FunctionError'):
        raise click.ClickException(f"Lambda error: {response_payload}")

    return response_payload


def get_spot_instance_status(instance_id: str, region: str, profile: str = None) -> dict:
    """Get status of a spot instance."""
    if not HAS_BOTO3:
        raise click.ClickException("boto3 not installed")

    session = boto3.Session(profile_name=profile, region_name=region) if profile else boto3.Session(region_name=region)
    ec2 = session.client('ec2')

    response = ec2.describe_instances(InstanceIds=[instance_id])

    if not response['Reservations']:
        return {'state': 'not_found'}

    instance = response['Reservations'][0]['Instances'][0]
    return {
        'state': instance['State']['Name'],
        'instance_id': instance_id,
        'instance_type': instance.get('InstanceType'),
        'launch_time': str(instance.get('LaunchTime')),
        'public_ip': instance.get('PublicIpAddress'),
    }


def get_cloudwatch_logs(log_group: str, log_stream_prefix: str, region: str, limit: int = 50, profile: str = None) -> list:
    """Get recent CloudWatch logs."""
    if not HAS_BOTO3:
        raise click.ClickException("boto3 not installed")

    session = boto3.Session(profile_name=profile, region_name=region) if profile else boto3.Session(region_name=region)
    logs = session.client('logs')

    try:
        # Find log streams
        streams_response = logs.describe_log_streams(
            logGroupName=log_group,
            orderBy='LastEventTime',
            descending=True,
            limit=5
        )

        if not streams_response.get('logStreams'):
            return []

        # Get events from the most recent stream
        stream_name = streams_response['logStreams'][0]['logStreamName']

        events_response = logs.get_log_events(
            logGroupName=log_group,
            logStreamName=stream_name,
            limit=limit,
            startFromHead=False
        )

        return [{
            'timestamp': datetime.fromtimestamp(e['timestamp'] / 1000).isoformat(),
            'message': e['message']
        } for e in events_response.get('events', [])]

    except Exception as e:
        click.echo(click.style(f"  Warning: Could not fetch logs: {e}", fg="yellow"))
        return []


def get_import_status(config: Config) -> dict:
    """Get import status from the API."""
    # Try to get status from the running API
    api_url = f"https://api.{config.domain_name}/api/admin/import-stats"

    try:
        req = urllib.request.Request(api_url, method='GET')
        with urllib.request.urlopen(req, timeout=10) as response:
            return json.loads(response.read().decode())
    except Exception:
        # Try localhost fallback
        try:
            req = urllib.request.Request("http://localhost:5000/api/admin/import-stats", method='GET')
            with urllib.request.urlopen(req, timeout=5) as response:
                return json.loads(response.read().decode())
        except Exception:
            return {}


@click.group()
def pipeline():
    """Remote pipeline orchestration commands."""
    pass


@pipeline.command()
@click.option('--mode', '-m', type=click.Choice(['discovery', 'importer', 'full']), default='full',
              help='Pipeline mode: discovery, importer, or full')
@click.option('--wait', '-w', is_flag=True, help='Wait for completion and show logs')
@click.option('--timeout', '-t', type=int, default=None, help='Override timeout in minutes')
@click.option('--production', '-p', is_flag=True, default=True, help='Run on production (default, spot instances)')
@click.option('--local', '-l', is_flag=True, help='Run locally instead of on spot instance')
def run(mode: str, wait: bool, timeout: Optional[int], production: bool, local: bool):
    """Start pipeline on EC2 Spot instance or locally."""
    config = get_config()

    # Handle local mode
    if local:
        click.echo(click.style(f"\n=== Starting Pipeline ({mode}) - LOCAL ===", fg="cyan", bold=True))
        click.echo("  Running pipeline locally...")

        import subprocess
        import sys

        if mode == 'discovery':
            script = "scripts/data_processing/discovery_service.py"
            args = ["--discover-all"]
        elif mode == 'importer':
            script = "scripts/data_processing/database_driven_importer.py"
            args = []
        else:
            click.echo("  Note: 'full' mode will run discovery first.")
            script = "scripts/data_processing/discovery_service.py"
            args = ["--discover-all"]

        try:
            result = subprocess.run(
                [sys.executable, script] + args,
                cwd=config.project_root,
                check=False
            )
            if result.returncode == 0:
                click.echo(click.style("\n  Pipeline completed successfully!", fg="green"))
            else:
                click.echo(click.style(f"\n  Pipeline exited with code {result.returncode}", fg="yellow"))
        except Exception as e:
            raise click.ClickException(f"Failed to run pipeline: {e}")
        return

    # Production mode (default) - run on spot instance
    click.echo(click.style(f"\n=== Starting Pipeline ({mode}) ===", fg="cyan", bold=True))
    click.echo(f"  Region: {config.aws.region}")
    click.echo(f"  Instance type: {config.pipeline.spot_instance_type}")
    click.echo(f"  Timeout: {timeout or config.pipeline.timeout_minutes} minutes")

    # Determine operation mode for Lambda
    if mode == 'full':
        # For full pipeline, we'll run discovery first, then importer
        click.echo("\n  Note: 'full' mode will run discovery. Run 'ops pipeline run -m importer' after discovery completes.")
        operation_mode = 'discovery'
    else:
        operation_mode = mode

    payload = {
        'mode': operation_mode,
        'source': 'ops-cli'
    }

    # Try Lambda Function URL first
    if config.pipeline.lambda_function_url:
        click.echo(f"\n  Invoking Lambda via Function URL...")
        try:
            result = invoke_lambda_url(config.pipeline.lambda_function_url, payload)
            body = json.loads(result.get('body', '{}')) if isinstance(result.get('body'), str) else result.get('body', {})
        except Exception as e:
            click.echo(click.style(f"  Function URL failed: {e}", fg="yellow"))
            click.echo("  Trying direct Lambda invocation...")
            function_name = f"fiscaliza-{config.environment}-spot-launcher"
            result = invoke_lambda_direct(function_name, payload, config.aws.region, config.aws.profile)
            body = json.loads(result.get('body', '{}')) if isinstance(result.get('body'), str) else result.get('body', {})
    else:
        # Direct Lambda invocation
        click.echo(f"\n  Invoking Lambda directly...")
        function_name = f"fiscaliza-{config.environment}-spot-launcher"
        result = invoke_lambda_direct(function_name, payload, config.aws.region, config.aws.profile)
        body = json.loads(result.get('body', '{}')) if isinstance(result.get('body'), str) else result.get('body', {})

    # Display result
    if 'error' in body:
        click.echo(click.style(f"\n  Error: {body['error']}", fg="red"))
        return

    click.echo(click.style("\n  Pipeline started successfully!", fg="green"))
    click.echo(f"  Spot Request ID: {body.get('spotRequestId', 'N/A')}")
    click.echo(f"  Instance ID: {body.get('instanceId', 'pending...')}")
    click.echo(f"  Operation Mode: {body.get('operationMode', operation_mode)}")

    instance_id = body.get('instanceId')

    # Wait for completion if requested
    if wait and instance_id:
        click.echo("\n  Waiting for completion (Ctrl+C to stop watching)...")
        try:
            while True:
                time.sleep(30)
                status = get_spot_instance_status(instance_id, config.aws.region, config.aws.profile)
                state = status.get('state', 'unknown')

                if state == 'running':
                    click.echo(f"    [{datetime.now().strftime('%H:%M:%S')}] Instance running...")
                elif state == 'terminated':
                    click.echo(click.style(f"    [{datetime.now().strftime('%H:%M:%S')}] Instance terminated (completed)", fg="green"))
                    break
                elif state == 'not_found':
                    click.echo(click.style(f"    [{datetime.now().strftime('%H:%M:%S')}] Instance not found", fg="yellow"))
                    break
                else:
                    click.echo(f"    [{datetime.now().strftime('%H:%M:%S')}] State: {state}")

        except KeyboardInterrupt:
            click.echo("\n  Stopped watching. Pipeline continues in background.")

    # Show how to check logs
    click.echo(f"\n  View logs: ops logs pipeline")
    click.echo(f"  Check status: ops pipeline status")


@pipeline.command()
@click.option('--wait', '-w', is_flag=True, help='Wait for completion')
@click.option('--production', '-p', is_flag=True, default=True, help='Run on production (default)')
@click.option('--local', '-l', is_flag=True, help='Run locally')
def discover(wait: bool, production: bool, local: bool):
    """Run discovery only (find new files on parliament.pt)."""
    ctx = click.get_current_context()
    ctx.invoke(run, mode='discovery', wait=wait, production=production, local=local)


@pipeline.command(name='import')
@click.option('--wait', '-w', is_flag=True, help='Wait for completion')
@click.option('--production', '-p', is_flag=True, default=True, help='Run on production (default)')
@click.option('--local', '-l', is_flag=True, help='Run locally')
def import_cmd(wait: bool, production: bool, local: bool):
    """Run import only (process discovered files)."""
    ctx = click.get_current_context()
    ctx.invoke(run, mode='importer', wait=wait, production=production, local=local)


@pipeline.command()
@click.option('--production', '-p', is_flag=True, default=True, help='Check production status (default)')
@click.option('--local', '-l', is_flag=True, help='Check local status')
def status(production: bool, local: bool):
    """Check pipeline and import status."""
    config = get_config()

    if local:
        click.echo(click.style("\n=== Pipeline Status (Local) ===", fg="cyan", bold=True))
        # Show local import statistics
        click.echo("\n  Import Statistics (Local):")
        stats = get_import_status(config)
        if stats:
            click.echo(f"    Total files: {stats.get('total', 'N/A')}")
            click.echo(f"    Completed: {stats.get('completed', 'N/A')}")
            click.echo(f"    Pending: {stats.get('pending', 'N/A')}")
            click.echo(f"    Failed: {stats.get('failed', 'N/A')}")
        else:
            click.echo("    Could not fetch import statistics (local API not reachable)")
        return

    click.echo(click.style("\n=== Pipeline Status ===", fg="cyan", bold=True))

    # Check for running spot instances
    if HAS_BOTO3:
        session = boto3.Session(profile_name=config.aws.profile, region_name=config.aws.region) if config.aws.profile else boto3.Session(region_name=config.aws.region)
        ec2 = session.client('ec2')

        try:
            response = ec2.describe_instances(
                Filters=[
                    {'Name': 'tag:Project', 'Values': ['Parliament']},
                    {'Name': 'tag:Purpose', 'Values': ['automated-data-import']},
                    {'Name': 'instance-state-name', 'Values': ['pending', 'running']}
                ]
            )

            instances = []
            for reservation in response.get('Reservations', []):
                for instance in reservation.get('Instances', []):
                    instances.append({
                        'id': instance['InstanceId'],
                        'state': instance['State']['Name'],
                        'type': instance.get('InstanceType'),
                        'launch_time': str(instance.get('LaunchTime')),
                    })

            if instances:
                click.echo("\n  Running Import Instances:")
                for inst in instances:
                    click.echo(f"    - {inst['id']}: {inst['state']} ({inst['type']}) - launched {inst['launch_time']}")
            else:
                click.echo("\n  No running import instances.")

        except Exception as e:
            click.echo(click.style(f"  Could not check EC2 instances: {e}", fg="yellow"))

    # Get import statistics from API
    click.echo("\n  Import Statistics:")
    stats = get_import_status(config)

    if stats:
        click.echo(f"    Total files: {stats.get('total', 'N/A')}")
        click.echo(f"    Completed: {stats.get('completed', 'N/A')}")
        click.echo(f"    Pending: {stats.get('pending', 'N/A')}")
        click.echo(f"    Failed: {stats.get('failed', 'N/A')}")
        click.echo(f"    Records imported: {stats.get('total_records', 'N/A')}")
    else:
        click.echo("    Could not fetch import statistics (API not reachable)")

    # Show recent logs
    click.echo("\n  Recent Log Entries:")
    logs = get_cloudwatch_logs(
        "/aws/parliament/import",
        "parliament-import",
        config.aws.region,
        limit=5,
        profile=config.aws.profile
    )

    if logs:
        for log in logs[-5:]:
            msg = log['message'][:80] + "..." if len(log['message']) > 80 else log['message']
            click.echo(f"    [{log['timestamp']}] {msg}")
    else:
        click.echo("    No recent logs available")
