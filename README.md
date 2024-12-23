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



## Limitations
This is coded to what I need, and therefore doesn't support all of the
possibilities of forwardemail.net

Annoyingly sending either "" or [] for recipients ends up setting the
default email for the domain.  So I use nobody@forwardemail.net

Probably all this should be Terraform instead, but this was the quickest
path from zero to success for me
