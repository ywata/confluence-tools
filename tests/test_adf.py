import pytest
import unittest
import jsonschema.schema
import json

def test_create_adf_processor():
    with open("../spec/adf-schema.json", "r") as f:
        schema_dict = json.load(f)
        res = jsonschema.schema.parse_json_schema(schema_dict)
        pass


