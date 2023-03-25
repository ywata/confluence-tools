import dataclasses

import requests
import json
from dataclasses import dataclass
from functools import reduce
import logging

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
    definitions = {}
    ref_map = {}
    for (key, val) in defs.items():
        ref_name = f"#/definitions/{key}"
        defn = parse_definition(val)
        typ = None
        match defn :
            case JObject(attr, addProp):
                typ = attr['type'][0].enums[0]
            case JArray(_):
                typ = ref_name
            case AllOf(_):
                typ = ref_name
            case AnyOf(_):
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

def match_keys(jobject : JObject, target):
    add_prop = jobject.additionalProperties
    # check to see if all the keys in target matches to a key defined in jobject
    # OR add_prop is allowed
    for k in target.keys():
        if k in jobject.attributes:
            continue
        if add_prop:
            continue
        else:
            return None
    for (k, (_, required)) in jobject.attributes.items():
        if k in target:
            continue
        else:
            if required:
                return None
    return target
def parse_anyof(schema:Schema, conds:AnyOf, target:dict):
    match conds:
        case AnyOf(constraints):
            for c in constraints:
                parsed = parse_structure(schema, c, target)
                if parsed is not None:
                    return target
    return None
def parse_allof(schema:Schema, conds:AllOf, target:dict):
    match conds:
        case AllOf(constraints):
            for c in constraints:
                parsed = parse_structure(schema, c, target)
                if parsed is None:
                    logging.debug(f"parse_allof() failed with {conds} {dict}")
                    return None

    return target

def parse_array(schema, curr, target:dict):
    assert type(target) == dict
    match curr:
        case (JArray(attrs),ap):
            for attr in attrs:
                parsed = parse_structure(schema, attr, target)
                if parsed is None:
                    logging.debug(f"parse_array() failed {attr} {target}")
                    return None
    return target
def parse_jobject(schema, jobject:JObject, target:dict):
    assert type(target) == dict
    match_keys(jobject, target)

    for (k, constraint) in jobject.attributes.items():
        try:
            parsed = parse_structure(schema, constraint, target[k])
            if parsed is None:
                logging.debug(f"parse_jobject() failed {constraint} {target[k]}")
                return None
        except Exception as ex:
            logging.debug(f"parse_jobject() failed {constraint} {k}")

    return target
def parse_enum(schema, curr, struct):
    match curr:
        case (Enum(es), _):
            if struct in es:
                return struct
            else:
                logging.debug(f"parse_jobject() failed {curr} {struct}")
                return None

def parse_string(schema, curr, target):
    match curr:
        case JString(constraints):
            for c in constraints:
                parsed = parse_structure(schema, c, target)
                if parsed is None:
                    logging.debug(f"parse_jobject() failed {c} {target[k]}")
                    return None
            return target
def parse_ref(schema, curr, struct):
    match curr:
        case Ref(ref):
            ref_constraint = schema.ref_map[ref]
            parsed = parse_structure(schema, ref_constraint, struct)
            if parsed is None:
                logging.debug(f"parse_ref() failed {curr} {struct}")
            return parsed
def parse_structure(schema: Schema, curr, struct):
    match curr:
        case JObject(attr, addProp):
            assert type(struct) == dict
            parsed = parse_jobject(schema, curr, struct)
            return parsed
        case (JObject(attr, addProp), ap):
            assert type(struct) == dict
            parsed = parse_jobject(schema, curr, struct)
            return parsed
        case (JArray(constraints), _):
            if type(struct) == dict:
                parsed = parse_array(schema, curr, struct)
                return parsed
            elif type(struct) == list:
                for l in struct:
                    parsed = parse_structure(schema, curr, l)
                    if parsed is None:
                        logging.debug(f"{curr} {l}")
                        return None
                return struct
        case AnyOf(constraints):
            parsed = parse_anyof(schema, curr, struct)
            return parsed
        case AllOf(constraints):
            parsed = parse_allof(schema, curr, struct)
            return parsed
        case (Enum(es), _):
            parsed = parse_enum(schema, curr, struct)
            return parsed
        case Ref(ref):
            parsed = parse_ref(schema, curr, struct)
            return parsed
        case (JString(_), _):
            parse = parse_string(schema, curr[0], struct)
            return parse
        case _:
            assert False, f"parse_adf() require more implementation {curr}"

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

