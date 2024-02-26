# Pulumi Infrastructure Description

## Intension

Have all resources considered as infrastructure contained in one repository and managed by one tool.

## Getting started

- Install mise: https://mise.jdx.dev/getting-started.html
- Inside of the repository root run `mise run install` to install the project dependencies.
- Fill out the missing values inside `.mise.local.toml`. For secret values look into 1password.

### Introduction to mise-en-place

> Project Site: https://github.com/jdx/mise

Mise-en-place (frech for setup) takes care of managing the project dependencies, allows running tasks like `make` and automatically sets up the python virtual environment. To see all available commands run `mise tasks`.

### Resetting the project environment

If you find yourself in a place where the project seems to behave strange or your dependencies are broken, you can reset the project environment by running `mise run clean`. This will remove the virtual environment but not the `.mise.local.toml`. Afterwards you can run `mise run install` to reinstall the project dependencies.
