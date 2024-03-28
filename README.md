# PingSafe Sizing Scripts

### Google Cloud Script

Pre-requisites:

1. python 3+
2. `gcloud` cli
3. gcloud `alpha` component
4. gcloud `bq` cli tool
5. gcloud `gsutil` cli tool

`gcp-units.py`

To run the script

```bash
python3 ./gcp-units.py --project_id project_id
```

Output (in directory from where script is run)

```
gcp-{project_id}-units.csv
```

Important Information:

- `--project_id` is a required flag
- If you have multiple project ids, the script needs to be run for each one separately
- The script may take a longer time to run based on the size of the cloud for the project that is being run for

### AWS Script

Pre-requisites:

1. python 3+
2. `aws` cli

`aws-units.py`

To run the script:

```bash
python3 ./aws-units.py --profiles default profile_2 ... profile_n
```

Important Information:

- Script requires at least one profile to be passed with the **required** `--profiles` flag
- if there are no named profiles configured, the script requires the `"default"` profile to be passed, eg: `--profiles default`
- For more information on named profile configuration for aws cli, please refer to https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-configure.html and https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-files.html
- The script may take a longer time to run based on the size of the cloud for which it is being run for
- If you pass many profiles, it may take a considerable amount of time, subject to the size of the cloud

Output (in directory from where script is run)

```
aws-{profile}-units.csv
aws-{profile2}-units.csv
```

### Azure Script

Pre-requisites:

1. `az` cli

`azure-units.py`

To run the script:

```bash
python3 ./azure-units.py --subscriptions <subscription_id_1> <subscription_id_2>
```

Important Information:

- Script requires at least one subscriptions to be passed with the **required** `--subscriptions` flag
- The script may take a longer time to run based on the size of the cloud for the subscriptions that is being run for

Output (in directory from where script is run)

```
azure-{subscription}-units.csv
azure-{subscription}-units.csv
```
