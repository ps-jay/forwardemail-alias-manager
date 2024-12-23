# forwardemail-alias-manager
Manage aliases on forwardemail.net as code

## Use
Consume this repo & code as a GitHub action

Have a private (presumably!) repo with YAML files for each domain

Then setup a workflow like this:
```yaml
TBA
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
