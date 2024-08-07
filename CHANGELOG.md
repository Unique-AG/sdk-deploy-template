This changelog documents the changes made to the `sdk-deploy-template` repository in regards to how copies of the template can be updated with the latest changes.

## [2024-08-06] - Add async assistant app demo and unique_toolkit integration
- Adds a demo application `assistant_demo_async` that showcases the usage of the async web app using the Quart web framework.
- Demonstrates in `assistant_demo` and `assistant_demo_async` how to use the `unique_toolkit` to interact with the assistant.

## [2024-05-15] - Enabling Application Logs
Forks of this template that are hosted under Uniques [Hosting Service](https://unique-ch.atlassian.net/wiki/x/noEKGg) can now leverage the [App Logs feature](https://unique-ch.atlassian.net/wiki/x/hgB_I). To enable this feature, all deployment workflows must be updated to `v3` and include its [breaking change](https://github.com/Unique-AG/sdk-deploy-action/blob/main/CHANGELOG.md#v3).

The workflows to deploy must edited, bumped to `v3` and supplied with the `azure_storage_account_id` input.

```yaml
uses: Unique-AG/sdk-deploy-action@v3 # <-- This must be at least v3 
with:
  environment: <environment> # This variable is already present if the module was previously deployed already.
  azure_storage_account_id: ${{ vars.AZURE_STORAGE_ACCOUNT_ID }}
```

Unique hosted repositories have this variable injected into its variables and can be directly used as described above. In order to later see the logs, you must also remember the `environment` that was set. You can learn more about the App Logs themselves [here](https://unique-ch.atlassian.net/wiki/x/hgB_I).