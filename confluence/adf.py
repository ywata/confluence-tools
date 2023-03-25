import dataclasses

import requests
import json
from dataclasses import dataclass
from functools import reduce

import pprint as pp
@dataclass()
class RestrictionX():
    pass

@dataclass()
class Condition():
    condition: dict
@dataclass()
class JObject():
    attributes : list # of (name, restriction)
    additionalProperties : bool
@dataclass()
class JNumber():
    constraints : list # of (name, restriction)
@dataclass()
class JBoolean():
    constraints : list # of (name, restriction)

@dataclass()
class JArray():
    constraints : list
@dataclass()
class JString():
    constraints : list
@dataclass()
class AllOf():
    constraints : list # of Restrictions
@dataclass()
class AnyOf():
    constraints : list # of Restrictions
@dataclass()
class OneOf():
    constraints : list # of Restrictions

@dataclass()
class Ref():
    ref : str
@dataclass()
class Enum():
    enums : list

def parse_type(val):
    if val['type'] == 'object':
        fields = []
        assert 'properties' in val
        #pp.pprint((list(val.keys()), list(val['properties'].keys())))
        req = []
        addProp = None
        if 'required' in val:
            req = val['required']
        if 'additionalProperties' in val:
            addProp = val['additionalProperties']

        fields = {}
        for (key, constraints) in val['properties'].items():
            cond = parse_definition(constraints)
            field = (key, cond, key in req)
            fields[key] = (cond, key in req)

        return JObject(fields, addProp)

    elif val['type'] == 'array':
        del val['type']
        conditions = []
        for (key, constraints) in val.items():
            if type(constraints) == dict:
                cond = parse_definition(constraints)
            elif type(constraints) == list:
                conds = []
                for c in constraints:
                    cnst = parse_definition(c)
                    conds.append(cnst)
                cond = JArray(conds)
            else:
                cond = {key: constraints}
            conditions.append(cond)
        return JArray(conditions)
    elif val['type'] == 'string':
        return JString([])
    elif val['type'] == 'number':
        return JNumber([])
    elif val['type'] == 'boolean':
        return JBoolean([])
    else:
        return Condition(val)
        #pp.pprint(val)

def parse_definition(val):
    assert(type(val) == dict)
    if 'type' in val:
        #assert val['type'] == 'object' or val['type'] == 'array'
        res = parse_type(val)
        return res
    elif len(val) == 1 and ('allOf' in val or 'anyOf' in val):
        constructor = None
        tag = None
        if 'allOf' in val:
            constructor = AllOf
            tag = 'allOf'
        elif 'anyOf' in val:
            constructor = AnyOf
            tag = 'anyOf'
        constraints = []
        for c in val[tag]:
            constraint = parse_definition(c)
            constraints.append(constraint)
        return constructor(constraints)
    elif val == {}:
        return {}
    elif len(val) == 1 and 'enum' in val:
        return Enum(val['enum'])
    elif len(val) == 1 and '$ref' in val:
        return Ref(val['$ref'])
    else:
        pp.pprint(val)


def parse_definitions(defs:dict):
    print()
    definitions = []
    for (key, val) in defs.items():
        ref_name = f"#/definitions/{key}"
        defn = parse_definition(val)
        definitions.append((ref_name, defn))
    return definitions

def parse_json_schema(json_schema_defn):
    schema_name = None
    description = None
    definitions = None
    if '$schema' in json_schema_defn:
        schema_name = json_schema_defn['$schema']
    if "description" in json_schema_defn:
        description = json_schema_defn['description']
    if 'definitions' in json_schema_defn:
        definitions = parse_definitions(json_schema_defn['definitions'])

    print(schema_name, description)
    ref_to_defn = dict(definitions)
    for (key, val) in ref_to_defn.items():
        pp.pprint(val)

    return (schema_name, description, definitions)




def generate_adf_processor():
    url = "https://unpkg.com/@atlaskit/adf-schema@25.2.3/dist/json-schema/v1/full.json"
    headers = {
        "Accept": "application/json"
    }
    request_url = f"{url}"
    resp = requests.request(
        "GET",
        request_url,
        headers=headers,
    )
    if resp.status_code != 200:
        return None

    schema_dic = json.loads(resp.text)
    try:
        data_class = parse_json_schema(schema_dic)
        return
    except Exception as ex:
        print(ex)
        import sys
        sys.exit(1)

