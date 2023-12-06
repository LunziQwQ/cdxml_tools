import xml.dom.minidom

from ..boundingbox import BoundingBox

class SvgNode(object):
    def __init__(self, xmlElement):
        assert isinstance(xmlElement, xml.dom.minidom.Element)
        self.xmlElement = xmlElement
        self.xmlElement.node = self

        self.usedTags = set([])
        self.ignoreTags = {}

        self.loadBBox()
        self.loadTransform()
        self.init()
        self.checkUnknownTags()
    
    @classmethod
    def fromXML(cls, _xml):
        if isinstance(_xml, str):
            _xml = _xml.replace("\n", "").replace("\r", "")
            doc = xml.dom.minidom.parseString(_xml)
            for i in doc.childNodes:
                if isinstance(i, xml.dom.minidom.Element):
                    _xml = i
                    break
        return cls(_xml)
    
    def loadTransform(self):
        if self.attr("transform"):
            self.transformer = SvgTransformer(self.attr("transform").strip())
        else:
            self.transformer = None

    def loadBBox(self):
        if self.attr("BoundingBox"):
            self.coord = tuple(map(float, self.attr("BoundingBox").strip().split(" ")))
            self.box = BoundingBox(self.coord)
        else:
            self.coord = None
            self.box = None
    
    def attr(self, attrName: str):
        return self.xmlElement.getAttribute(attrName)

    def setattr(self, attrName: str, value):
        return self.xmlElement.setAttribute(attname=attrName, value=value)
    
    def childrenByTag(self, tag, svgClass=None):
        self.usedTags.add(tag)
        return [svgClass(child) if (svgClass is not None) else child 
                    for child in self.xmlElement.childNodes
                        if hasattr(child, "tagName") and child.tagName == tag]
    
    def childByTag(self, tag, svgClass=None, assertOnlyOne=False):
        children = self.childrenByTag(tag, svgClass)
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

class SvgTransformer:
    def __init__(self, transformStr: str):
        m, args = transformStr.replace(")", "").split("(")
        self.method = m
        self.args = args
    
    def transform(self, x, y):
        if self.method == "matrix":
            a,b,c,d,e,f = [float(a) for a in self.args.split(" ")]
            return a*x + c*y + e, b*x + d*y + f
    
    def reverseTransform(self, x, y):
        x1, y1 = None, None
        if self.method == "matrix":
            a,b,c,d,e,f = [float(a) for a in self.args.split(" ")]
            if 0 not in [a, b, c, d, e, f]:
                x1 = (y - f - d/c * (x-e)) / (b - (d * a) / c)
                y1 = (x - e - a * x1) / c
            else:
                if b == 0 and c == 0:
                    x1 = (x - e) / a
                    y1 = (y - f) / d
            return x1, y1
