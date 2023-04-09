import unittest
import json

import jsonschema.schema as sc
from jsonschema.schema import *
def test_top_level_string():
    input = '''{
  "$id": "https://example.com/address.schema.json",
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "description": "An address similar to http://microformats.org/wiki/h-card",
  "type": "string",
  "minLength": 2,
  "maxLength": 3
}
'''
    dic = json.loads(input)
    res = sc.parse_json_schema(dic)
    assert res.defn == sc.JString({'minLength':2, 'maxLength':3})
def test_top_level_number():
    input = '''{
  "$id": "https://example.com/address.schema.json",
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "description": "An address similar to http://microformats.org/wiki/h-card",
  "type": "number"
}
'''
    dic = json.loads(input)
    res = sc.parse_json_schema(dic)
    assert res.defn == sc.JNumber({})
def test_top_level_integer():
    input = '''{
  "$id": "https://example.com/address.schema.json",
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "description": "An address similar to http://microformats.org/wiki/h-card",
  "type": "integer"
}
'''
    dic = json.loads(input)
    res = sc.parse_json_schema(dic)
    assert res.defn == sc.JInteger({})
def test_top_level_boolean():
    input = '''{
  "$id": "https://example.com/address.schema.json",
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "description": "An address similar to http://microformats.org/wiki/h-card",
  "type": "boolean"
}
'''
    dic = json.loads(input)
    res = sc.parse_json_schema(dic)
    assert res.defn == sc.JBoolean({})
def test_top_level_null():
    input = '''{
  "$id": "https://example.com/address.schema.json",
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "description": "An address similar to http://microformats.org/wiki/h-card",
  "type": "null"
}
'''
    dic = json.loads(input)
    res = sc.parse_json_schema(dic)
    assert res.defn == sc.JNull({})


def test_top_level_object():
    input = '''{
  "$id": "https://example.com/address.schema.json",
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "description": "An address similar to http://microformats.org/wiki/h-card",
  "type": "object"
}
'''
    dic = json.loads(input)
    res = sc.parse_json_schema(dic)
    assert res.defn == sc.JObject({}, False)

def test_top_level_object_with_properties():
    input = '''{
  "$id": "https://example.com/address.schema.json",
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "description": "An address similar to http://microformats.org/wiki/h-card",
  "type": "object",
  "properties":{
         "type": {
          "enum": [
            "text"
          ]
        },
        "text": {
          "type": "string",
          "minLength": 1
        }
  }
}
'''
    dic = json.loads(input)
    res = sc.parse_json_schema(dic)
    assert res.defn == sc.JNamedObject('text', {'text': (sc.JString({'minLength':1}), False)}, False)

def test_top_level_object_with_multiple_properties():
    input = '''{
  "$id": "https://example.com/address.schema.json",
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "description": "An address similar to http://microformats.org/wiki/h-card",
  "type": "object",
  "properties":{
         "type": {
          "enum": [
            "text"
          ]
        },
        "text": {
          "type": "string",
          "minLength": 1
        },
        "note": {
          "type": "number"
        }
  }
}
'''
    dic = json.loads(input)
    res = sc.parse_json_schema(dic)
    assert res.defn == sc.JNamedObject('text', {'text': (sc.JString({'minLength':1}), False),
                                                 'note': (sc.JNumber({}), False),
                                                 }, False)



def test_top_level_object_with_required():
    input = '''{
  "$id": "https://example.com/address.schema.json",
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "description": "An address similar to http://microformats.org/wiki/h-card",
  "type": "object",
  "properties":{
         "type": {
          "enum": [
            "text"
          ]
        },
        "text": {
          "type": "string",
          "minLength": 1
        }
  },
  "required":["text"]
}
'''
    dic = json.loads(input)
    res = sc.parse_json_schema(dic)
    assert res.defn == sc.JNamedObject('text', {'text': (sc.JString({'minLength':1}), True)}, False)

def test_top_level_object_with_additionalProperties():
    input = '''{
  "$id": "https://example.com/address.schema.json",
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "description": "An address similar to http://microformats.org/wiki/h-card",
  "type": "object",
  "properties":{
         "type": {
          "enum": [
            "text"
          ]
        },
        "text": {
          "type": "string",
          "minLength": 1
        }
  },
  "additionalProperties" : true
}
'''
    dic = json.loads(input)
    res = sc.parse_json_schema(dic)
    assert res.defn == sc.JNamedObject('text', {'text': (sc.JString({'minLength':1}), False)}, True)

def test_object_with_enum():
    input = '''{
  "$id": "https://example.com/address.schema.json",
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "description": "An address similar to http://microformats.org/wiki/h-card",
  "definitions": {
    "breakout_mark": {
      "type": "object",
      "properties": {
        "type": {
          "enum": [
            "breakout"
          ]
        },
        "attrs": {
          "type": "object",
          "properties": {
            "mode": {
              "enum": [
                "wide",
                "full-width"
              ]
            }
          },
          "required": [
            "mode"
          ],
          "additionalProperties": false
        }
      },
      "required": [
        "type",
        "attrs"
      ],
      "additionalProperties": false
    }
  }
}
'''
    dic = json.loads(input)
    res = sc.parse_json_schema(dic)
    assert res.defn == {"#/definitions/breakout_mark":sc.JNamedObject('breakout',
                                       {'attrs': (sc.JObject({'mode': (sc.Enum(['wide', 'full-width']), True)}, False), True)},
                                       False)}

def test_object_with_enum():
    input = '''{
  "$id": "https://example.com/address.schema.json",
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "description": "An address similar to http://microformats.org/wiki/h-card",
  "definitions":{
      "textColor_mark": {
      "type": "object",
      "properties": {
        "type": {
          "enum": [
            "textColor"
          ]
        },
        "attrs": {
          "type": "object",
          "properties": {
            "color": {
              "type": "string",
              "pattern": "^#[0-9a-fA-F]{6}$"
            }
          },
          "required": [
            "color"
          ],
          "additionalProperties": false
        }
      },
      "required": [
        "type",
        "attrs"
      ],
      "additionalProperties": false
    }
  }
}
'''
    dic = json.loads(input)
    res = sc.parse_json_schema(dic)
    assert res.defn == {'#/definitions/textColor_mark': sc.JNamedObject('textColor',
                                                                        {'attrs': (sc.JObject({'color': (sc.JString({'pattern': '^#[0-9a-fA-F]{6}$'}), True)}, False), True)}, False)}




def test_top_level_object_with_array():
    input = '''{
  "$id": "https://example.com/address.schema.json",
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "description": "An address similar to http://microformats.org/wiki/h-card",
  "type": "object",
      "properties": {
        "type": {
          "enum": [
            "codeBlock"
          ]
        },
        "content": {
          "type": "array",
          "items": {
            "allOf": [
              {
                "$ref": "#/definitions/text_node"
              }
            ]
          }
        }
      }
}
'''
    dic = json.loads(input)
    res = sc.parse_json_schema(dic)
    assert res.defn == sc.JNamedObject('codeBlock',
                                       {'content': (sc.JArray({'items':sc.AllOf([sc.Ref("#/definitions/text_node")])}), False)},False)


def test_top_level_object_with_array2():
    input = '''{
  "$id": "https://example.com/address.schema.json",
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "description": "An address similar to http://microformats.org/wiki/h-card",
  "type": "object",
      "properties": {
        "type": {
          "enum": [
            "codeBlock"
          ]
        },
        "content": {
          "type": "array",
          "items": {
            "allOf": [
              {
                "$ref": "#/definitions/text_node"
              },
              {
                "type": "object",
                "properties": {
                  "marks": {
                    "type": "array",
                    "maxItems": 0
                  }
                },
                "additionalProperties": true
              }
            ]
          }
        }
      }
}
'''
    dic = json.loads(input)
    res = sc.parse_json_schema(dic)
    assert res.defn == sc.JNamedObject('codeBlock',
       {'content': (sc.JArray({'items':sc.AllOf([sc.Ref("#/definitions/text_node"),
       sc.JObject({'marks':(sc.JArray({'maxItems':0}),False)}, True)
                                                  ])}),False)}, False)






def test_top_level_array():
    input = '''{
  "$id": "https://example.com/address.schema.json",
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "description": "An address similar to http://microformats.org/wiki/h-card",
  "type": "array"

}
'''
    dic = json.loads(input)
    res = sc.parse_json_schema(dic)
    assert res.defn == sc.JArray({})

def test_top_level_array_with_params():
    input = '''{
  "$id": "https://example.com/address.schema.json",
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "description": "An address similar to http://microformats.org/wiki/h-card",
  "type": "array",
  "maxItems": 0
}
'''
    dic = json.loads(input)
    res = sc.parse_json_schema(dic)
    assert res.defn == sc.JArray({"maxItems":0})


def test_top_level_ref():
    input = '''{
  "$id": "https://example.com/address.schema.json",
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "description": "An address similar to http://microformats.org/wiki/h-card",
  "$ref" : "#/definitions/top_node",
  "definitions":{
     "top_node":{
       "type":"string"
     }
  }
}
'''
    dic = json.loads(input)
    res = sc.parse_json_schema(dic)
    assert res.ref == "#/definitions/top_node"


def test_simple_definitions():
    input = '''{
  "$id": "https://example.com/address.schema.json",
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "description": "An address similar to http://microformats.org/wiki/h-card",
  "$ref" : "#/definitions/top_node",
  "definitions":{
     "top_node":{
       "type":"object"
     }
  }
}
'''
    dic = json.loads(input)
    res = sc.parse_json_schema(dic)
    assert res.defn == {"#/definitions/top_node":(sc.JObject({}, False))}

def test_allOf():
    input = '''{
  "$id": "https://example.com/address.schema.json",
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "description": "An address similar to http://microformats.org/wiki/h-card",
  "$ref" : "#/definitions/top_node",
  "definitions":{
     "top_node":{
       "allOf":[
         {"$ref":"#/definitions/sample"}
       ]
     }
  }
}
'''
    dic = json.loads(input)
    res = sc.parse_json_schema(dic)
    assert res.defn == {"#/definitions/top_node": (sc.AllOf([sc.Ref("#/definitions/sample")]))}

def test_anyOf():
    input = '''{
  "$id": "https://example.com/address.schema.json",
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "description": "An address similar to http://microformats.org/wiki/h-card",
  "$ref" : "#/definitions/top_node",
  "definitions":{
     "top_node":{
       "anyOf":[]
     }
  }
}
'''
    dic = json.loads(input)
    res = sc.parse_json_schema(dic)
    assert res.defn == {"#/definitions/top_node": (sc.AnyOf([]))}

def test_anyOf_two_objects():
    input = '''{
  "$id": "https://example.com/address.schema.json",
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "description": "An address similar to http://microformats.org/wiki/h-card",
  "$ref" : "#/definitions/top_node",
  "definitions":{
    "inlineCard_node": {
      "type": "object",
      "properties": {
        "type": {
          "enum": [
            "inlineCard"
          ]
        },
        "attrs": {
          "anyOf": [
            {
              "type": "object",
              "properties": {
                "url": {
                  "type": "string"
                }
              },
              "required": [
                "url"
              ],
              "additionalProperties": false
            },
            {
              "type": "object",
              "properties": {
                "data": {}
              },
              "required": [
                "data"
              ],
              "additionalProperties": false
            }
          ]
        }
      },
      "required": [
        "type",
        "attrs"
      ],
      "additionalProperties": false
    }
  }
}
'''
    dic = json.loads(input)
    res = sc.parse_json_schema(dic)
    assert res.defn == {'#/definitions/inlineCard_node':
                            JNamedObject('inlineCard',
                            {'attrs': (AnyOf([JObject({'url': (JString(constraints={}), True)}, additionalProperties=False),
                            JObject({'data': (None, True)}, False)]), True)}, False)}

def test_oneOf():
    input = '''{
  "$id": "https://example.com/address.schema.json",
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "description": "An address similar to http://microformats.org/wiki/h-card",
  "$ref" : "#/definitions/top_node",
  "definitions":{
     "top_node":{
       "oneOf":[]
     }
  }
}
'''
    dic = json.loads(input)
    res = sc.parse_json_schema(dic)
    assert res.defn == {"#/definitions/top_node": (sc.OneOf([]))}


def test_ref():
    input = '''{
  "$id": "https://example.com/address.schema.json",
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "description": "An address similar to http://microformats.org/wiki/h-card",
  "$ref" : "#/definitions/top_node",
  "definitions":{
     "top_node":{
       "$ref": "#/definitions/nothing"
     }
  }
}
'''
    dic = json.loads(input)
    res = sc.parse_json_schema(dic)
    assert res.defn == {"#/definitions/top_node": sc.Ref("#/definitions/nothing")}

