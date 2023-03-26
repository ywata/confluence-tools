import logging

from jsonschema.schema import JObject, Schema, AnyOf, AllOf, JArray, Enum, JString, Ref


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
    matched = match_keys(jobject, target)
    if matched is None:
        return None

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
