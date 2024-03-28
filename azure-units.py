import subprocess
import json
import argparse
# Usage python3 ./azure-units.py --subscriptions <subscription_1> <subscription_2> <subscription_3> <subscription_4>

parser = argparse.ArgumentParser(prog="PingSafe Azure Unit Audit")
parser.add_argument("--subscriptions", help="Azure subscription(s) separated by space", nargs='+', default=[], required=False)
args = parser.parse_args()

SUBSCRIPTIONS = args.subscriptions


def call_with_output(command):
    success = False
    retries = 3
    while(retries > 0 and not success ):
        try:
            output = subprocess.check_output(command, text=True, shell=True)
            success = True
            break
        except subprocess.CalledProcessError as e:
            output = e.output
        retries = retries - 1
        print(f"retries {retries}/3")
    return(success, output)

def check_extenstion(name):
    print("Checking extension: ",name)
    success = False
    try:
        success, output = call_with_output(f"az extension show -n {name}")
        success = True
    except subprocess.CalledProcessError as e:
        output = e.output
    if f"The extension {name} is not installed" in output:
        return False
    return success

def azure_show_subscription(subscription):
    success, output = call_with_output(f"az account subscription show --subscription-id {subscription} --output json")
    if f"SubscriptionNotFound" in output:
        return False
    return success

class PingSafeAzureUnitAudit:
    def __init__(self, subscription):
        self.file_path = f"azure-{subscription}-units.csv" if subscription else 'azure-units.csv'
        self.subscription_flag = f'--subscription "{subscription}"'
        self.total_resource_count = 0

        extensions= () # example "containerapp",
        for extension in extensions:
            if not check_extenstion(extension):
                raise Exception(f"Extension not installed: {extension}. Install using az extension add -n {extension}")

        if not azure_show_subscription(subscription):
            raise Exception(f"check azure subscription id/permissions subscription-id: {subscription}")

        with open(self.file_path, 'w') as f:
            f.write("Resource Type, Unit Counted, Error\n")

    def add_result(self, k, v):
        with open(self.file_path, 'a') as f:
            error = json.dumps(v[1])
            f.write(f'{k}, {v[0]}, {error}\n')

    def count_all(self):
        self.add_result("Azure Virtual Machine", self.count_vm_instances())
        self.add_result("Azure Kubernetes Cluster (AKS)", self.count_kubernetes_clusters())
        self.add_result("Azure Container Repository", self.count_container_repository())

        self.add_result("Total Resource", (self.total_resource_count,""))
        print("results stored at", self.file_path)

    def count_vm_instances(self):
        print('getting data for count_vm_instances')
        success, output = call_with_output(f"az vm list {self.subscription_flag} --output json")
        if not success:
            print("Failed with error: ",output)
            return 0, output
        j = json.loads(output)
        self.total_resource_count += len(j)
        return len(j), ""

    def count_kubernetes_clusters(self):
        print('getting data for count_kubernetes_clusters')
        success, output = call_with_output(f"az aks list {self.subscription_flag} --output json")
        if not success:
            print("Failed with error: ",output)
            return 0, output
        j = json.loads(output)
        self.total_resource_count += len(j)
        return len(j), ""

    def count_container_repository(self):
        print('getting data for count_container_repository')
        success, output = call_with_output(f"az acr list {self.subscription_flag} --output json")
        if not success:
            print("Failed with error: ",output)
            return 0, output
        registries = json.loads(output)
        total_repositories = 0;
        for registry in registries:
            registryName = registry.get("name")
            success, output = call_with_output(f"az acr repository list {self.subscription_flag} --name {registryName} --output json")
            if not success:
                print("Failed with error: ",output)
                return 0, output
            repositories = json.loads(output)
            total_repositories += len(repositories)
        self.total_resource_count += total_repositories
        return total_repositories, ""

if __name__ == '__main__':
    subscriptions = SUBSCRIPTIONS if len(SUBSCRIPTIONS) > 0 else [None]
    for s in subscriptions:
        PingSafeAzureUnitAudit(s).count_all()
