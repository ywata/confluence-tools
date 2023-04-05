import unittest
import json

import jsonschema.schema as sc
def test_get_jsonschema_for_adf():
    url = "https://unpkg.com/@atlaskit/adf-schema@25.2.3/dist/json-schema/v1/full.json"
    resp = ()

    assert resp is not None

def test_string_basic():
    input = '''{
  "definitions": {
    "string1": {
       "type": "string"
    }
  }
}   
'''
    dic = json.loads(input)
    res = sc.parse_json_schema(dic)
    assert res.ref_map['#/definitions/string1'] == sc.JString([])

def test_string_min_max():
    input = '''{
  "definitions": {
    "string1": {
       "type": "string",
       "minLength":1,
       "maxLength":3
    }
  }
}   
'''
    dic = json.loads(input)
    res = sc.parse_json_schema(dic)
    assert res.ref_map['#/definitions/string1'] == sc.JString([{"minLength":1, "maxLength":3}])



def test_string_integer():
    input = '''{
  "definitions": {
    "integer1": {
       "type": "integer"
    }
  }
}   
'''
    dic = json.loads(input)
    res = sc.parse_json_schema(dic)
    assert res.ref_map['#/definitions/integer1'] == sc.JInteger([])

def test_number_basic():
    input = '''{
  "definitions": {
    "number1": {
       "type": "number"
    }
  }
}   
'''
    dic = json.loads(input)
    res = sc.parse_json_schema(dic)
    assert res.ref_map['#/definitions/number1'] == sc.JNumber([])

def test_number_multipleOf():
    input = '''{
  "definitions": {
    "number1": {
       "type": "number",
       "multipleOf": 10
    }
  }
}   
'''
    dic = json.loads(input)
    res = sc.parse_json_schema(dic)
    assert res.ref_map['#/definitions/number1'] == sc.JNumber([{"multipleOf":10}])

def test_object_basic():
    input = '''{
  "definitions": {
    "object1": {
      "type": "object",
      "properties": {
        "number": { "type": "number" },
        "street_name": { "type": "string" },
        "street_type": { "enum": ["Street", "Avenue", "Boulevard"] }
        }
    }
  }
}   
'''
    dic = json.loads(input)
    res = sc.parse_json_schema(dic)
    val = res.ref_map['#/definitions/object1']
    assert (val == sc.JObject({'number':(sc.JNumber([]), False), 'street_name':(sc.JString([]),False), 'street_type':(sc.Enum(['Street', 'Avenue', 'Boulevard']), False)}, None))


def test_object_required():
    input = '''{
  "definitions": {
    "object1": {
      "type": "object",
      "properties": {
        "number": { "type": "number" },
        "street_name": { "type": "string" },
        "street_type": { "enum": ["Street", "Avenue", "Boulevard"] }
        },
      "required":["number"]
    }
  }
}   
'''
    dic = json.loads(input)
    res = sc.parse_json_schema(dic)
    val = res.ref_map['#/definitions/object1']
    assert (val == sc.JObject({'number':(sc.JNumber([]), True), 'street_name':(sc.JString([]),False), 'street_type':(sc.Enum(['Street', 'Avenue', 'Boulevard']), False)}, None))


def test_object_additionalProperty():
    input = '''{
  "definitions": {
    "object1": {
      "type": "object",
      "properties": {
        "number": { "type": "number" },
        "street_name": { "type": "string" },
        "street_type": { "enum": ["Street", "Avenue", "Boulevard"] }
        },
      "required":["number"],
      "additionalProperties" : true
    }
  }
}   
'''
    dic = json.loads(input)
    res = sc.parse_json_schema(dic)
    val = res.ref_map['#/definitions/object1']
    assert (val == sc.JObject({'number':(sc.JNumber([]), True), 'street_name':(sc.JString([]),False), 'street_type':(sc.Enum(['Street', 'Avenue', 'Boulevard']), False)}, True))


def test_array_simple():
    input = '''{
    "definitions": {
      "array1": {
        "type": "array",
        "items": {
          "type": "number"
      }
    }
  }
}   
'''
    dic = json.loads(input)
    res = sc.parse_json_schema(dic)
    assert res.ref_map['#/definitions/array1'] == sc.JArray([sc.JNumber([])])

def test_array_simple_with_minmaxItems():
    input = '''{
    "definitions": {
      "array1": {
        "type": "array",
        "items": {
          "type": "number"
        },
        "minItems":1,
        "maxItems":3
      }
   }
}   
'''
    dic = json.loads(input)
    res = sc.parse_json_schema(dic)
    assert res.ref_map['#/definitions/array1'] == sc.JArray([sc.JNumber([]), {"minItems":1}, {"maxItems":3}])

def test_array_anyOf():
    input = '''{
    "definitions": {
      "array1": {
        "type": "array",
        "items": {
          "anyOf":[
            {"type":"object"},
            {"type":"number"},
            {"type":"boolean"}
          ]
        }
      }
   }
}   
'''
    dic = json.loads(input)
    res = sc.parse_json_schema(dic)
    assert res.ref_map['#/definitions/array1'] == sc.JArray([sc.AnyOf([sc.JObject({}, None),sc.JNumber([]), sc.JBoolean([])])])


def test_array_allOf():
    input = '''{
    "definitions": {
      "array1": {
        "type": "array",
        "items": {
          "anyOf":[
            {"type":"object"},
            {"type":"number"}
          ]
        }
      }
   }
}
'''
    dic = json.loads(input)
    res = sc.parse_json_schema(dic)
    assert res.ref_map['#/definitions/array1'] == sc.JArray([sc.AnyOf([sc.JObject({}, None),sc.JNumber([]) ])])


def test_ref():
    input = '''{
    "definitions": {
      "array1": {
        "type": "array",
        "items": {
          "anyOf":[
            {"type":"object"},
            {"type":"number"}
          ]
        }
      }
   }
}
'''
    dic = json.loads(input)
    res = sc.parse_json_schema(dic)
    assert res.ref_map['#/definitions/array1'] == sc.JArray([sc.AnyOf([sc.JObject({}, None),sc.JNumber([]) ])])


