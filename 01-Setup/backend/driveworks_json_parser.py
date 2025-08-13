import xml.etree.ElementTree as ET
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def extract_common_attributes(control):
    props = {}
    position = {}
    width = control.attrib.get("Width")
    height = control.attrib.get("Height")
    x = control.attrib.get("X")
    y = control.attrib.get("Y")
    if width:
        props["width"] = width
    if height:
        props["height"] = height
    if x and y:
        try:
            position = {"x": int(x), "y": int(y)}
        except (ValueError, TypeError):
            position = {"x": 0, "y": 0}
    return props, {}, position

def parse_label(control):
    name = control.attrib.get("Name", "UnnamedLabel")
    text = control.attrib.get("Text", "")
    font_size = control.attrib.get("FontSize", "")
    font_color = control.attrib.get("FontColor", "")
    font_weight = control.attrib.get("FontWeight", "")
    props, _, position = extract_common_attributes(control)
    return {
        "name": name,
        "type": "component",
        "componentName": "Label",
        "reusable": True,
        "styles": "mb-2 font-bold text-gray-700",
        "props": {**props, "text": text, "fontSize": font_size, "color": font_color, "fontWeight": font_weight},
        "position": position,
        "alignment": infer_alignment(position.get("x", 0))
    }

def parse_combobox(control):
    name = control.attrib.get("Name", "UnnamedComboBox")
    options = [child.attrib.get("Text") for child in control.findall("Option")]
    props, _, position = extract_common_attributes(control)
    return {
        "name": name,
        "type": "component",
        "componentName": "Dropdown",
        "reusable": True,
        "styles": "w-full border border-gray-300 rounded mb-4",
        "props": {**props, "options": options or ["Option1", "Option2"]},
        "position": position,
        "alignment": infer_alignment(position.get("x", 0))
    }

def parse_textbox(control):
    name = control.attrib.get("Name", "UnnamedTextBox")
    placeholder = control.attrib.get("Placeholder", "")
    props, _, position = extract_common_attributes(control)
    return {
        "name": name,
        "type": "component",
        "componentName": "TextBox",
        "reusable": True,
        "styles": "w-full border border-gray-300 rounded mb-4",
        "props": {**props, "placeholder": placeholder},
        "position": position,
        "alignment": infer_alignment(position.get("x", 0))
    }

def parse_slider(control):
    name = control.attrib.get("Name", "UnnamedSlider")
    min_val = control.attrib.get("Min", "0")
    max_val = control.attrib.get("Max", "100")
    step = control.attrib.get("Step", "1")
    props, _, position = extract_common_attributes(control)
    return {
        "name": name,
        "type": "component",
        "componentName": "Slider",
        "reusable": True,
        "styles": "w-full",
        "props": {**props, "min": min_val, "max": max_val, "step": step},
        "position": position,
        "alignment": infer_alignment(position.get("x", 0))
    }

def parse_button(control):
    name = control.attrib.get("Name", "UnnamedButton")
    text = control.attrib.get("Text", "Submit")
    props, _, position = extract_common_attributes(control)
    return {
        "name": name,
        "type": "component",
        "componentName": "Button",
        "reusable": True,
        "styles": "bg-green-500 text-white px-4 py-2 rounded hover:bg-green-700",
        "props": {**props, "text": text},
        "position": position,
        "alignment": infer_alignment(position.get("x", 0))
    }

def infer_alignment(x):
    try:
        x_val = int(x)
        if x_val < 400:
            return "left"
        elif x_val < 800:
            return "center"
        else:
            return "right"
    except:
        return "left"

def parse_driveworks_form(xml_str):
    try:
        logger.info("Parsing DriveWorks form")
        root = ET.fromstring(f"<root>{xml_str}</root>")
        components = []
        for control in root:
            tag = control.tag.split("}")[-1]
            if tag == "Label":
                components.append(parse_label(control))
            elif tag == "ComboBox":
                components.append(parse_combobox(control))
            elif tag == "TextBox":
                components.append(parse_textbox(control))
            elif tag == "Slider":
                components.append(parse_slider(control))
            elif tag == "Button":
                components.append(parse_button(control))

        return json.dumps({"children": [{"children": components}]}, indent=2)
    except Exception as e:
        logger.error(f"Error parsing form: {str(e)}")
        return json.dumps({"children": []})
