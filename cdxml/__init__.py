from typing import Dict, Tuple, Union
from PIL.Image import Image


def parseCdxml(
    cdxml: str, 
    svg: Union[str, bytearray, None] = None, 
    png: Union[bytearray, None] = None, 
    withPosition: bool = False, 
    withCdxml: bool = False, 
    withImg: bool = False
) -> Union[Tuple[Dict, Image], None]:
    from .parser import CdxmlParser
    parser = CdxmlParser(cdxml, svg=svg, png=png)
    parser.parse()
    return parser.dumpAll(withPosition=withPosition, withCdxml=withCdxml, withImg=withImg), parser.getDebugPng()

def buildCdxml(data: Dict) -> str:
    from .builder import CdxmlBuilder
    builder = CdxmlBuilder(data)
    return builder.getCdxml()