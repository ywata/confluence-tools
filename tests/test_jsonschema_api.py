import pytest
import os
import jsonschema.schema
from jsonschema.schema import *
import jsonschema.api
import json

import pprint as pp
dir_path = os.path.dirname(os.path.realpath(__file__))
def show_named_object(obj):
    match obj:
        case JNamedObject(name, schema, _):
            print(f"JNamedObject: {obj}")
def show_object(obj):
    match obj:
        case JObject(schema, _):
            print(f"JObject: {obj}")
        case JNamedObject(_,_,_):
            pass
        case _:
            print(f"Other: {obj}")
def test_create_adf_processor():
    with open(os.path.join(dir_path, "../spec/adf-schema.json"), "r") as f:
        schema_dict = json.load(f)
        jsc = jsonschema.schema.parse_json_schema(schema_dict)

        #jsc = jsonschema.schema.normalize_schema((jsc))
        jsonschema.api.traverse_schema(jsc, show_named_object)
        jsonschema.api.traverse_schema(jsc, show_object)

    return

def test_generate_api():
    with open(os.path.join(dir_path, "../spec/adf-schema.json"), "r") as f:
        schema_dict = json.load(f)
        jsc = jsonschema.schema.parse_json_schema(schema_dict)
        defs = jsonschema.api.generate_api(jsc)

    return