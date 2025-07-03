import json
import boto3
from datetime import datetime, timezone, timedelta

client = boto3.client('ec2')

def clean_up_elastic_ip():
    # Delete redundant eips that are not associated
    elastic_ip_response = client.describe_addresses()
    for addresses in elastic_ip_response['Addresses']:
        public_ip=addresses['PublicIp']
        allocation_id=addresses['AllocationId']
        association_id = addresses.get('AssociationId')

        if not association_id:
            print(F"Elastic IP {public_ip} is not associated with any instance")
            print(F"Releasing Elastic IP {public_ip}")
            try:
                client.release_address(AllocationId=allocation_id)
                print(F"Released Elastic IP {public_ip}")
            except Exception as e:
                print(F"Error releasing Elastic IP {public_ip} : {e}")
        else:
            print(F"Elastic IP {public_ip} is associated with an instance")

def clean_up_stale_snapshots():
    warn_snapshots = []
    paginator = client.get_paginator('describe_snapshots')
    page_iterator = paginator.paginate(OwnerIds=['self'])
    threshold_days=30
    current_time = datetime.now(timezone.utc)
    total_GB_saved=0

    for page in page_iterator:
        for snapshot in page['Snapshots']:
            snapshot_id = snapshot['SnapshotId']
            snapshot_time = snapshot['StartTime']
            snapshot_size = snapshot['VolumeSize']
            age = (current_time - snapshot_time).days
            if age >= threshold_days:
                print(F"Snapshot {snapshot_id} is older than {threshold_days} days")
                print(F"Deleting snapshot {snapshot_id}")
                try:
                    client.delete_snapshot(SnapshotId=snapshot_id)
                    total_GB_saved+=snapshot_size
                    print(F"Deleted snapshot {snapshot_id} of size {snapshot_size}")
                except Exception as e:
                    print(F"Error deleting snapshot {snapshot_id} : {e}")
            elif age in [28,29]:
                days_left = threshold_days - age
                warn_snapshots.append((snapshot_id, age, days_left))

    if warn_snapshots:
        print("\n⏳ Snapshots close to deletion:")
        for snap_id, age, days_left in warn_snapshots:
            print(F"Snapshot {snap_id}  will be deleted in {days_left}")

    print(F"Total GB saved: {total_GB_saved}")

def clean_up_redundant_volumes():
    paginator = client.get_paginator('describe_volumes')
    page_iterator = paginator.paginate()
    threshold_days=30
    current_time = datetime.now(timezone.utc)
    total_GB_saved=0
    warn_volumes_with_retain=[]

    for page in page_iterator:
        for volume in page['Volumes']:
            volume_id = volume['VolumeId']
            volume_size = volume['Size']
            volume_creation_time = volume['CreateTime']
            volume_tags = volume.get('Tags', [])
            volume_in_use=volume.get('state')
            age_days = (current_time - volume_creation_time).days
            if volume_in_use == 'in-use':
                continue
            elif volume_tags:
                tag_dict = {tag['Key']: tag['Value'] for tag in volume_tags}  # Convert to dict
                if 'Retain' in tag_dict and tag_dict['Retain'] == 'true':
                    if 'Days' in tag_dict:
                        days_to_retain = int(tag_dict['Days'])
                        if  days_to_retain == -1:
                            continue
                        elif age_days >= days_to_retain:
                            print(F"Volume {volume_id} is older than {days_to_retain} days")
                            print(F"Deleting volume {volume_id}")
                            try:
                                client.delete_volume(VolumeId=volume_id)
                                total_GB_saved+=volume_size
                                print(F"Deleted volume {volume_id} of size {volume_size}")
                            except Exception as e:
                                print(F"Error deleting volume {volume_id} : {e}")
                        elif (days_to_retain-age_days) <=2:
                            days_left = days_to_retain - age_days
                            warn_volumes_with_retain.append((volume_id, age_days, days_left))
                    else:
                        print(F"Volume {volume_id} has 'Retain' tag but no 'Days' tag")
                        print(F"Deleteing Retain tag from volume={volume_id}")
                        client.delete_tags(Resources=[volume_id], Tags=[{'Key': 'Retain'}])
            
            elif age_days>=threshold_days:
                print(F"Volume {volume_id} has no tags")
                print(F"Volume {volume_id} is older than {threshold_days} days")
                print(F"Deleting volume {volume_id}")
                try:
                    client.delete_volume(VolumeId=volume_id)
                    total_GB_saved+=volume_size
                    print(F"Deleted volume {volume_id} of size {volume_size}")
                except Exception as e:
                    print(F"Error deleting volume {volume_id} : {e}")
    
    if warn_volumes_with_retain:
        print("\n⏳ Volumes close to deletion:")
        for vol_id, age_days, days_left in warn_volumes_with_retain:
            print(F"Volume {vol_id}  will be deleted in {days_left}")

    print(F"Total GB saved: {total_GB_saved}")

def lambda_handler(event, context):
    
    print("Deleting redundant resources")
    print("Deleting stale elastic IPs")
    clean_up_elastic_ip()
    print("Deleting stale snapshots")
    clean_up_stale_snapshots()
    print("Deleting redundant volumes")
    clean_up_redundant_volumes()
    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }
