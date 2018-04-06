#!/usr/bin/python

import json
import yaml
import os

ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'version': '0.1'}

DOCUMENTATION = '''
---
module: kubectl
author:
  - Fai Fung and Eric Nieuwenhuijsen
short_description: kubectl (cli) module
description:
  - The kubectl module wraps the kubectl binary
options:
  command:
    description:
      - kubectl command
    required: true
    choices:
  args:
    description:
      -
    required: false
    default: ''
  template:
    description:
      -
    required: false
    default: null
'''

EXAMPLES = """
- name: kubectl create pod from json input
  kubectl:
     command: apply
     args:  -f <something already on the host>
# results in kubectl apply -f <rendered template>
- name: kubectl create pod from json input
  kubectl:
     command: apply
     template: <my template.j2>
"""

RETURN = '''
output:
  description: Output of kubectl
  returned: success
  type: string
'''

class Kubectl:
    def __init__(self, module):
        self.module = module
        self.default_namespace = "default"

    def kubectl(self):
        command = self.module.params['command']
        args = self.module.params['args']

        return "kubectl %s %s" % (command, args)

    def apply(self, args, tempfile):
        resources = self.read_kube_file(tempfile)
        resource_versions_prior_to_apply = self.fetch_resource_versions(resources)

        rc, out, err = self.module.run_command('kubectl apply ' + args + ' -f ' + tempfile , use_unsafe_shell=True)
        if rc != 0:
            self.module.fail_json(msg=err, rc=rc, err=err, out=out)
        else:
            failed = False

        # Cleanup temporary files
        try:
            os.remove(tempfile)
        except OSError as exc:
            if exc.errno != errno.ENOENT:
                raise

        resource_versions_after_apply = self.fetch_resource_versions(resources)

        if resource_versions_prior_to_apply != resource_versions_after_apply:
            changed = True
        else:
            changed = False

        self.module.exit_json(changed=changed, rc=rc, err=err, out=out)

    def fetch_resource_versions(self, resources):
        result = dict()
        for name, resourceData in resources.iteritems():
             rc, out, err = self.module.run_command("kubectl get -o jsonpath='{.metadata.resourceVersion}' "+ " --namespace=" + resourceData['namespace'] + " " + resourceData['kind'] +  " " + name)
             result[name] = out
        return result

    def read_kube_file(self, filename):
        result = dict()

        if filename.endswith('.yaml') or filename.endswith('.yml'):
            result = self.process_yaml(filename)
        elif filename.endswith('.json'):
            result = self.process_json(filename)
        else:
            raise ValueError('Unsupported file extension.')

        return result

    def process_yaml(self, filename):
        result = dict()

        with open(filename, 'r') as f:
            try:
                for data in yaml.load_all(f):
                    name, item = self.parse_item(data)
                    result[name] = item
                f.close()
            except yaml.YAMLError as exc:
                print(exc)

        return result

    def process_json(self, filename):
        result = dict()

        with open(filename, 'r') as f:
            try:
                data = json.load(f)
                if data['kind'] == "List":
                    for listItem in data['items']:
                        name, item = self.parse_item(listItem)
                        result[name] = item
                else:
                        name, item = self.parse_item(data)
                        result[name] = item
            except ValueError:
                print "JSON decode error"

        return result

    def parse_item(self, item):
        result = dict()
        name = item['metadata']['name']
        result["kind"] = item['kind']
        if "namespace" in item['metadata']:
            result['namespace'] = item['metadata']['namespace']
        else:
            result['namespace'] = self.default_namespace

        return name,result
    def get_output(self, rc=0, out=None, err=None):
        if rc:
            self.module.fail_json(msg=err, rc=rc, err=err, out=out)
        else:
            self.module.exit_json(changed=1, msg=json.dumps(out))

def main():
    module = AnsibleModule(
            argument_spec = dict(
                command         = dict(required=True),
                args            = dict(required=False, default=''),
                template        = dict(required=False, default='')
                ),
            supports_check_mode = False
            )

    kube = Kubectl(module)
    if module.params['command'] == "apply" and module.params['template']:
        kube.apply(module.params['args'],module.params['template'])
    else:
        rc, out, err = module.run_command(kube.kubectl(), use_unsafe_shell=True)
        kube.get_output(rc, out, err)

from ansible.module_utils.basic import *

if __name__ == '__main__':
    main()
