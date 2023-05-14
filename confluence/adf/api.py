from typing import List, Optional, Union
import json
from dataclasses import dataclass, make_dataclass, field
import logging
@dataclass()
class Table():
    header: Optional[List[str]]
    rows: List[List[str]] # inner List conttains columns of the table

@dataclass()
class Text():
    text: str

InlineNode = Text
@dataclass()
class Heading():
    level: int
    content: List[InlineNode]

@dataclass()
class Paragraph():
    contents: List[InlineNode]

TopLevelNode = Union[Heading, Table, Paragraph]



def adf_table(table:Table):
    """
    generate ADF json data from table
    :param table:
    :return: json data
    """

def inline_node(content : InlineNode):
    """
    generate ADF json data from contents
    :param contents:
    :return:
    """
    match content:
        case Text(text):
            logging.info(f"{content}")
            return {
                "type": "text",
                "text": text
            }
        case _:
            assert False, f"Unknown content type: {type(content)}"
def to_cell(cell : InlineNode):
    return {
        "type": "tableCell",
        "attrs": {},
        "content": list(map(top_level, cell))
    }
def to_row(cells : List[InlineNode]):
    logging.info(cells)
    return {
        "type": "tableRow",
        "content": list(map(to_cell, cells))
    }

def top_level(content : TopLevelNode):
    """
    generate ADF json data from contents
    :param contents:
    :return:
    """
    match content:
        case Heading(level, content):
            return {
                "type": "heading",
                "attrs": {
                    "level": level
                },
                "content": list(map(inline_node, content))
            }
        case Table(header, rows):
            logging.info(f"{rows}")
            table_rows = list(map(to_row, rows))
            return{
                "type": "table",
                "attrs": {
                    "isNumberColumnEnabled": True,
                    "layout": "default"
                },
                "content": table_rows
            }
        case Paragraph(contents):
            logging.info(f"{contents}")
            return{
                "type": "paragraph",
                "content": list(map(inline_node, contents))
            }
        case _:
            assert False, f"Unknown content type: {type(content)}"
def doc_node(content: List[TopLevelNode]):
    #cnt = json.dumps(list(map(top_level, content)))
    cnt = list(map(top_level, content))
    return {
        "type": "doc",
        "version": 1,
        "content": cnt}


