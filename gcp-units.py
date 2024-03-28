import argparse
import json
import subprocess

# Usage python3 ./gcp-units.py --project_id <project_id>

parser = argparse.ArgumentParser(prog="PingSafe GCP Unit Audit")
parser.add_argument("--project_id", help="GCP Project ID", required=True)
args = parser.parse_args()

PROJECT_ID = args.project_id


def gcloud_set_project(project_id):
    output = subprocess.check_output(
        f"gcloud config set project {project_id}",
        text=True, shell=True, stderr=subprocess.STDOUT
    )
    print(output)
    if f"WARNING: You do not appear to have access to project [{project_id}] or it does not exist." in output:
        return False
    return True


def gcloud_components_check():
    output = subprocess.check_output(
        "gcloud --version",
        text=True, shell=True
    )
    installed_components = [x.split(" ")[0] for x in list(filter(lambda x: len(x.strip()) > 0, output.split("\n")))]
    requirements = {
        "alpha": False,
        "bq": False,
        "gsutil": False
    }
    for component in installed_components:
        if requirements.get(component, None) is not None:
            requirements[component] = True
    for component in requirements:
        if not requirements[component]:
            print("missing component:", component)
            print("required gcloud components:", "alpha", "bq", "gsutil")
            return False
    return True


def gcloud_list_services():
    output = subprocess.check_output(
        "gcloud services list --format json",
        text=True, shell=True
    )
    services = json.loads(output)
    for service in services:
        yield {
            'name': service['config']['name'],
            'enabled': service['state'] == 'ENABLED'
        }


class PingSafeGCPUnitAudit:
    def __init__(self, project_id):
        self.existing_permissions = {}
        self.project_id = project_id
        self.file_path = f"gcp-{project_id}-units.csv"
        self.total_resource_count = 0

        if not gcloud_set_project(project_id):
            raise Exception("check gcp project id/permissions")
        print("successfully set gcloud project id:", project_id)

        if not gcloud_components_check():
            raise Exception("check installed components")
        print("found all required cli components")

        for service in gcloud_list_services():
            if service['enabled']:
                self.existing_permissions[service['name']] = True
        print("fetched all existing permissions on account")

        with open(self.file_path, 'w') as f:
            # Write Header
            f.write("Resource Type, Unit Counted\n")

    def is_api_enabled(self, apis):
        for api in apis:
            if not self.existing_permissions.get(api, False):
                print(f"service-api {api} is disabled")
                return False
        return True

    def add_result(self, k, v):
        with open(self.file_path, 'a') as f:
            f.write(f'{k}, {v}\n')

    def count_all(self):
        self.add_result("GCP Compute Instance", self.count_compute_instances())
        self.add_result("GCP Kubernetes Cluster (GKE)", self.count_kubernetes_clusters())
        self.add_result("GCP Cloud Function", self.count_cloud_functions())
        self.add_result("GCP Cloud Run", self.count_cloud_run())
        self.add_result("GCP Artifact Repository (only docker repositories)", self.count_artifact_repository_docker())
        self.add_result("GCP Container Repository", self.count_container_repository())

        self.add_result('TOTAL', self.total_resource_count)
        print("results stored at", self.file_path)

    def count_compute_instances(self):
        print('getting data for count_compute_instances')
        if not self.is_api_enabled(["compute.googleapis.com"]):
            return 0
        output = subprocess.check_output(
            "gcloud compute instances list --format json",
            text=True, shell=True
        )
        j = json.loads(output)
        self.total_resource_count += len(j)
        return len(j)

    def count_kubernetes_clusters(self):
        print('getting data for count_kubernetes_clusters')
        if not self.is_api_enabled(["container.googleapis.com"]):
            return 0
        output = subprocess.check_output(
            "gcloud container clusters list --format json",
            text=True, shell=True
        )
        j = json.loads(output)
        self.total_resource_count += len(j)
        return len(j)

    def count_cloud_functions(self):
        print('getting data for count_cloud_functions')
        if not self.is_api_enabled(["cloudfunctions.googleapis.com"]):
            return 0
        output = subprocess.check_output(
            f"gcloud functions list --regions={','.join(GCP_CF_LOCATIONS)} --format json",
            text=True, shell=True
        )
        j = json.loads(output)
        self.total_resource_count += len(j)
        return len(j)
    def count_cloud_run(self):
        print('getting data for count_cloud_run')
        if not self.is_api_enabled(["run.googleapis.com"]):
            return 0
        output = subprocess.check_output(
            f"gcloud run services list --format json",
            text=True, shell=True
        )
        j = json.loads(output)

        # TODO remove latter if needed
        output2 = subprocess.check_output(
            f"gcloud run jobs list --format json",
            text=True, shell=True
        )
        i = json.loads(output2)
        self.total_resource_count += len(i)

        self.total_resource_count += len(j)
        return len(j) + len(i)

    def count_artifact_repository_docker(self):
        print('getting data for count_artifact_repository_docker')
        if not self.is_api_enabled(["artifactregistry.googleapis.com"]):
            return 0
        output = subprocess.check_output(
            f"gcloud artifacts repositories list --filter=\"format=docker\" --format json",
            text=True, shell=True
        )
        j = json.loads(output)
        self.total_resource_count += len(j)
        return len(j)

    def count_container_repository(self):
        print('getting data for count_container_repository')
        if not self.is_api_enabled(["storage-api.googleapis.com"]):
            return 0
        output = subprocess.check_output(
            f"gcloud container images list --format json",
            text=True, shell=True
        )
        j = json.loads(output)
        self.total_resource_count += len(j)
        return len(j)

GCP_CF_LOCATIONS = [
    'us-west1',
    'us-central1',
    'us-east1',
    'us-east4',
    'europe-west1',
    'europe-west2',
    'asia-east1',
    'asia-east2',
    'asia-northeast1',
    'asia-northeast2',
    'us-west2',
    'us-west3',
    'us-west4',
    'northamerica-northeast1',
    'southamerica-east1',
    'europe-west3',
    'europe-west6',
    'europe-central2',
    'australia-southeast1',
    'asia-south1',
    'asia-southeast1',
    'asia-southeast2',
    'asia-northeast3'
]

PingSafeGCPUnitAudit(PROJECT_ID).count_all()
