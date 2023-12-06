import json
import base64
import unittest
from .parser import CdxmlParser
from PIL.PngImagePlugin import PngImageFile

class CdxmlParserTestCase(unittest.TestCase):

    def test_single_reaction(self):
        with open('tests/single.b64data', "r") as f:
            input_data = json.loads(base64.b64decode(f.read()).decode("utf-8"))
        parser = CdxmlParser(input_data["cdxml"], svg=input_data["svg"])

        parser.parse()
        output_data = parser.dumpAll(withCdxml=False, withImg=False)
        self.assertTrue(set(output_data.keys()) >= {'label', 'compound', 'reaction', 'condition'})
