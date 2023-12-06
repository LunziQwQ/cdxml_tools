from typing import Dict, Tuple
from PIL.Image import Image


def parseCdxml(
    cdxml: str, 
    svg: str | bytearray | None = None, 
    png: bytearray | None = None, 
    withPosition: bool = False, 
    withCdxml: bool = False, 
    withImg: bool = False
) -> Tuple[Dict, Image | None]:
    from .parser import CdxmlParser
    parser = CdxmlParser(cdxml, svg=svg, png=png)
    parser.parse()
    return parser.dumpAll(withPosition=withPosition, withCdxml=withCdxml, withImg=withImg), parser.getDebugPng()

def buildCdxml(data: Dict) -> str:
    from .builder import CdxmlBuilder
    builder = CdxmlBuilder(data)
    return builder.getCdxml()