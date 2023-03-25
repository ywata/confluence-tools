import requests
import confluence.adf
from confluence.adf import parse_definition, JObject, JArray, AllOf, AnyOf, Ref, Enum
def test_create_adf_processor():
    res = confluence.adf.generate_adf_processor()
    return

def test_parse_definition_object_type():
    defn = {
        'type' : 'object',
        "properties" : {
            'type': {'enum':["text"]}
        },
        'additionalProperties': False,
        'required':['type']
    }
    res = parse_definition(defn)

    assert res == JObject({'type': (Enum(['text']), True)}, False)

def test_parse_definition_object_additionalProperty_True():
    defn = {
        'type' : 'object',
        "properties" : {
            'type': {'enum':["text"]}
        },
        'additionalProperties': True,
        'required':['type']
    }
    res = parse_definition(defn)
    assert res == JObject({'type': (Enum(['text']), True)}, True)

def test_parse_definition_object_non_required():
    defn = {
        'type' : 'object',
        "properties" : {
            'type': {'enum':["text"]}
        },
        'additionalProperties': True,
        'required':[]
    }
    res = parse_definition(defn)
    assert res == JObject({'type':(Enum(['text']), False)}, True)


def test_parse_definition_array_in_properties():
    defn = {
        'type' : 'object',
        "properties" : {
            'type': {'enum':["text"]},
            'marks':{'type':'array'}
        },
    }
    res = parse_definition(defn)

    assert res == JObject({'type':(Enum(['text']), False),
                           'marks':(JArray([]), False)}, None)
    #assert res == JObject([('type', Enum(['text']), False),
    #                       ('marks', JArray([]), False)], None)

def test_parse_definition_array_in_object():
    defn = {
        'type' : 'object',
        'properties':{
            'content':{
                'type':'array',
                'items':{
                    'anyOf':[
                        {'$ref':'path'}
                    ]
                }
            }
        }
    }
    res = parse_definition(defn)

    assert res == JObject({'content':(JArray([(AnyOf([Ref('path')]))]), False)}, None)
    #assert res == JObject([('content', JArray([(AnyOf([Ref('path')]))]), False)], None)

