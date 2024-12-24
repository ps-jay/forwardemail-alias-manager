#!/usr/bin/env python3

"""
Manages forwardemail.net aliases
"""

import argparse
import pprint
import sys

import requests
import yaml


def parse_args():
    """Parse the arguments given to the application"""
    parser = argparse.ArgumentParser()

    parser.add_argument('domain',
        help='Domain name to configure aliases for',
    )
    parser.add_argument('api_key',
        help='API key to use for authentication',
    )
    parser.add_argument('alias_file',
        type=argparse.FileType('r'),
        help='Configuration YAML file with the aliases to define',
    )
    parser.add_argument('-d', '--diff',
        action='store_true',
        help='Run in diff mode',
    )

    return parser.parse_args()


def get_current(domain, api_key):
    """Get current aliases for the domain"""
    data = []
    page = 1
    more_pages = True
    session = requests.Session()
    auth = requests.auth.HTTPBasicAuth(api_key, '')

    while more_pages:
        params = {
            'pagination': 'true',
            'page': page,
        }
        request = requests.get(f"https://api.forwardemail.net/v1/domains/{domain}/aliases",
            auth=auth,
            params=params,
            timeout=10,
        )

        if request.status_code != 200:
            raise RuntimeError(f"HTTP Error {request.status_code} on get aliases:\n{request.text}")

        if not request.headers.get('X-Page-Count'):
            raise RuntimeError("HTTP X-Page-Count not returned")

        if int(request.headers['X-Page-Count']) > page:
            page += 1
        else:
            more_pages = False

        data += request.json()

    return data


def filter_fields(data):
    """Filter the data down to the fields of interest"""
    keys = [
      'id',
      'name',
      'is_enabled',
      'error_code_if_disabled',
      'recipients',
      'has_imap',
      'max_quota',
    ]

    filtered = []
    for item in data:
        filtered.append({key: value for key, value in item.items() if key in keys})

    return filtered


def set_defaults(data):
    """Set default values, mutates the data given in the args"""
    for item in data:
        if 'recipients' not in item:
            item['recipients'] = ["nobody@forwardemail.net"]  # Empty array or string ends up getting the default email :(
        if 'max_quota' not in item:
            item['max_quota'] = "128 MB"
        if 'is_enabled' not in item:
            item['is_enabled'] = True
        if 'error_code_if_disabled' not in item:
            item['error_code_if_disabled'] = 550

        # fix bytes as int -> string
        if type(item['max_quota']) is int:
            item['max_quota'] = f"{int(item['max_quota'] / 1024 / 1024)} MB"

        if not item['is_enabled'] and not item.get('recipients'):
            item['has_imap'] = True

        if item.get('recipients') and not 'has_imap' in item:
            item['has_imap'] = False

def sanity_check(data):
    """Checks for data sanity"""
    for item in data:
        if 'name' not in item:
            raise RuntimeError("Found data with no name")
        if not item.get('recipients') and not item['has_imap']:
            raise RuntimeError(f"Alias {item['name']} has neither recipients nor has imap enabled")


def find_diff_aliases(current, desired):
    """Find any difference in aliases"""
    current_names = []
    desired_names = []
    for item in current:
        current_names.append(item['name'])
    for item in desired:
        desired_names.append(item['name'])
    current_names.sort()
    desired_names.sort()

    to_be_deleted = list(set(current_names) - set(desired_names))
    to_be_created = list(set(desired_names) - set(current_names))
    to_remain = list(set(current_names) & set(desired_names))

    return to_be_deleted, to_be_created, to_remain


def delete(domain, api_key, names):
    """Delete these aliases"""
    auth = requests.auth.HTTPBasicAuth(api_key, '')
    session = requests.Session()
    for name in names:
        request = session.delete(f"https://api.forwardemail.net/v1/domains/{domain}/aliases/{name}",
            auth=auth,
            timeout=10,
        )

        if request.status_code != 200:
            raise RuntimeError(f"HTTP Error {request.status_code} on deleting {name}:\n{request.text}")
        print(f"Deleted {name}")

    print()


def create(domain, api_key, names, data):
    """Create these aliases"""
    auth = requests.auth.HTTPBasicAuth(api_key, '')
    session = requests.Session()
    for name in names:
        details = next(filter(lambda detail: detail['name'] == name, data))
        params = {
            'name': name,
            'is_enabled': details['is_enabled'],
            'error_code_if_disabled': details['error_code_if_disabled'],
            'recipients': details['recipients'],
            'has_imap': details['has_imap'],
            'max_quota': details['max_quota'],
        }

        request = session.post(f"https://api.forwardemail.net/v1/domains/{domain}/aliases",
            auth=auth,
            data=params,
            timeout=10,
        )

        if request.status_code != 200:
            raise RuntimeError(f"HTTP Error {request.status_code} on creating {name}:\n{request.text}")
        print(f"Created {name}")

    print()


def update(domain, api_key, names, current, data):
    """Update these aliases if required"""
    auth = requests.auth.HTTPBasicAuth(api_key, '')
    session = requests.Session()
    for name in names:
        current_details = next(filter(lambda detail: detail['name'] == name, current))
        desired_details = next(filter(lambda detail: detail['name'] == name, data))

        alias_id = current_details['id']
        desired_details['id'] = alias_id

        if current_details == desired_details:
            print(f"No update needed for {name}")
            continue

        params = {
            'name': name,
            'is_enabled': desired_details['is_enabled'],
            'error_code_if_disabled': desired_details['error_code_if_disabled'],
            'recipients': desired_details['recipients'],
            'has_imap': desired_details['has_imap'],
            'max_quota': desired_details['max_quota'],
        }

        diff = {}
        for detail in current_details:
            if current_details[detail] != desired_details[detail]:
                diff[detail] = f"{current_details[detail]} -> {desired_details[detail]}"

        request = session.put(f"https://api.forwardemail.net/v1/domains/{domain}/aliases/{alias_id}",
            auth=auth,
            data=params,
            timeout=10,
        )

        if request.status_code != 200:
            raise RuntimeError(f"HTTP Error {request.status_code} on creating {name}:\n{request.text}")
        print(f"Updated {name} for differences: {diff}")

    print()


def main():
    """Main program"""
    args = parse_args()

    data = yaml.safe_load(args.alias_file)
    data = filter_fields(data)

    current = get_current(args.domain, args.api_key)
    current = filter_fields(current)

    set_defaults(current)
    set_defaults(data)
    sanity_check(current)
    sanity_check(data)

    to_be_deleted, to_be_created, to_be_updated = find_diff_aliases(current, data)

    print("To be deleted:")
    pprint.pprint(to_be_deleted)
    print()

    print("To be created:")
    pprint.pprint(to_be_created)
    print()

    print("To be kept (and possibly updated):")
    pprint.pprint(to_be_updated)
    print()

    if args.diff:
        print("Diff mode only, exiting without doing anything")
        sys.exit(0)

    if to_be_deleted:
        delete(args.domain, args.api_key, to_be_deleted)

    if to_be_created:
        create(args.domain, args.api_key, to_be_created, data)

    if to_be_updated:
        update(args.domain, args.api_key, to_be_updated, current, data)


if __name__ == "__main__":
    main()
