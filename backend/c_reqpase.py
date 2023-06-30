import json
import re
import uuid

from flask import abort, Response, request


class ParaErr(Exception):
    pass


ip_pattern = re.compile(
    r'^(?:(?:1[0-9][0-9]\.)|(?:2[0-4][0-9]\.)|(?:25[0-5]\.)|(?:[1-9][0-9]\.)|(?:[0-9]\.)){3}'
    r'(?:(?:1[0-9][0-9])|(?:2[0-4][0-9])|(?:25[0-5])|(?:[1-9][0-9])|(?:[0-9]))$')
url_pattern = re.compile(
    r'^(https?|ftp)://[-A-Za-z0-9+&@#/%?=~_|!:,.;]+[-A-Za-z0-9+&@#/%=~_|]$'
)


def type_url(x):
    try:
        if not (ip_pattern.match(x) or url_pattern.match(x)):
            return False
    except:
        return False
    return True


class Argument:
    def __init__(self, name, default=None, required=False, choices=None, type=str, save_none=False):
        self.name = name
        self.default = default
        self.required = required
        self.choices = choices
        self.type = type
        self.save_none = save_none

    def parse(self, value):
        if value is None and self.required:
            raise ParaErr("Parameter error: %s is required" % self.name)
        elif value is None and self.default is not None:
            if callable(self.default):
                value = str(self.default())
            else:
                value = self.default

        if self.choices and value not in self.choices:
            raise ParaErr("Parameter error: %s is not in ranged" % self.name)
        if self.type.__name__ == 'type_url':
            try:
                if not self.type(value):
                    raise ParaErr("Parameter error: %s type is not matched" % self.name)
            except:
                raise ParaErr("Parameter error: %s type is not matched" % self.name)
        elif not isinstance(value, self.type):
            raise ParaErr("Parameter error: %s type is not matched" % self.name)

        return value


class Parser:
    def __init__(self, save_none=False):
        self.arguments = []
        self.save_none = save_none

    def add_arguments(self, name, default=None, required=False, choices=None, type=str):
        self.arguments.append(Argument(name, default, required, choices, type))

    def parse(self) -> dict:
        """
        :return: if error occur, abort the request
        """
        ret, source = {}, {}
        if request.json:
            source.update(dict(request.json))
        if request.args:
            source.update(dict(request.args))
        for arg in self.arguments:
            try:
                val = arg.parse(source.get(arg.name))
                if val is not None:
                    ret[arg.name] = val
                elif arg.save_none:
                    ret[arg.name] = None
            except ParaErr as e:
                abort(Response(json.dumps({"msg": e.args[0], "data": None, "code": 3003004000,
                                           "requestId": source.get("requestId") or uuid.uuid4().hex},
                                          ensure_ascii=False), status=400, content_type='application/json'))
        return ret
