#!/usr/bin/python

import json

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
     arguments:  -f <something already on the host>
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
        filename = self.module.params['command']
        args = self.module.params['args']
        template = self.module.params['template']

        command = "kubectl %s %args" % (filename, args)


def main():
    module = AnsibleModule(
            argument_spec = dict(
                command         = dict(required=True),
                arguments       = dict(required=False, default=''),
                template        = dict(required=False, default='')
                ),
            supports_check_mode = False
            )


    kube = Kubectl(module)
    rc, out, err = module.run_command(kube.kubectl, use_unsafe_shell=True)
    kube.get_output(rc, out, err)

from ansible.module_utils.basic import *

if __name__ == '__main__':
    main()
