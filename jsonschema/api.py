from jsonschema.schema import JObject, JString, Ref, JArray, Schema, Enum, AllOf, AnyOf, OneOf
from dataclasses import make_dataclass, field, dataclass

import pprint as pp

def has_type(schema):
    match schema:
        case JObject(attr, _):
            if 'type' in attr:
                match attr['type']:
                    case (Enum(enm), _):
                        if len(enm) == 1:
                            return enm[0]
    return None

def reverse_ref(name, schema):
    rev_ref = {}
    match schema:
        case AllOf(constraints):
            rev_ref[constraints[0].ref] = (name, "AllOf")
        case AnyOf(constraints):
            for c in constraints:
                rev_ref[c.ref] = (name, "AnyOf")
        case JArray(constraints):
            return reverse_ref(name, constraints[1])
        case _:
            pass
    return rev_ref

def classify_definitions(schema:Schema):
    conditions, types = [], []
    for (ref_name, schema) in schema.ref_map.items():
        typ = has_type(schema)
        if typ:
            types.append(ref_name)
            # api = jsonschema.api.generate_api(adf_schema, ref_name)
        else:
            conditions.append(ref_name)
    return (types, conditions)
import faulthandler

def merge_array(schema, prims, auxs):
    new_conditions = []
    for elm in auxs:
        if elm not in prims:
            match elm:
                case {}:
                    new_conditions.append(elm)
                case Ref(ref):
                    ref_def = schema.ref_map[ref]
                    new_conditions.append(ref_def)
            pass
    return new_conditions


def merge_conditions(schema, ref_name, primary:JObject, aux:JObject):
    assert hasattr(aux, 'attributes')
    new_condition = []
    if hasattr(primary, 'attributes'):
        #pp.pprint((primary, aux))
        for (key, (aux_cond, addProp)) in aux.attributes.items():
            if key in primary.attributes:
                primary_cond = primary.attributes[key]
                match primary_cond, aux_cond:
                    case (JArray(consp), addpp), JArray(consa):
                        new_condition = merge_array(schema, consp, consa)
                    case _, _:
                        pass
    else:
        match primary:
            case [{}]:
                pass
    return new_condition

def normalize_schema(schema:Schema):
    (types, conditions) = classify_definitions(schema)
    rest = []
    for ref_name in conditions:
        curr_schema = schema.ref_map[ref_name]
        match curr_schema:
            case AllOf([Ref(ref), jobj]):
                match jobj:
                    case JObject({},adp):
                        target_schema = schema.ref_map[ref]
                        new_schema = merge_conditions(schema, ref_name, target_schema, jobj)
                        schema.ref_map[ref] = new_schema
                    case _:
                        pass
            case _:
                rest.append(ref_name)

    return

def generate_api(adf_schema, ref_name:str):
    target = adf_schema.ref_map[ref_name]
    typ = target.attributes['type'][0].enums[0]
    @dataclass
    class base():
        pass
        adf_schema
        schema: Schema = adf_schema
    def set_text(self, text):
        self.text = text
    def add_mark(self, mark):
        self.marks.append(mark)
    def add_content(self, content):
        self.content.append(content)
    def set_text(self, text):
        self.text = text
    def set_attr(self, key, value):
        self.content[key] = value
    match target:
        case (JObject({'type':_})):
            fields = [('type', str, field(default_factory=lambda:typ)),
                      ('ref_name', str, field(default=ref_name) )]
            namespace = {}
            if 'version' in target.attributes:
                version = target.attributes['version']
                fields.append(('version', int, field(default_factory=lambda:version[0].enums[0])))

            if 'content' in target.attributes:
                fields.append(('content', list, field(default_factory=lambda:[])))
                namespace['add_content'] = lambda self, content:self.add_content(content)

            if 'marks' in target.attributes:
                fields.append(('marks', list, field(default_factory=lambda: [])))
                namespace['add_mark'] = lambda self, mark: self.add_mark(mark)

            if 'text' in target.attributes:
                fields.append(('text', str, field(default=None)))
                namespace['set_text'] = lambda self, text:self.set_text(text)

            if 'attrs' in target.attributes:
                fields.append(('attr', dict, field(default_factory=lambda:{})))
                namespace['set_attr'] = lambda self, key, value : self.set_attr(key, value)
            api = make_dataclass(typ, fields, bases = (base,), namespace=namespace)
            return api

        case JObject(attr):
            pp.pprint(attr)