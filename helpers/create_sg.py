import json 
from botocore.exceptions import ClientError
from helpers.get_default_vpc import get_default_vpc_id
from helpers.get_session import assumed_role_session


def sg_id(ec2_client:object, groupe_name:str = 'test1') -> str:

    vpc_id = get_default_vpc_id(ec2_client=ec2_client)
    
    try:
        # check if security group exist
        response = ec2_client.describe_security_groups(
            GroupNames=[
                groupe_name,
            ]
        )
    except Exception as e:
        if str(e).find(f"The security group {groupe_name} does not exist in") :
            response = ec2_client.create_security_group(
                Description='create sg',
                GroupName=groupe_name,
                VpcId=vpc_id
            )
        
        print('*** Security group is created ***: ', response)
        return response['GroupId']
    
    print('*** Security group already exist ***: ', response)

    response = response['SecurityGroups'][0]
            
    return response['GroupId']


def authorize_port_of_sg(ec2_client:object, security_group_id:str):
    try:
        data = ec2_client.authorize_security_group_ingress(
        GroupId=security_group_id,
        IpPermissions=[
            {'IpProtocol': 'tcp',
             'FromPort': 22,
             'ToPort': 22,
             'IpRanges': [{'CidrIp': '0.0.0.0/0'}]}
        ])

        print('Ingress Successfully Set %s' % data)

    except ClientError as e:
        print(e)


if __name__=='__main__':
    with open('config_file.json') as cf:
        json_file = json.load(cf)
        session = assumed_role_session(json_file['assume_role_arn'])
        authorize_port_of_sg(role_arn=json_file['assume_role_arn'], security_group_id=sg_id())