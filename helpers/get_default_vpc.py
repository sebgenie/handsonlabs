def get_default_vpc_id(ec2_client:object) -> dict : 
    list_vpcs =  ec2_client.describe_vpcs()
    vpc_id = {}
    # print(list_vpcs['Vpcs'])

    list_vpcs = list_vpcs['Vpcs']
    for i in range(0, len(list_vpcs)):
        if list_vpcs[i]['IsDefault']== True:
            vpc_id = list_vpcs[i]['VpcId']
    
    return vpc_id