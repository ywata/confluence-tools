import logging
from dataclasses import dataclass


@dataclass()
class JsonSchema():
    schema: str
    ref: str
    defn: object


@dataclass()
class RestrictionX():
    pass


@dataclass()
class Condition():
    condition: list


@dataclass()
class JNamedObject():
    name: str
    attr: dict  # of (name, restriction)
    addp: bool


@dataclass()
class JObject():
    attr: dict  # of (name, restriction)
    addp: bool


@dataclass()
class JNumber():
    cnst: dict  # of (name, restriction)


@dataclass()
class JInteger():
    cnst: dict  # of (name, restriction)


@dataclass()
class JBoolean():
    cnst: dict  # of (name, restriction)


@dataclass()
class JNull():
    cnst: dict  # This should always be []


@dataclass()
class JArray():
    cnst: dict


@dataclass()
class JString():
    cnst: dict


@dataclass()
class AllOf():
    cnst: list  # of Restrictions


@dataclass()
class AnyOf():
    cnst: list  # of Restrictions


@dataclass()
class OneOf():
    cnst: list  # of Restrictions


@dataclass()
class Ref():
    ref: str


@dataclass()
class Enum():
    enums: list


def parse_simple_type(schema_dict, accept_keys, cnstr):
    assoc = {}
    temp_list = ['type', '$id', '$schema', 'description']
    for k in accept_keys:
        if k in schema_dict:
            assoc[k] = schema_dict[k]
    # check to see if unknown key word is used
    for key in schema_dict:
        if key not in accept_keys and key not in temp_list:
            logging.warning(f"{key} is not handled in {accept_keys}")
            assert False, f"{key} is not handled in {accept_keys}"

    return cnstr(assoc)


# ignore_tags != [] iff schema_dict is top level JSON object.
def parse_string(schema_dict):
    accept_keys = ['minLength', 'maxLength', 'pattern']
    return parse_simple_type(schema_dict, accept_keys, JString)


def parse_number(schema_dict):
    accept_keys = ['minimum', 'maximum']
    return parse_simple_type(schema_dict, accept_keys, JNumber)


def parse_integer(schema_dict):
    accept_keys = []
    return parse_simple_type(schema_dict, accept_keys, JInteger)


def parse_null(schema_dict):
    accept_keys = []
    return parse_simple_type(schema_dict, accept_keys, JNull)


def parse_boolean(schema_dict):
    accept_keys = []
    return parse_simple_type(schema_dict, accept_keys, JBoolean)


def parse_array(schema_dict, ignore_tags):
    assert schema_dict['type'] == 'array'
    res = {}
    for (key, val) in schema_dict.items():
        if 'type' == key:
            continue
        if key in ignore_tags:
            continue
        if type(val) == dict:
            res[key] = parse_schema(val, [])
        elif type(val) == list:
            res[key] = list(map(lambda v:parse_schema(v, []), val))
        else:
            res[key] = val
    return JArray(res)


def parse_enum(schema_dict) -> Enum:
    assert 'enum' in schema_dict
    return Enum(schema_dict['enum'])


def parse_ref(schema_dict) -> Ref:
    assert '$ref' in schema_dict
    return Ref(schema_dict['$ref'])


def parse_properties(schema_dict: dict, required, addProp):
    name = None
    if 'type' in schema_dict and 'enum' in schema_dict['type']:
        name = schema_dict['type']['enum'][0]
    res = {}
    for (key, val) in schema_dict.items():
        if key == 'type':
            continue
        res[key] = (parse_schema(val, []), key in required)

    if name:
        return JNamedObject(name, res, addProp)
    else:
        return JObject(res, addProp)


def parse_object(schema_dict: dict, ignore_tags=[]):
    # accept_keys = ['properties','required']
    required, addtionalProp, props = [], False, None
    if 'properties' in schema_dict:
        cnstr = JObject
        if 'required' in schema_dict:
            required = schema_dict['required']
        if 'additionalProperties' in schema_dict:
            addtionalProp = schema_dict['additionalProperties']
        props = parse_properties(schema_dict['properties'], required, addtionalProp)
        return props
    else:
        new_dict = {}
        for (key, val) in schema_dict.items():
            if key not in ignore_tags:
                new_dict[key] = val
        if 'type' in new_dict:
            if new_dict['type'] == 'object':
                del new_dict['type']
                return JObject(new_dict, False)
            else:
                res = parse_schema(new_dict, [])


def parse_predicate(schema_lst: dict, cnstr):
    res = []
    for sc in schema_lst:
        ret = parse_schema(sc, [])
        res.append(ret)
    return cnstr(res)


def parse_schema(schema_dict: dict, ignore_tags):
    assert type(schema_dict) == dict
    res = None
    if 'type' in schema_dict:
        if schema_dict['type'] == 'string':
            res = parse_string(schema_dict)
        elif schema_dict['type'] == 'array':
            res = parse_array(schema_dict, ignore_tags)
        elif schema_dict['type'] == 'number':
            res = parse_number(schema_dict)
        elif schema_dict['type'] == 'boolean':
            res = parse_boolean(schema_dict)
        elif schema_dict['type'] == 'integer':
            res = parse_integer(schema_dict)
        elif schema_dict['type'] == 'null':
            res = parse_null(schema_dict)
        elif schema_dict['type'] == 'object':
            res = parse_object(schema_dict, ignore_tags)
        else:
            return JObject({}, False)
    elif 'allOf' in schema_dict:
        res = parse_predicate(schema_dict['allOf'], AllOf)
    elif 'anyOf' in schema_dict:
        res = parse_predicate(schema_dict['anyOf'], AnyOf)
    elif 'oneOf' in schema_dict:
        res = parse_predicate(schema_dict['oneOf'], OneOf)
    elif 'not' in schema_dict:
        pass  # not implemented]
    elif 'enum' in schema_dict:
        res = parse_enum(schema_dict)
    elif '$ref' in schema_dict:
        res = parse_ref(schema_dict)

    return res


any_keys = ['type', 'enum', 'id']


def parse_json_schema(json_schema_dict):
    id, schema, descr, ref = None, None, None, None
    json_schema = JsonSchema(None, None, None)

    top_level_items = [('$id', lambda scm: scm),
                       ('$schema',
                        lambda scm:
                        JsonSchema(json_schema_dict['$schema'], scm.ref, scm.defn)),
                       ('description', lambda scm: scm),
                       ('$ref', lambda scm: JsonSchema(scm.schema, json_schema_dict['$ref'], scm.defn))]
    ignore_tags = list(map(lambda pair: pair[0], top_level_items))
    jschema = json_schema
    for (tag, fun) in top_level_items:
        if tag in json_schema_dict:
            jschema = fun(jschema)
    if 'definitions' in json_schema_dict:
        defn = {}
        for (key, val) in json_schema_dict['definitions'].items():
            name = f"#/definitions/{key}"
            res = parse_schema(val, [])
            defn[name] = res

        jschema.defn = defn
    elif 'type' in json_schema_dict:
        res = parse_schema(json_schema_dict, ignore_tags)
        jschema.defn = res
    return jschema
def merge_all_of_properties(props1, props2):
    res = {}
    for key in props1.keys() | props2.keys():
        if key in props1 and key in props2:
            v1 = props1[key]
            v2 = props2[key]
            match v1, v2:
                case (JArray(prop1), ap1), (JArray(prop2), ap2):
                    return JArray(prop1 | prop2, ap1)
                case _, _:
                    assert False, "merge_all_op_properties()"
    return res


def merge_constraints(schema:dict) -> dict:
    match schema:
        case [JNamedObject(name, props, addProp),JObject(props2, addProp2)]:
            return JNamedObject(name, merge_all_of_properties(props, props2), addProp)
    return schema

def map_over_dict(d: dict, f) -> dict:
    res = {}
    for (key, val) in d.items():
        res[key] = f(val)
    return res
def normalize(val: dict, schema:JsonSchema) -> dict:
    match val:
        case (obj, addProp):
            if type(addProp) == bool:
                return (normalize(obj, schema), addProp)
            else:
                return (normalize(obj, schema), normalize(addProp, schema))
        case JObject(props, addProp):
            res = normalize(props, schema)
            return JObject(res, addProp)
        case JNamedObject(name, props, addProp):
            res = normalize(props, schema)
            return JNamedObject(name, res, addProp)
        case JArray(constr):
            res1 = normalize(constr, schema)
            res2 = merge_constraints(res1)
            return JArray(res2)
        case JString(props)|JNumber(props)|JInteger(props)|JBoolean(props)|JNull(props)|Enum(props):
            return val
        case AnyOf(ls):
            return AnyOf(list(map(lambda x: normalize(x, schema), ls)))
        case AllOf(ls):
            res = AllOf(list(map(lambda x: normalize(x, schema), ls)))
            return res
        case OneOf(ls):
            return OneOf(list(map(lambda x: normalize(x, schema), ls)))
        case Ref(ref):
            r = schema.defn[ref]
            return r
        case {}:
            for (key, v) in val.items():
                res = normalize(v, schema)
                val[key] = res
            return val
        case any:
            return any


def normalize_schema(schema: JsonSchema) -> JsonSchema:
    if schema.defn:
        for (key, val) in schema.defn.items():
            schema.defn[key] = normalize(val, schema)
        return schema
    else:
        return schema
