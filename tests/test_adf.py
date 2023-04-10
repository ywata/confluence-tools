import pytest
import unittest
import jsonschema.schema
import json
import os

dir_path = os.path.dirname(os.path.realpath(__file__))
def test_create_adf_processor():
    with open(os.path.join(dir_path, "../spec/adf-schema.json"), "r") as f:
        schema_dict = json.load(f)
        jsc = jsonschema.schema.parse_json_schema(schema_dict)

        jsc= jsonschema.schema.normalize_schema((jsc))
        nodes = list(jsc.defn.keys())

        pass


