import subprocess
import json
import argparse

# Usage python3 ./aws-units.py --profiles <profile_1> <profile_2> <profile_3> <profile_4>

parser = argparse.ArgumentParser(prog="PingSafe AWS Unit Audit")
parser.add_argument("--profiles", help="AWS profile(s) separated by space", nargs='+', default=[], required=False)
parser.add_argument("--regions", help="Regions to run script for", nargs='+', default=[], required=False)
args = parser.parse_args()

PROFILES = args.profiles
REGIONS = args.regions


def aws_describe_regions(profile):
    profile_flag = "--profile {profile}".format(profile=profile) if profile else ''
    output = subprocess.check_output(
        "aws {profile_flag} ec2 describe-regions --filters \"Name=opt-in-status,Values=opted-in,opt-in-not-required\" --output json".format(profile_flag=profile_flag),
        universal_newlines=True, shell=True, stderr=subprocess.STDOUT
    )
    if "The config profile ({profile}) could not be found".format(profile=profile) in output:
        raise Exception("found invalid aws profile {profile}".format(profile=profile))
    j = json.loads(output)
    all_regions_active = [region_object['RegionName'] for region_object in j['Regions']]
    if len(REGIONS) == 0:
        return all_regions_active

    # if only some regions to be whitelisted
    print('found whitelisted regions', REGIONS)
    regions_to_run = []
    for region in all_regions_active:
        if region in REGIONS:
            regions_to_run.append(region)
    print("valid whitelisted regions", regions_to_run)
    return regions_to_run


class PingSafeAWSUnitAudit:
    def __init__(self, profile):
        self.file_path = "aws-{profile}-units.csv".format(profile=profile) if profile else 'aws-units.csv'
        self.profile_flag = "--profile {profile}".format(profile=profile) if profile else ''
        self.total_resource_count = 0
        self.regions = aws_describe_regions(profile)

        with open(self.file_path, 'w') as f:
            # Write Header
            f.write("Resource Type, Unit Counted\n")

    def build_aws_cli_command(self, service, api, paginate=True, region=None, query=None):
        region_flag = paginate_flag = query_flag = ""
        if region:
            region_flag = "--region {region}".format(region=region)
        if query:
            query_flag = "--query {query}".format(query=query)
        if not paginate:
            paginate_flag = "--no-paginate"
        cmd = "aws {region_flag} {profile_flag} --output json {service} {api} {query_flag} {paginate_flag}".format(
            region_flag=region_flag, profile_flag=self.profile_flag, service=service, api=api,
            paginate_flag=paginate_flag, query_flag = query_flag
        )
        print(cmd)
        return cmd

    def add_result(self, k, v):
        with open(self.file_path, 'a') as f:
            f.write('{k}, {v}\n'.format(k=k,v=v))

    def count_all(self):
        ec2_instances_count = 0
        ecr_repositories_count = 0
        eks_cluster_count = 0
        lambda_functions_count = 0
        ecs_clusters_count = 0

        # Region Agnostic
        # s3_bucket_count += self.count_s3_buckets()

        # Region Specific
        for region in self.regions:
            ec2_instances_count += self.count_ec2_instances(region)
            ecr_repositories_count += self.count_ecr_repositories(region)
            eks_cluster_count += self.count_eks_clusters(region)
            lambda_functions_count += self.count_lambda_functions(region)
            ecs_clusters_count += self.count_ecs_clusters(region)

        self.add_result("AWS EC2 Instance", ec2_instances_count)
        self.add_result("AWS Container Repository", ecr_repositories_count)
        self.add_result("AWS Kubernetes Cluster (EKS)", eks_cluster_count)
        self.add_result("AWS Lambda Function", lambda_functions_count)
        self.add_result("AWS ECS Cluster", ecs_clusters_count)

        self.add_result('TOTAL', self.total_resource_count)
        print("results stored at", self.file_path)

    def count_ec2_instances(self, region):
        print('getting data for count_ec2_instances', region)
        output = subprocess.check_output(
            # "aws --region {region} {profile_flag} --query \"Reservations[].Instances\" ec2 describe-instances --output json --no-paginate".format(region=region, profile_flag=self.profile_flag),
            self.build_aws_cli_command(
                service="ec2",
                api="describe-instances",
                paginate=False,
                query="\"Reservations[].Instances\"",
                region=region),
            universal_newlines=True, shell=True, stderr=subprocess.STDOUT
        )
        j = json.loads(output)
        if j is None or len(j) == 0:
            return 0
        c = len(j)
        self.total_resource_count += c
        return c

    def count_ecr_repositories(self, region):
        print('getting data for count_ecr_repositories', region)
        output = subprocess.check_output(
            # "aws --region {region} {profile_flag} ecr describe-repositories --query \"repositories[].repositoryArn\" --output json --no-paginate".format(region=region,profile_flag=self.profile_flag)
            self.build_aws_cli_command(
                service="ecr",
                api="describe-repositories",
                query="\"repositories[].repositoryArn\"",
                paginate=False,
                region=region),
            universal_newlines=True, shell=True, stderr=subprocess.STDOUT
        )
        j = json.loads(output)
        if j is None or len(j) == 0:
            return 0
        c = len(j)
        self.total_resource_count += c
        return c

    def count_eks_clusters(self, region):
        print('getting data for count_eks_clusters', region)
        output = subprocess.check_output(
            # f"aws --region {region} {self.profile_flag} eks list-clusters --output json --no-paginate",
            self.build_aws_cli_command(
                service="eks",
                api="list-clusters",
                paginate=False,
                region=region),
            universal_newlines=True, shell=True, stderr=subprocess.STDOUT
        )
        j = json.loads(output)
        c = len(j.get("clusters", []))
        if j is None or len(j) == 0:
            return 0
        self.total_resource_count += c
        return c

    def count_lambda_functions(self, region):
        print('getting data for count_lambda_function', region)
        output = subprocess.check_output(
            # f"aws --region {region} {self.profile_flag} lambda list-functions --query 'Functions[*].FunctionName' --output json --no-paginate",
            self.build_aws_cli_command(
                service="lambda",
                api="list-functions",
                paginate=False,
                query="\"Functions[*].FunctionName\"",
                region=region),
            universal_newlines=True, shell=True, stderr=subprocess.STDOUT
        )
        j = json.loads(output)
        if j is None or len(j) == 0:
            return 0
        c = len(j)
        self.total_resource_count += c
        return c
    def count_ecs_clusters(self, region):
        print('getting data for count_ecs_cluster', region)
        output = subprocess.check_output(
            # f"aws --region {region} {self.profile_flag} ecs list-clusters --query 'clusterArns' --output json --no-paginate",
            self.build_aws_cli_command(
                service="ecs",
                api="list-clusters",
                paginate=False,
                query="\"clusterArns\"",
                region=region),
            universal_newlines=True, shell=True, stderr=subprocess.STDOUT
        )
        j = json.loads(output)
        if j is None or len(j) == 0:
            return 0
        c = len(j)
        self.total_resource_count += c
        return c

if __name__ == '__main__':
    profiles = PROFILES if len(PROFILES) > 0 else [None]
    for p in profiles:
        PingSafeAWSUnitAudit(p).count_all()
