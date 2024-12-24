# forwardemail-alias-manager
Manage aliases on forwardemail.net as code

## Use
Consume this repo & code as a GitHub action

Have a private (presumably!) repo with YAML files for each domain

Then setup a workflow like this:
```yaml
      - id: run
        name: Make it so
        uses: ps-jay/forwardemail-alias-manager@2024.12.1
        with:
          domain: example.net
          api_key: "${{ secrets.api_key }}"
          alias_file: example.net.yaml
```

The domain YAML for a catch-all domain looks like this:
```yaml
---
- name: "*"  # catch-all
  recipients: ["my.real.email@example.com"]

- name: do-not-deliver
  is_enabled: false
```

The domain YAML for multiple alias domain looks like this:
```yaml
---
# Alice
- name: alice
  recipients: ["alice@example.com"]

# Bob
- name: bob
  recipients: ["bob@example.com"]

# Joint delivery
- name: aandb
  recipients: ["alice@example.com", "bob@example.com"]
```

## Inputs

<!-- AUTO-DOC-INPUT:START - Do not remove or modify this section -->

|                             INPUT                              |  TYPE  | REQUIRED |  DEFAULT  |                                DESCRIPTION                                 |
|----------------------------------------------------------------|--------|----------|-----------|----------------------------------------------------------------------------|
| <a name="input_alias_file"></a>[alias_file](#input_alias_file) | string |   true   |           |                 The YAML file that defines all the aliases                 |
|     <a name="input_api_key"></a>[api_key](#input_api_key)      | string |   true   |           |              The API key for forwardemail.net authentication               |
|          <a name="input_diff"></a>[diff](#input_diff)          | string |  false   | `"false"` | Don't make changes, show diff between forwardemail.net and alias YAML file |
|       <a name="input_domain"></a>[domain](#input_domain)       | string |   true   |           |                         The domain name to manage                          |

<!-- AUTO-DOC-INPUT:END -->


## Limitations
This is coded to what I need, and therefore doesn't support all of the
possibilities of forwardemail.net

Annoyingly sending either "" or [] for recipients ends up setting the
default email for the domain.  So I use nobody@forwardemail.net

Probably all this should be Terraform instead, but this was the quickest
path from zero to success for me


##  Full example workflow for YAML storing repo

```yaml
---
name: Make aliases as intended

on:  # yamllint disable-line rule:truthy
  push:
    branches:
      - '**'
    tags-ignore:
      - '**'

jobs:
  files:
    runs-on: ubuntu-latest
    outputs:
      matrix: ${{ steps.show.outputs.domains }}
    steps:
      - id: checkout
        name: Checkout code 🛒
        uses: actions/checkout@v4

      - id: glob
        name: Glob match
        uses: tj-actions/glob@v22
        with:
          files: |
            *.yaml

      - id: show
        name: Show found and strip YAML
        shell: bash
        run: |
         set -euo pipefail
         echo "${{ steps.glob.outputs.paths }}"
         export paths="${{ steps.glob.outputs.paths }}"
         echo "domains=$(jq -cR 'split(" ")' <<< "${paths//.yaml}")" | tee -a "${GITHUB_OUTPUT}"

  diff:
    if: ${{ github.ref_name != github.event.repository.default_branch }}
    runs-on: ubuntu-latest
    needs: [files]
    strategy:
      matrix: 
        domains: ${{ fromJSON(needs.files.outputs.matrix) }}
      max-parallel: 5
      fail-fast: false
    steps:
      - id: checkout
        name: Checkout code 🛒
        uses: actions/checkout@v4

      - id: diff
        name: Show diff
        uses: ps-jay/forwardemail-alias-manager@2024.12.1
        with:
          domain: "${{ matrix.domains }}"
          api_key: "${{ secrets.api_key }}"
          alias_file: "${{ matrix.domains }}.yaml"
          diff: true

  run:
    if: ${{ github.ref_name == github.event.repository.default_branch }}
    runs-on: ubuntu-latest
    needs: [files]
    strategy:
      matrix: 
        domains: ${{ fromJSON(needs.files.outputs.matrix) }}
      max-parallel: 5
      fail-fast: false
    steps:
      - id: checkout
        name: Checkout code 🛒
        uses: actions/checkout@v4

      - id: run
        name: Make it so
        uses: ps-jay/forwardemail-alias-manager@2024.12.1
        with:
          domain: "${{ matrix.domains }}"
          api_key: "${{ secrets.api_key }}"
          alias_file: "${{ matrix.domains }}.yaml"
```
