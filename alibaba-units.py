import subprocess
import json
import argparse

# Usage python3 ./alibaba-units.py --profiles <profile_1> <profile_2> <profile_3> <profile_4>

parser = argparse.ArgumentParser(prog="PingSafe Alibaba Unit Audit")
parser.add_argument("--profiles", help="Alibaba profile(s) separated by space", nargs='+', default=[], required=False)
parser.add_argument("--regions", help="Regions to run script for", nargs='+', default=[], required=False)
args = parser.parse_args()

PROFILES = args.profiles
REGIONS = args.regions

def alibaba_ecs_get_all_regions(profileFlag):
    output = subprocess.check_output(
        f"aliyun ecs DescribeRegions {profileFlag}",
        text=True, shell=True
    )
    regions_info = json.loads(output)

    all_regions_active = []

    if regions_info and 'Regions' in regions_info and 'Region' in regions_info['Regions']:
        all_regions_active = [region['RegionId'] for region in regions_info['Regions']['Region']]

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

class PingSafeAlibabaUnitAudit:
    def __init__(self, profile):
        self.file_path = "alibaba-{profile}-units.csv".format(profile=profile) if profile else 'alibaba-units.csv'
        self.profile_flag = "--profile {profile}".format(profile=profile) if profile else ''
        self.total_resource_count = 0
        self.regions = alibaba_ecs_get_all_regions(self.profile_flag)

        with open(self.file_path, 'w') as f:
            # Write Header
            f.write("Resource Type, Unit Counted\n")


    def add_result(self, k, v):
        with open(self.file_path, 'a') as f:
            f.write('{k}, {v}\n'.format(k=k,v=v))

    def count_all(self):
        ecs_instances_count = 0

        # Region Specific
        for region in self.regions:
            ecs_instances_count += self.count_ecs_instances(region)

        self.add_result("Alibaba ECS Instance", ecs_instances_count)
        self.add_result('TOTAL', self.total_resource_count)
        print("results stored at", self.file_path)

    def count_ecs_instances(self, region):
        print('getting data for count_ecr_instances', region)
        output = subprocess.check_output(
          f"aliyun ecs DescribeInstances --RegionId {region} {self.profile_flag}",
          text=True, shell=True
        )

        j = json.loads(output)
        if j is None:
            return 0

        c = len(j)
        self.total_resource_count += c
        return c

if __name__ == '__main__':
    profiles = PROFILES if len(PROFILES) > 0 else [None]
    for p in profiles:
        PingSafeAlibabaUnitAudit(p).count_all()
