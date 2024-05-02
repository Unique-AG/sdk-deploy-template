# SDK Deployments

## Table of Contents
1. [Overview](#overview)
2. [Requirements for Python Projects](#requirements-for-python-projects)
3. [Managing Environment Variables](#managing-environment-variables)
4. [GitHub Action Deployment](#github-action-deployment)
5. [Deployment Environments](#deployment-environments)
6. [Dockerfile & Scaling](#dockerfile--scaling)

## 1. Overview

This repository serves as a monorepo for Python applications, each of which can be individually deployed to Azure Container Apps. To ensure successful deployment, there are specific requirements for each Python project outlined below.

## 2. Requirements for Python Projects

For each Python application within this monorepo, the following requirements must be met:

- **Naming Convention:** Use only lowercase letters (a-z) in the project name. Underscores (_) are permitted to enhance readability.
- **App & Module name must match:** The name of the Python module containing the Flask app must match the name of the app.
- **Poetry Project:** Each app must be a Poetry project, as the deployment relies on a shared Dockerfile that executes the app with Poetry.
- **Encrypted Environment Variables:** All environment variables must be encrypted and checked into Git as a `.env.enc` file. This file must exist even if it is empty.
- **Dependencies:** Ensure the inclusion of `gunicorn` and `python-dotenv` in the project's dependencies.

## 3. Managing Environment Variables

For secure transmission of secrets to the container app, we employ encryption with Sops (https://github.com/mozilla/sops) using Age (https://github.com/FiloSottile/age) keys. The repository contains a private Age key stored as a GitHub secret, and the public key is provided below:

```
{age_public_key}
```

To encrypt your environment variables, follow these steps:

1. Store all development environment variables in a `.env` file, which is excluded from Git.
2. Install `sops`:
   - On macOS, use `brew install sops`.
   - On other systems, refer to the official documentation at https://github.com/mozilla/sops.
3. After updating the `.env` file, encrypt it and refresh the `.env.enc` file with the following command:

```bash
sops --encrypt --age {age_public_key} .env > .env.enc
```

If you deploy to multiple environments (e.g., `dev`, `staging`, `prod`), you can create a separate `.env` file for each environment and encrypt them accordingly. If you do so, **make sure you update the GitHub Action deployment workflow to use the correct `.env.enc` file for each environment.**

## 4. GitHub Action Deployment

Deploy each Python app using a specific GitHub Action workflow.

** Each app and each environment get its own deployment workflow **

1. In `.github/workflows`, create a new file named `<your-app-name>.<your-github-environment-name>.deploy.yaml`.
2. Insert the following workflow definition, replacing placeholders as necessary:

```yaml
name: "[<your-app-name>][🗄️env: <your-github-environment-name>] Deploy to Azure Container Apps"

on:
  workflow_dispatch:

permissions:
      id-token: write
      contents: read

jobs:
  warning:
    if: github.ref != 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - run: You are not allowed to deploy from branches other than main.

  deployment:
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    environment: <your-github-environment-name>
    steps:
      - name: Deploy to Azure Container Apps
        id: deploy
        uses: Unique-AG/sdk-deploy-action@v2
        with:
          module: <your-app-name>
          environment: <your-github-environment-name>
          resource_group_name: ${{ vars.AZURE_RESOURCE_GROUP }}
          acr_login_server: ${{ vars.ACR_LOGIN_SERVER }}
          azure_client_id: ${{ vars.AZURE_CLIENT_ID }}
          azure_tenant_id: ${{ vars.AZURE_TENANT_ID }}
          azure_subscription_id: ${{ vars.AZURE_SUBSCRIPTION_ID }}
          acr_username: ${{ secrets.ACR_USERNAME }}
          acr_password: ${{ secrets.ACR_PASSWORD }}
          age_private_key: ${{ secrets.AGE_PRIVATE_KEY }}
          encrypted_env_file: .env.enc
      - name: Create Summary
        run: |
          echo "## Azure Container App ${{ steps.deploy.outputs.app_name }}" >> $GITHUB_STEP_SUMMARY
          echo "**FQDN:** [${{ steps.deploy.outputs.fqdn }}](https://${{ steps.deploy.outputs.fqdn }})" >> $GITHUB_STEP_SUMMARY
          echo "**App Name:** ${{ steps.deploy.outputs.app_name }}" >> $GITHUB_STEP_SUMMARY
          echo "**Environment:** ${{ steps.deploy.outputs.environment }}" >> $GITHUB_STEP_SUMMARY
          echo "**Resource Group:** ${{ steps.deploy.outputs.resource_group_name }}" >> $GITHUB_STEP_SUMMARY
          echo "**Location:** ${{ steps.deploy.outputs.location }}" >> $GITHUB_STEP_SUMMARY
          
```

3. Ensure you replace the placeholders `<your-app-name>` and `<your-github-environment-name>` with the appropriate values.
4. Customize the `with` section of the action to match your project's `sops` and `poetry` versions.
5. You should keep the `warning` job to prevent deployments from branches other than `main`. Removing this block might result in a violation of the deployment policy.
6. Commit the action to GitHub.
7. Navigate to the Actions tab in your GitHub repository.
8. Select the appropriate workflow and run it to initiate the first deployment.
9. The FQDN of your deployed app will be visible in the job summary of your GitHub Action workflow.

### Full list of available inputs

* `module`: Name of the module to deploy. **(Required)**
* `environment`: Name of the environment to deploy the module to. **(Required)**
* `resource_group_name`: Name of the resource group to deploy the module to. **(Required)**
* `acr_login_server`: Azure Container Registry login server. **(Required)**
* `azure_client_id`: Azure client ID. **(Required)**
* `azure_tenant_id`: Azure tenant ID. **(Required)**
* `azure_subscription_id`: Azure subscription ID. **(Required)**
* `acr_username`: Azure Container Registry username. **(Required)**
* `acr_password`: Azure Container Registry password. **(Required)**
* `age_private_key`: Age private key. **(Required)**

The action also supports the following optional inputs:

* `app_name`: Name of the Flask app (and file). Don't confuse it with the name of the container that is deployed. The container name is automatically defined. Default: `app`
* `encrypted_env_file`: Name of the encrypted environment file. Default: `.env.enc`
* `dockerfile`: Dockerfile for the container app. Default: `./Dockerfile`
* `sops_version`: Version of sops to use. Default: `3.8.1`
* `poetry_version`: Version of poetry to use. Default: `1.7.1`
* `min_replicas`: Minimum number of replicas for the container app. Default: `1`
* `max_replicas`: Maximum number of replicas for the container app. Default: `1`
* `location`: Location of the Azure Container Apps environment. Default: `switzerlandnorth`
* `cache_tag`: Tag to use for caching the docker build. Default: `dockercache`

> [!WARNING]
> There are also two more optional inputs available but they have a cost-aspect and must only be applied after consulting your teams engineer or architect.

* `cpu`: CPUs to allocate for the container app cores from 0.25 - 2.0, e.g. 0.5. Defaults to `0.5`. Only available with `Unique-AG/sdk-deploy-action@v2`.
* `memory`: Required memory from 0.5 - 4.0, will be converted to *Gi and Gi must not be supplied. Defaults to `1`(Gi). Only available with `Unique-AG/sdk-deploy-action@v2`.

### Handling the FQDN for Webhooks

To resolve the challenge of obtaining the FQDN before configuring your `ENDPOINT_SECRET` for webhook verification, consider these approaches:

- **Option A:** Deploy the app without an `ENDPOINT_SECRET`. Once you have the FQDN, update your app and redeploy.
- **Option B:** Initially define a placeholder endpoint (e.g., `http://localhost/webhook`), use the generated signing secret, and update the endpoint with the actual FQDN later.

## 5. Deployment Environments

You have the option to request Unique to configure each of your deployments as distinct deployment environments. This allows you to select the specific environment for each deployment action. Different environments can be set up with unique requirements, such as mandatory reviews or specific wait times, before the deployment proceeds.

## 6. Dockerfile & Scaling

All apps within this repository are deployed using a shared Dockerfile. You have the option to modify the Dockerfile according to your needs and specify your custom version in the GitHub Actions as an input. The default Dockerfile utilizes `gunicorn` to run the app, configured with `2` workers and `4` threads per worker.

As we use threads, your code **must be thread-safe!** Failure to ensure thread safety may result in unpredictable behavior and potential data corruption.

**This setup allows each app replica to handle 8 concurrent requests.**

To adjust the scaling, you can change the `min_replicas` and `max_replicas` parameters in the GitHub Action. This modification enables the deployment of additional replicas of the app.
