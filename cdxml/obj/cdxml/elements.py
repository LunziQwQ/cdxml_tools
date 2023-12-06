from typing import Tuple
from .node import CdxmlNode, CdxmlUnit


class CdxmlFontTable(CdxmlNode):
    def init(self):
        self.fonts = self.childrenByTag("font")

class CdxmlColorTable(CdxmlNode):
    def init(self):
        self.colors = self.childrenByTag("color")
        
class CdxmlDoc(CdxmlNode):
    def init(self):
        self.colorTable = self.childByTag("colortable", CdxmlColorTable)
        self.fontTable = self.childByTag("fonttable", CdxmlFontTable)
        self.pages = self.childrenByTag("page", CdxmlPage)
        self.font = None
        self.pngOffsetScaleCache = None
    
    def pngOffsetScale(self, imgSize: Tuple[float, float]):
        xScale = imgSize[0] / self.box.width
        yScale = imgSize[1] / self.box.height
        offset = -self.box.left, -self.box.top
        
        return offset, (xScale, yScale)
    

class CdxmlBracketedGroup(CdxmlNode):
    def init(self):
        self.attachments = self.childrenByTag("bracketattachment")
        assert len(self.attachments) == 2, f"Only know 2 bracketattachment, but: {self.prettyXml}"


class CdxmlGraphic(CdxmlUnit, CdxmlNode):
    def init(self):
        self.unitWeight = 100
        self.type = self.attr("GraphicType")
        self.represents = self.childrenByTag("represent")
        self.symbolType = self.attr("SymbolType")
        

class CdxmlFragment(CdxmlUnit, CdxmlNode):
    def init(self):
        self.unitWeight = 10000 + (self.box.area if self.box else 0)
        self.nodes = self.childrenByTag("n", CdxmlNode)
        self.bonds = self.childrenByTag("b", CdxmlBond)
        self.graphics = self.childrenByTag("graphic", CdxmlGraphic)
    
    def applyOffsetScale(self, offset, scale):
        for n in self.nodes:
            n.applyOffsetScale(offset, scale)
    
    def onlyText(self):
        "若分子为仅包含文字的分子，返回文字内容，否则返回False"
        if len(self.bonds) == 0 and len(self.graphics) == 0 and len(self.nodes) == 1:
            if len(self.nodes[0].texts) == 1:
                return self.nodes[0].texts[0].text
        return False

class CdxmlChemicalProp(CdxmlNode):
    def init(self):
        pass


class CdxmlNode(CdxmlNode):
    def init(self):
        self.fragments = self.childrenByTag("fragment", CdxmlFragment)
        self.texts = self.childrenByTag("t", CdxmlText)
    
    def applyOffsetScale(self, offset, scale):
        (ox, oy), (sx, sy) = offset, scale
        left, bottom = self.attr("p").split(" ")
        nl, nb = float(left) * sx + ox , float(bottom) * sy + oy
        self.setattr("p", "%f %f" % (nl, nb))
        
        for t in self.texts:
            t.applyOffsetScale(offset, scale)


class CdxmlBond(CdxmlNode):
    def init(self):
        pass
        

class CdxmlText(CdxmlUnit, CdxmlNode):
    def init(self):
        self.unitWeight = 10
        self.styles = self.childrenByTag("s")
    
    def applyOffsetScale(self, offset, scale):
        (ox, oy), (sx, sy) = offset, scale
        left, bottom = self.attr("p").split(" ")
        nl, nb = float(left) * sx + ox , float(bottom) * sy + oy
        self.setattr("p", "%f %f" % (nl, nb))
    
    @property
    def text(self):
        return "".join([s.firstChild.data.strip() for s in self.styles])


class CdxmlArrow(CdxmlNode):
    def init(self):
        self.headCoord = self.xmlElement.getAttribute("Head3D").split(" ")[:2]
        self.tailCoord = self.xmlElement.getAttribute("Tail3D").split(" ")[:2]
        
    @property
    def headExtBox(self):
        """判断左右关系, 扩充指向区域Box"""
        if self.headCoord[0] > self.tailCoord[0]:     # 箭头向右，取右侧区域
            return self.box.extend(right=200, top=60, bottom=60, left=-self.box.width)
        else:                                           # 箭头向左，取左侧区域
            return self.box.extend(left=200, top=60, bottom=60, right=-self.box.width)

    @property
    def tailExtBox(self):
        """判断左右关系, 扩充起始区域Box"""
        if self.headCoord[0] > self.tailCoord[0]:     # 箭头向右，取左侧区域
            return self.box.extend(left=200, top=60, bottom=60, right=-self.box.width)
        else:                                           # 箭头向左，取右侧区域
            return self.box.extend(right=200, top=60, bottom=60, left=-self.box.width)

    @property
    def topExtBox(self):
        return self.box.extend(top=80, bottom=-self.box.height)
   
    @property
    def bottomExtBox(self):
        return self.box.extend(bottom=80, top=-self.box.height)


class CdxmlGroup(CdxmlNode):
    def init(self):
        self.fragments = self.childrenByTag("fragment", CdxmlFragment)
    
    def checkUnknownTags(self):
        pass

class CdxmlPage(CdxmlNode):
    def init(self):
        self.ignoreTag("border", "scheme")
        
        # 剥离 page下的 group 层；
        groupNodes = self.childrenByTag("group", CdxmlGroup)
        for group in groupNodes:
            for child in group.xmlElement.childNodes:
                self.xmlElement.appendChild(child)
            self.xmlElement.removeChild(group.xmlElement)
        
        self.fragments = self.childrenByTag("fragment", CdxmlFragment)
        self.texts = self.childrenByTag("t", CdxmlText)
        self.graphics = self.childrenByTag("graphic", CdxmlGraphic)
        self.bracketedGroups = self.childrenByTag("bracketedgroup", CdxmlBracketedGroup)
        self.arrows = self.childrenByTag("arrow", CdxmlArrow)
        self.chemicalProps = self.childrenByTag("chemicalproperty", CdxmlChemicalProp)
    
    
    def appendFragment(self, fragment: CdxmlFragment):
        self.xmlElement.appendChild(fragment.xmlElement)