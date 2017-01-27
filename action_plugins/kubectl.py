#!/usr/bin/python
#
# Copyright 2015 Peter Sprygada <psprygada@ansible.com>
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.
#
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible.errors import AnsibleError
from ansible.plugins.action import ActionBase
from ansible.module_utils._text import to_bytes, to_native, to_text

class ActionModule(ActionBase):
    def run(self, tmp=None, task_vars=None):
        command  = self._task.args.get('command', None)
        args = self._task.args.get('args', None)
        template = self._task.args.get('template', None)
        template_data = None
        result = super(ActionModule, self).run(tmp, task_vars)

        if template:
            try:
                template = self._find_needle('templates', template)
            except AnsibleError as e:
                result['failed'] = True
                result['msg'] = to_native(e)
                return result

            b_source = to_bytes(template)

            try:
                with open(b_source, 'r') as f:
                    template_data = to_text(f.read())
                    self._templar.template(template_data, preserve_trailing_newlines=True, escape_backslashes=False, convert_data=False)

            except Exception as e:
                result['failed'] = True
                result['msg'] = type(e).__name__ + ": " + str(e)
                return result


        self._task.args['template'] = template_data
        result.update(self._execute_module(module_name='kubectl', module_args=self._task.args, task_vars=task_vars))
        return result