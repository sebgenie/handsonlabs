import json
from botocore.exceptions import ClientError
from helpers.get_session import assumed_role_session



def create_role(iam_client:object, iam_role_name:str = 'test_role_ec2'):
    
    try:
        response = iam_client.create_role(
                        RoleName=iam_role_name,
                        AssumeRolePolicyDocument='{   "Version": "2012-10-17",   "Statement": [     {       "Effect": "Allow",       "Principal": {         "Service": "ec2.amazonaws.com"       },       "Action": "sts:AssumeRole"     }   ] }'
            )
        print("*** Role is created ***", response)
    except ClientError as e:
        print(e)


def  attach_manage_permission(iam_client:object, role_name:str, arn:str):
    try:
        response = iam_client.attach_role_policy(
                    RoleName=role_name, 
                    PolicyArn=arn
                    )
    except ClientError as e:
        print(e)
    print("*** permission is attached ***", response)


if __name__ == '__main__':
    role_name = "test_role"

    with open('scripts/config_file.json') as cf:
        json_file = json.load(cf)
        
        session = assumed_role_session(json_file['assume_role_arn'])
        iam_client = session.client('iam')

        create_role(
            iam_client=iam_client,
            iam_role_name=role_name)
        
        attach_manage_permission(
            iam_client=iam_client,
            role_name=role_name,
            arn='arn:aws:iam::aws:policy/AmazonEC2ReadOnlyAccess' 
        ) 