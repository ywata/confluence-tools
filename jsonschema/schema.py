import requests
import json
from dataclasses import dataclass

import pprint as pp


@dataclass()
class Schema():
    json_schema: str
    namespace: str
    ref: str
    definitions:dict # type -> definition
    ref_map : dict # ref to type

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
class JInteger():
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

def parse_simple_type(typ, val, constructor, defined_keys):
    assert typ in ['integer', 'number', 'string', 'boolean']
    res = {}
    for (key, v) in val.items():
        if key != 'type':
            res[key] = v
    if res == {}:
        return constructor([])
    else:
        return constructor([res])


def parse_type(val):
    if val['type'] == 'object':
        fields = []
        #pp.pprint((list(val.keys()), list(val['properties'].keys())))
        req = []
        addProp = None
        if 'required' in val:
            req = val['required']
        if 'additionalProperties' in val:
            addProp = val['additionalProperties']

        fields = {}
        if 'properties' in val:
            for (key, constraints) in val['properties'].items():
                cond = parse_definition(constraints)
                fields[key] = (cond, key in req)

        return JObject(fields, addProp)

    elif val['type'] == 'array':
        defined_keys = ['items', 'prefixItems', 'contains', 'minContains', 'maxContains', 'minItems', 'maxItems', 'uniqueItems ']
        conditions = []
        for (key, constraints) in val.items():
            if key == 'type': # skip 'type'
                continue
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
        defined_keys = ['minLength', 'maxLength']
        res = parse_simple_type(val['type'], val, JString, defined_keys)
        return res
    elif val['type'] == 'integer':
        assert len(val) == 1
        defined_keys = []
        res = parse_simple_type(val['type'], val, JInteger, defined_keys)
        return res
    elif val['type'] == 'number':
        defined_keys = ['minumum', 'maxmum', 'exclusiveMinum', 'exclusiveMaxmum']
        res = parse_simple_type(val['type'], val, JNumber, defined_keys)
        return res
    elif val['type'] == 'boolean':
        assert len(val) == 1
        defined_keys = []
        res = parse_simple_type(val['type'], val, JBoolean, defined_keys)
        return res

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
    definitions = {}
    ref_map = {}
    for (key, val) in defs.items():
        ref_name = f"#/definitions/{key}"
        defn = parse_definition(val)
        typ = None
        match defn :
            case JObject(attr, addProp):
                typ = ref_name
            case JArray(_):
                typ = ref_name
            case AllOf(_):
                typ = ref_name
            case AnyOf(_):
                typ = ref_name
            case JString(_):
                typ = ref_name
            case JInteger(_):
                typ = ref_name
            case JNumber(_):
                typ = ref_name
            case JBoolean(_):
                typ = ref_name
            case _:
                assert False, "This case should not happen."
        definitions[typ] = defn
        ref_map[ref_name] = defn
    return (definitions, ref_map)

def parse_json_schema(json_schema_defn):
    schema_name, description, definitions, ref_map = None, None, None, None
    ref_name = None
    if '$schema' in json_schema_defn:
        schema_name = json_schema_defn['$schema']
    if "$ref" in json_schema_defn:
        ref_name = json_schema_defn['$ref']
    if "description" in json_schema_defn:
        description = json_schema_defn['description']
    if 'definitions' in json_schema_defn:
        (definitions, ref_map) = parse_definitions(json_schema_defn['definitions'])

    return Schema(schema_name, "", ref_name, definitions, ref_map)


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

def get_dependencies(schema, start, top_level, tmp:list):
    match start:
        case JObject(obj, _):
            for (p, v) in obj.items():
                rs = get_dependencies(schema, v, False, [])
                tmp = tmp + rs
            return tmp
        case (JObject(obj, _), _):
            for (p, v) in obj.items():
                rs = get_dependencies(schema, v, False, [])
                tmp = tmp + rs
            return tmp

        case JArray(arr):
            for a in arr:
                rs = get_dependencies(schema, a, False, [])
                tmp = tmp + rs
            return tmp
        case (JArray(arr), _):
            for a in arr:
                rs = get_dependencies(schema, a, False, [])
                tmp = tmp + rs
            return tmp
        case AnyOf(arr):
            ()
            for a in arr:
                rs = get_dependencies(schema, a, False, [])
                tmp = tmp + rs
            return tmp
        case AllOf(arr):
            for a in arr:
                rs = get_dependencies(schema, a, False, [])
                tmp = tmp + rs
            return tmp
        case Ref(ar):
            return tmp + [ar]
        case d:
            if type(d) == dict:
                for (k, val) in d.items():
                    rs = get_dependencies(schema, val, False, [])
                    tmp = tmp + rs
                return tmp
            else:
                return []
            return []

