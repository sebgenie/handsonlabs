import json
import time

from helpers.get_session import assumed_role_session
from helpers.create_sg import sg_id, authorize_port_of_sg
from helpers.iam_role import create_role, attach_manage_permission


def create_ec2() -> dict:
    
    #create security group
    with open('config_file.json') as cf:
        json_file = json.load(cf)
        role_name = json_file['role_name']
        instance_profile_name = json_file['instance_profile_name']
        credentials = json_file['credentials']
        
        session = assumed_role_session(role_arn=json_file['assume_role_arn'])
        ec2_client = session.client('ec2')
        iam_client = session.client('iam')
        
        security_group_id = sg_id(
            ec2_client = ec2_client,
            groupe_name = json_file['security_group'])
        
        authorize_port_of_sg(
            ec2_client = ec2_client,
            security_group_id=security_group_id
            )
        
        # create role and add permissions
        
        create_role(
            iam_client=iam_client,
            iam_role_name=role_name)
        
        attach_manage_permission(
            iam_client=iam_client,
            role_name=role_name,
            arn='arn:aws:iam::aws:policy/AmazonEC2FullAccess' 
        ) 
        
        # create instance profile
        instance_profile_response = iam_client.create_instance_profile(
            InstanceProfileName=instance_profile_name,
        )
        
        waiter = iam_client.get_waiter('instance_profile_exists')
        waiter.wait(
            InstanceProfileName=instance_profile_name,
            WaiterConfig={
                'Delay': 123,
                'MaxAttempts': 123
            }
        )

        # attach role to instance profile
        attach_role_response = iam_client.add_role_to_instance_profile(
            InstanceProfileName=instance_profile_name,
            RoleName=role_name
        )
        
        time.sleep(120)
        
        # define user data
        user_data = f"""#!/bin/bash
        if grep -wq "PasswordAuthentication no" /etc/ssh/sshd_config; then 
            sed 's/PasswordAuthentication no/PasswordAuthentication yes/' -i /etc/ssh/sshd_config
        else
            "PasswordAuthentication yes" >> /etc/ssh/sshd_config
        fi
        systemctl restart sshd
        service sshd restart

        #TODO: replace <user_test> with your desired username
        useradd {credentials['user_test']}
        # TODO: replace password with desired password and change <user_test> to your username chosen in useradd 
        echo "{credentials['password']}" | passwd --stdin {credentials['user_test']}

        """

        instance_params = {
                   
                "BlockDeviceMappings":[
                    {
                        'DeviceName': '/dev/xvda',
                        'Ebs': {

                            'DeleteOnTermination': True,
                            'VolumeSize': 8,
                            'VolumeType': 'gp2'
                        },
                    },
                ],
                "ImageId": json_file['ami'],
                "InstanceType":'t2.micro',
                "MaxCount":1,
                "MinCount":1,
                "Monitoring":{
                    'Enabled': False
                },
                "SecurityGroupIds":[
                    security_group_id,
                ],
                "DryRun":json_file['dry_run'],
                'UserData': user_data,
                "IamInstanceProfile": {'Name': json_file['instance_profile_name']}
        }
        instance = ec2_client.run_instances(**instance_params)
        instance_id = instance["Instances"][0]["InstanceId"]
        
        waiter = ec2_client.get_waiter('instance_running')
        waiter.wait(
            InstanceIds=[
                        instance_id,
                    ],
            WaiterConfig={
                'Delay': 123,
                'MaxAttempts': 123
            }
        )
    
        response = ec2_client.describe_instances(
                    InstanceIds=[
                        instance_id,
                    ]
                    )
        time.sleep(120)
        public_ip_address = response['Reservations'][0]['Instances'][0]['PublicIpAddress']
        print("\n**** PublicIpAddress: ", public_ip_address)
        # print('\n****', instance)
        print('\n****', credentials)
        
        return {'public_ip_address': public_ip_address, 'credentials': credentials}
        
    
    

def lambda_handler(event, context):
    result = create_ec2()
    
    response = {'result': result}
    
    return response


if __name__ == "__main__":
    event = None
    context = None
    lambda_handler(event=event, context=context)