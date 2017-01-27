#!/usr/bin/python

import json
import yaml

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

    def kubectl(self):
        command = self.module.params['command']
        args = self.module.params['args']
        template = self.module.params['template']

        return "/opt/bin/kubectl %s %s" % (command, args)

    def apply(self, arguments, filename):
        resources = self.read_kube_file(filename)
        resource_versions_prior_to_apply = self.fetch_resource_versions(resources)

        rc, out, err = self.module.run_command("/opt/bin/kubectl apply -f " + filename + " " + arguments, use_unsafe_shell=True)
        if rc != 0:
            self.module.fail_json(msg=err, rc=rc, err=err, out=out)
        else:
            failed = False

        resource_versions_after_apply = self.fetch_resource_versions(resources)
        
        if resource_versions_prior_to_apply != resource_versions_after_apply:
            changed = True
        else:
            changed = False

        self.module.exit_json(changed=changed, rc=rc, err=err, out=out)

    def fetch_resource_versions(self, resources):
        result = dict()
        for name, resourceData in resources.iteritems():
             rc, out, err = self.module.run_command("/opt/bin/kubectl get -o jsonpath='{.metadata.resourceVersion}' "+ " --namespace=" + resourceData['namespace'] + " " + resourceData['kind'] +  " " + name)
             result[name] = out
        return result

    def read_kube_file(self, filename):
        default_namespace = "default"
        result = dict()
        with open(filename, 'r') as stream:
            c = stream.read(1)
            stream.seek(0)
            if c == '-':
               try:
                  for data in yaml.load_all(stream):
                    name = data['metadata']['name']
                    result[name] = dict()
                    result[name]["kind"] = data['kind']
                    if "namespace" in data['metadata']:
                        result[name]['namespace'] = data['metadata']['namespace']
                    else:
                        result[name]['namespace'] = default_namespace
               except yaml.YAMLError as exc:
                  print(exc)
            else:
                try:
                   data = json.load(stream)
                   if data['kind'] == "List":
                      for item in data['items']:
                        name = item['metadata']['name']
                        result[name] = dict()
                        result[name]["kind"] = item['kind']
                        if "namespace" in item['metadata']:
                            result[name]['namespace'] = item['metadata']['namespace']
                        else:
                            result[name]['namespace'] = default_namespace
                   else:
                     name = data['metadata']['name']
                     result[name] = dict()
                     result[name]["kind"] = data['kind']
                     if "namespace" in data['metadata']:
                        result[name]['namespace'] = data['metadata']['namespace']
                     else:
                        result[name]['namespace'] = default_namespace
                except ValueError:
                   print "JSON decode error"
        return result
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
    if module.params['command'] == "apply":
        kube.apply(module.params['args'],module.params['template'])
    else:
        rc, out, err = module.run_command(kube.kubectl(), use_unsafe_shell=True)
        kube.get_output(rc, out, err)

from ansible.module_utils.basic import *

if __name__ == '__main__':
    main()
