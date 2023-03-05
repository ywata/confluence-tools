import unittest
import xml.etree.ElementTree as ET
from xml.etree import ElementTree as ET
from xml.etree import ElementPath as EP


def test_xpath_element():
    xml = """
    <!DOCTYPE html [<!ENTITY nbsp "&#160;">]>
    <root 
        xmlns:ac="https://example.com/ac"

        xmlns:ri="http://example.com/ri"
        >
    <h1>1st item <ac:emoticon ac:name="smile" ac:emoji-shortname=":slight_smile:" ac:emoji-id="1f642" ac:emoji-fallback="🙂" />   2023-02-25   </h1><ul><li><p>2nd part discusses about something</p></li><li><p>another item</p></li></ul><h1>2nd part <ac:emoticon ac:name="smile" ac:emoji-shortname=":slight_smile:" ac:emoji-id="1f642" ac:emoji-fallback="🙂" />   2023-02-25   </h1><ul><li><p>2nd part discusses about something</p></li><li><p>another item</p></li></ul><h1>rest of the page</h1><h2>what happens about <span style="color: rgb(255,86,48);">color</span>
  </h2><p>or Emoji 

  </p><table data-layout="default" ac:local-id="29f31793-1be9-4ba1-86f9-4c9cc95da7e3"><colgroup><col style="width: 226.67px;" /><col style="width: 226.67px;" /><col style="width: 226.67px;" /></colgroup><tbody><tr><th><p /></th><th><p /></th><th><p /></th></tr><tr><td><p>1,1 <ac:emoticon ac:name="smile" ac:emoji-shortname=":slight_smile:" ac:emoji-id="1f642" ac:emoji-fallback="🙂" /> </p></td><td><p><del>1,2</del></p></td><td><p><code>1,3</code></p></td></tr><tr><td><p>2,1 <ac:emoticon ac:name="blue-star" ac:emoji-shortname=":angry:" ac:emoji-id="1f620" ac:emoji-fallback="😠" /> </p></td><td><p><u>2,2</u></p></td><td><p><em><strong>2,3</strong></em></p></td></tr></tbody></table>

    </root>    
    """
    ET.register_namespace("ac", "http://example.com/ac")
    root = ET.fromstring(xml)

    assert root is not None


def test_xpath_element_tree():
    xml = """
    <!DOCTYPE html [<!ENTITY nbsp "&#160;">]>
    <root 
        xmlns:ac="https://example.com/ac"

        xmlns:ri="http://example.com/ri"
        >
    <h1>1st item <ac:emoticon ac:name="smile" ac:emoji-shortname=":slight_smile:" ac:emoji-id="1f642" ac:emoji-fallback="🙂" />   2023-02-25   </h1><ul><li><p>2nd part discusses about something</p></li><li><p>another item</p></li></ul><h1>2nd part <ac:emoticon ac:name="smile" ac:emoji-shortname=":slight_smile:" ac:emoji-id="1f642" ac:emoji-fallback="🙂" />   2023-02-25   </h1><ul><li><p>2nd part discusses about something</p></li><li><p>another item</p></li></ul><h1>rest of the page</h1><h2>what happens about <span style="color: rgb(255,86,48);">color</span>
  </h2><p>or Emoji 

  </p><table data-layout="default" ac:local-id="29f31793-1be9-4ba1-86f9-4c9cc95da7e3"><colgroup><col style="width: 226.67px;" /><col style="width: 226.67px;" /><col style="width: 226.67px;" /></colgroup><tbody><tr><th><p /></th><th><p /></th><th><p /></th></tr><tr><td><p>1,1 <ac:emoticon ac:name="smile" ac:emoji-shortname=":slight_smile:" ac:emoji-id="1f642" ac:emoji-fallback="🙂" /> </p></td><td><p><del>1,2</del></p></td><td><p><code>1,3</code></p></td></tr><tr><td><p>2,1 <ac:emoticon ac:name="blue-star" ac:emoji-shortname=":angry:" ac:emoji-id="1f620" ac:emoji-fallback="😠" /> </p></td><td><p><u>2,2</u></p></td><td><p><em><strong>2,3</strong></em></p></td></tr></tbody></table>

    </root>    
    """
    ET.register_namespace("ac", "http://example.com/ac")
    root = ET.XML(xml)

    assert root is not None


def test_xpath_get_first_item():
    xml = """
    <!DOCTYPE html [<!ENTITY nbsp "&#160;">]>
    <root xmlns:ac="https://example.com/ac" xmlns:ri="http://example.com/ri">
    <h1>text1</h1>
    <h1>text2</h1>    
    </root>    
    """
    ET.register_namespace("ac", "http://example.com/ac")
    root = ET.fromstring(xml)
    h1 = EP.findall(root, "h1")
    assert len(h1) == 2
    h1_1 = EP.find(root, "h1[1]")
    h1_2 = EP.find(root, "h1[2]")
    assert h1_1.text == "text1"
    assert h1_2.text == "text2"

def test_element_tree_isnert_remove():
    xml = """
        <root></root>
        """
    root = ET.fromstring(xml)
    root.insert(0, ET.Element("tag"))
    tag = EP.find(root, "tag")
    assert tag.tag == "tag"
    root.remove(tag)
    tag2 = EP.find(root, "tag")
    assert tag2 is None

def test_element_tree_parent():
    xml = """
    <root>
    <element>element1</element>
    <element>element2</element>
    <element>element3</element>
    </root>
    """
    root = ET.fromstring(xml)
    elm2 = EP.find(root, "element[2]")
    elm2_parent = EP.find(root, "element[2]/..")


    assert elm2 is not None