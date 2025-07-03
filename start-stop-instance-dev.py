import json
import boto3
client = boto3.client('ec2')

def get_instance_ids(tags: dict, instance_state):
    filter=[]
    for key, value in tags.items():
        filter.append(
            {
                'Name': f'tag:{key}',
                'Values': [value]
            }
        )
        filter.append(
            {
                'Name': 'instance-state-name',
                'Values': [instance_state]
            }
        )

    response = client.describe_instances(
        Filters=filter  
    )
    instance_ids=[]
    for reservation in response['Reservations']:
        for instance in reservation['Instances']:
            instance_ids.append(instance['InstanceId'])
    return instance_ids

def start_ec2_instance():
    tags={'AutoSchedule':'true', 'Env':'Dev'}
    instances= get_instance_ids(tags, 'stopped')

    if instances:
        client.start_instances(
            InstanceIds=instances
        )
        print(F"starting ec2 instances: {instances}")
    else:
        print("no instances to start")
    

def stop_ec2_instance():
    tags={'AutoSchedule':'true', 'Env':'Dev'}
    instances = get_instance_ids(tags, 'running')
    print(instances)
    if instances:
        client.stop_instances(
            InstanceIds=instances
        )
        print(F"stopping ec2 instances: {instances}")
    else:
        print("no instances to stop")


def lambda_handler(event, context):
    # TODO implement
    action=event.get('action','stop')
    if action=='start':
        print('starting ec2 instances')
        start_ec2_instance()
    elif action=='stop':
        print('stopping ec2 instances')
        stop_ec2_instance()
    else:
        print('unknown action')
    return {
        'statusCode': 200,
        'body': json.dumps('Executed Successfully')
    }
