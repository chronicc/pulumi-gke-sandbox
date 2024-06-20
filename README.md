# Pulumi GKE Sandbox

## Intension

Provide a playground for testing gke setups.

## Getting started

- Install mise: https://mise.jdx.dev/getting-started.html
- Inside of the repository root run `mise run install` to install the project dependencies.
- Login to google cloud by running
  - `gcloud config set project <YOUR_GCP_PROJECT_ID>`
  - `gcloud auth application-default login`
- Fill out the missing values inside `.mise.local.toml`.

### Introduction to mise-en-place

> Project Site: https://github.com/jdx/mise

Mise-en-place (french for setup) takes care of managing the project dependencies, allows
running tasks like `make` and automatically sets up the python virtual environment.
To see all available commands run `mise tasks`.

### Introduction to pulumi

> Project Site: https://www.pulumi.com/

Pulumi is a tool to manage cloud infrastructure as code. It supports multiple cloud
providers and allows to write infrastructure code in multiple languages. This project
uses python to define the infrastructure.

For local development you can use the local stack by running `pulumi login --local`.

Inside of `.mise.local.toml` the pulumi passphrase is set with `PULUMI_CONFIG_PASSPHRASE`.
Use this passphrase to decrypt the pulumi state file when creating a new stack with
`pulumi stack init <stack> --secrets-provider=passphrase`.

### Resetting the project environment

If you find yourself in a place where the project seems to behave strange or your
dependencies are broken, you can reset the project environment by running `mise run clean`.
This will remove the virtual environment but not the `.mise.local.toml`. Afterwards you
can run `mise run install` to reinstall the project dependencies.

## Topics

- [Conventional Commit Messages](docs/conventional_commit_messages.md)
