import subprocess
import json
import argparse

# Usage python3 ./digitalocean-units.py --contexts <context_1> <context_2> <context_3> <context_4>

parser = argparse.ArgumentParser(prog="PingSafe Digital Ocean Unit Audit")
parser.add_argument("--contexts", help="Digital Ocean CLI Contexts separated by space", nargs='+', default=[], required=False)
args = parser.parse_args()

CONTEXTS = args.contexts

class PingSafeDigitalOceanUnitAudit:
    def __init__(self, context):
        self.file_path = "digitalocean-{context}-units.csv".format(context=context) if context else 'digitalocean-units.csv'
        self.context_flag = "--context {context}".format(context=context) if context else ''
        self.total_resource_count = 0

        with open(self.file_path, 'w') as f:
            f.write("Resource Type, Unit Counted\n")

    def add_result(self, k, v):
        with open(self.file_path, 'a') as f:
            f.write('{k}, {v}\n'.format(k=k,v=v))

    def count_all(self):
        self.add_result("Digital Ocean Droplets", self.count_droplets())
        self.add_result('TOTAL', self.total_resource_count)

        print("results stored at", self.file_path)

    def count_droplets(self):
      output = subprocess.check_output(
          f"doctl  compute droplet  list --output json {self.context_flag}",
          text=True, shell=True
      )
      j = json.loads(output)
      self.total_resource_count += len(j)
      return len(j)

if __name__ == '__main__':
    contexts = CONTEXTS if len(CONTEXTS) > 0 else [None]
    for context in contexts:
        PingSafeDigitalOceanUnitAudit(context).count_all()
