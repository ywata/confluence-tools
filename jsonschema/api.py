from jsonschema.schema import *
from dataclasses import make_dataclass, field, dataclass

import pprint as pp

def traverse_schema(schema:JsonSchema, fun):
    if schema.schema:
        fun(schema.schema)
    if schema.ref:
        fun(schema.ref)
    if schema.defn:
        for (key, val) in schema.defn.items():
            fun(val)

def generate_api(schema:JsonSchema):
    top = schema.ref
    top_schema = schema.defn[top]
    aliases = top_schema.attributes['content'][0].constraints['items'].constraints
    for alias in aliases:
        alias_schema = schema.defn[alias.ref]
        normalized_schema = replace_ref(alias_schema, schema)
        print(alias)
        pp.pprint(normalized_schema)

    return
