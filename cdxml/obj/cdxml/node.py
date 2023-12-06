import base64
import io
from typing import Any
import xml.dom.minidom

from ..boundingbox import BoundingBox


class CdxmlNode(object):
    @classmethod
    def fromXML(cls, _xml):
        if isinstance(_xml, str):
            _xml = _xml.replace("\n", "").replace("\r", "")
            doc = xml.dom.minidom.parseString(_xml)
            for i in doc.childNodes:
                if isinstance(i, xml.dom.minidom.Element):
                    _xml = i
                    break
        return cls(_xml, isPart=(_xml.tagName != "CDXML"))

    def __init__(self, xmlElement, parent=None, isPart=None):
        assert isinstance(xmlElement, xml.dom.minidom.Element)
        self.xmlElement = xmlElement
        self.xmlElement.node = self
        self.parent = parent
        self.root = self if parent is None else parent.root
        self.usedTags = set([])
        self.ignoreTags = {"annotation", "objecttag"}
        self.unitWeight = 1
        if isPart is None:
            self.isPart = parent.isPart
        else:
            self.isPart = isPart
            
        if self.aid and not self.isPart:
            self.root.idMap[self.aid] = self
        
        self.loadBoundingBox()
        self.init()
        self.checkUnknownTags()
    
    @property
    def aid(self):
        return self.attr("id")
    
    @property
    def prettyXml(self):
        return "\n" + self.xmlElement.toprettyxml()
    
    @property
    def xmlStr(self):
        from io import StringIO
        stream = StringIO()
        self.xmlElement.writexml(stream)
        xmlStr = stream.getvalue()
        stream.close()
        return xmlStr

    @property
    def idMap(self):
        assert self.xmlElement.tagName == "CDXML"
        if not hasattr(self, "_idMap"):
            self._idMap = {}
        return self._idMap
        
    @property
    def idToUnitId(self):
        assert self.xmlElement.tagName == "CDXML"
        if not hasattr(self, "_idToUnitId"):
            self._idToUnitId = {}
        return self._idToUnitId
    def loadBoundingBox(self):
        if self.attr("BoundingBox"):
            self.coord = tuple(map(float, self.attr("BoundingBox").strip().split(" ")))
            self.box = BoundingBox(self.coord)
        else:
            self.coord = None
            self.box = None

    def attr(self, attrName: str):
        return self.xmlElement.getAttribute(attrName)
    
    def setattr(self, attrName: str, value: Any):
        self.xmlElement.setAttribute(attname=attrName, value=value)
    
    def childrenByTag(self, tag, cdxmlClass=None):
        self.usedTags.add(tag)
        return [cdxmlClass(child, self) if (cdxmlClass is not None) else child 
                    for child in self.xmlElement.childNodes
                        if hasattr(child, "tagName") and child.tagName == tag]
    
    def childByTag(self, tag, cdxmlClass=None, assertOnlyOne=False):
        children = self.childrenByTag(tag, cdxmlClass)
        if (len(children) != 1 and assertOnlyOne) or (len(children) > 1):
            raise Exception(f"<{tag}> expect only one but: {len(children)}")
        elif children:
            return children[0]
        else:
            return None
    
    def ignoreTag(self, *tags):
        for t in tags:
            self.ignoreTags.add(t)
    
    def checkUnknownTags(self):
        for child in self.xmlElement.childNodes:
            if hasattr(child, "tagName") and \
               (child.tagName not in self.usedTags) and \
               (child.tagName not in self.ignoreTags):
                raise Exception(f"Unknown tag <{child.tagName}> in <{self.xmlElement.tagName}>")
    
    
    
    def mergeUnits(self, units):
        bs = [u.semanticUnit for u in units]
        if any(bs) == False:
            return
        
        if all(bs) == False:
            raise Exception(f"merge units ({bs})")
            
        units.sort(key=lambda x: -x.unitWeight) 
        for u in units[1:]:
            u.semanticUnit = False
            u.semanticParent = units[0].aid
    
    def elePositionOffset(self, ele, offset):
        if ele.getAttribute("p"):
            x, y = tuple(map(float, ele.getAttribute("p").split(" ")))
            ele.setAttribute("p", f"{x+offset[0]} {y+offset[1]}")

        if ele.getAttribute("BoundingBox"):
            l, t, r, b = tuple(map(float, ele.getAttribute("BoundingBox").split(" ")))
            ele.setAttribute("BoundingBox", f"{l+offset[0]} {t+offset[1]} {r+offset[0]} {b+offset[1]}")
    
    def positionOffset(self, offset):
        self.elePositionOffset(self.xmlElement, offset)
        self.loadBoundingBox()
        
        for child in self.xmlElement.childNodes:
            if hasattr(child, "node"):
                child.node.positionOffset(offset)
            else: 
                self.elePositionOffset(child, offset)
    
    def positionReset(self, offset=(0,0)):
        self.positionOffset((offset[0]-self.box.left, offset[1]-self.box.top))


class CdxmlUnit(object):
    def drawGuideline(self, draw, color="red", ext=0, label=None):
        offset, scale = self.root.pngOffsetScale(draw.im.size)
        bb = self.box.offsetAndScale(offset, scale)
        
        draw.rectangle(((bb.left-ext, bb.top-ext), (bb.right+ext, bb.bottom+ext)),
                       fill=None, outline=color, width=1)
        draw.text((bb.left-ext, bb.bottom+ext), 
                  (f"{self.xmlElement.tagName}\n%0.0f %0.0f %0.0f %0.0f" % tuple(self.coord)) 
                      if label is None else label, 
                  font=self.root.font, 
                  fill=color)
    
    def getSubPNG(self, img):
        offset, scale = self.root.pngOffsetScale(img.size)
        bb = self.box.offsetAndScale(offset, scale)
        
        # print(img.size, (bb.left, bb.top, bb.right, bb.bottom))
        if bb.width < 2:
            subImg = img.crop((bb.left, bb.top, bb.left+2, bb.bottom))
        elif bb.height < 2:
            subImg = img.crop((bb.left, bb.top, bb.right, bb.height+2))
        else:
            subImg = img.crop((bb.left, bb.top, bb.right, bb.bottom))
            
        outFp = io.BytesIO()
        subImg.save(outFp, "PNG")
        outFp.seek(0)
        png = base64.b64encode(outFp.read()).decode("utf8")
        outFp.close()
        return png
