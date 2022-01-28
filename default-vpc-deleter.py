import argparse
import json
import boto3




def get_default_vpcs(client):
  vpc_list = []
  vpcs = client.describe_vpcs(
    Filters=[
      {
          'Name' : 'isDefault',
          'Values' : [
            'true',
          ],
      },
    ]
  )
  vpcs_str = json.dumps(vpcs)
  resp = json.loads(vpcs_str)
  data = json.dumps(resp['Vpcs'])
  vpcs = json.loads(data)
  
  for vpc in vpcs:
    vpc_list.append(vpc['VpcId'])  
  
  return vpc_list

def del_igw(ec2, vpcid):
  vpc_resource = ec2.Vpc(vpcid)
  igws = vpc_resource.internet_gateways.all()
  if igws:
    for igw in igws:
      try:
        print("Detaching and Removing igw: ", igw.id)
        igw.detach_from_vpc(
          VpcId=vpcid
        )
        igw.delete()
      except boto3.exceptions.Boto3Error as e:
        print(e)

def del_sub(ec2, vpcid):
  vpc_resource = ec2.Vpc(vpcid)
  subnets = vpc_resource.subnets.all()
  default_subnets = [ec2.Subnet(subnet.id) for subnet in subnets if subnet.default_for_az]
  
  if default_subnets:
    try:
      for sub in default_subnets: 
        print("Removing sub: ", sub.id)
        sub.delete()
    except boto3.exceptions.Boto3Error as e:
      print(e)

def del_rtb(ec2, vpcid):
  vpc_resource = ec2.Vpc(vpcid)
  rtbs = vpc_resource.route_tables.all()
  if rtbs:
    try:
      for rtb in rtbs:
        assoc_attr = [rtb.associations_attribute for rtb in rtbs]
        if [rtb_ass[0]['RouteTableId'] for rtb_ass in assoc_attr if rtb_ass[0]['Main'] == True]:
          print(rtb.id + " is the main route table, deleting.")
          continue
        print("Removing rtb: ", rtb.id)
        table = ec2.RouteTable(rtb.id)
        table.delete()
    except boto3.exceptions.Boto3Error as e:
      print(e)

def del_acl(ec2, vpcid):
    
  vpc_resource = ec2.Vpc(vpcid)      
  acls = vpc_resource.network_acls.all()

  if acls:
    try:
      for acl in acls: 
        if acl.is_default:
          print(acl.id + " is the default NACL, deleting.")
          continue
        print("Removing acl-id: ", acl.id)
        acl.delete()
    except boto3.exceptions.Boto3Error as e:
      print(e)

def del_sgp(ec2, vpcid):
  vpc_resource = ec2.Vpc(vpcid)
  sgps = vpc_resource.security_groups.all()
  if sgps:
    try:
      for sg in sgps: 
        if sg.group_name == 'default':
          print(sg.id + " is the default security group, deleting")
          continue
        print("Removing sg: ", sg.id)
        sg.delete()
    except boto3.exceptions.Boto3Error as e:
      print(e)

def del_vpc(ec2, vpcid):
  vpc_resource = ec2.Vpc(vpcid)
  try:
    print("Removing vpc: ", vpc_resource.id)
    vpc_resource.delete()
  except boto3.exceptions.Boto3Error as e:
      print(e)
      print("Please delete VPC manually.")




if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument('-p', '--profile',  type=str, help='AWS CLI Profile name')
    parser.add_argument('-r', '--region',  type=str, help='AWS CLI Region name')

    args = parser.parse_args()

    session = boto3.Session(
    region_name=args.region,
    profile_name=args.profile
    )
    client = session.client('ec2')
    ec2 = session.resource('ec2')
    try:
        vpcs = get_default_vpcs(client)
    except Exception as err:
        print(err)
        exit(1)
    else:
        for vpc in vpcs:
            print("\n" + "\n" + "REGION:" + args.region + "\n" + "VPC Id:" + vpc)
            del_igw(ec2, vpc)
            del_sub(ec2, vpc)
            del_rtb(ec2, vpc)
            del_acl(ec2, vpc)
            del_sgp(ec2, vpc)
            del_vpc(ec2, vpc)