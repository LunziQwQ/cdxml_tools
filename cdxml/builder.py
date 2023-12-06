from .obj.target.elements import TArrow, TCompound, TText

class CdxmlBuilder:
    def __init__(self, data):
        self._reset()
        self._arrows = {}
        self._compounds = {}
        self._texts = {}

        if data.get("graphic", {}).get("scale"):
            scale = data["graphic"]["scale"]
            self.scale = scale["h"], scale["v"] 
        else:
            self.scale = 1, 1

        for label in data.get("label", []):
            if label.get("semantics") == "arrow":
                self._arrows[label["tag"]] = TArrow.buildByDict(label)
                continue
            else:
                self._texts[label["tag"]] = TText.buildByDict(label)

        for c in data.get("compound", []):
            self._compounds[c["tag"]] = TCompound.buildByDict(c)

    def _reset(self):
        self._usedId = [1000000, 1000001]
        self._maxZ = 0

    def _newId(self):
        newId = max(self._usedId) + 1
        self._usedId.append(newId)
        return newId
    
    def _newZ(self):
        self._maxZ += 1
        return self._maxZ

    def buildText(self, text, left, bottom):
        # 应用整体缩放比
        sx, sy = self.scale
        return """
            <t id="{id}" p="{l} {b}" Z="{z}" LineHeight="auto">
                <s font="1000000" size="10" color="0">{text}</s>
            </t>
        """.format(
            id=self._newId(),
            l=left * sx,
            b=bottom * sy,
            z=self._newZ(),
            text=text
        )
    
    def buildArrow(self, targetArrow: TArrow):
        # 应用整体缩放比
        sx, sy = self.scale
        return """
            <graphic id="{graphicId}" SupersededBy="{arrowId}" BoundingBox="{headX} {headY} {tailX} {tailY}" Z="{z}" GraphicType="Line" ArrowType="FullHead" HeadSize="1000"/>
            <arrow id="{arrowId}" Z="{z}" FillType="None" ArrowheadHead="Full" ArrowheadType="Solid" HeadSize="1000" ArrowheadCenterSize="875" ArrowheadWidth="250" Head3D="{headX} {headY} 0" Tail3D="{tailX} {tailY} 0"/>
        """.format(
            arrowId=self._newId(), 
            graphicId=self._newId(), 
            headX=targetArrow.headPosition["l"] * sx, 
            headY=targetArrow.headPosition["t"] * sy,
            tailX=targetArrow.tailPosition["l"] * sx, 
            tailY=targetArrow.tailPosition["t"] * sy,
            z=self._newZ()
        )

    def buildCompound(self, targetCompound: TCompound):
        from .obj.cdxml.elements import CdxmlFragment
        if targetCompound.cdxml:
            f = CdxmlFragment.fromXML(targetCompound.cdxml)
            tBox, fBox = targetCompound.box, f.box
            
            # 防止图像变形，scale只算单边
            scale = (float(tBox.width) / float(fBox.width), float(tBox.width) / float(fBox.width))
            offset = tBox.left - fBox.left * scale[0], tBox.top - fBox.top * scale[1]
            # 由于初始坐标系为cdxml标准，先将cdxml转换成targetNode坐标系
            f.applyOffsetScale(offset, scale)
            # 和其他元素同坐标系标准后，再应用整体缩放比
            f.applyOffsetScale((0, 0), self.scale)
            return f.xmlStr
        
        # 缺省图：无CDXML，但有svg的情况
        if targetCompound.svg:
            # 以缺省图的宽度最左，高度居中为文字起点
            left = targetCompound.box.left
            bottom = targetCompound.box.center[1]
            return self.buildText(targetCompound.text, left, bottom)
        return ""

    def getCdxml(self):
        self._reset()
        cdxml = ""
        for a in self._arrows.values():
            cdxml += self.buildArrow(a)

        for t in self._texts.values():
            cdxml += self.buildText(t.text, t.bbox.ltrb[0], t.bbox.ltrb[3])

        for c in self._compounds.values():
            cdxml += self.buildCompound(c)

        return cdxmlTemplate.format(content=cdxml).replace("\n", "").replace("\r", "")

cdxmlTemplate = """
<?xml version="1.0" encoding="UTF-8" ?><!DOCTYPE CDXML SYSTEM "http://www.cambridgesoft.com/xml/cdxml.dtd">
<CDXML CreationProgram="ChemDraw 20.0.0.38" Name="new.cdxml" WindowPosition="0 0" WindowSize="0 0" FractionalWidths="yes" InterpretChemically="yes" ShowAtomQuery="yes" ShowAtomStereo="no" ShowAtomEnhancedStereo="yes" ShowAtomNumber="no" ShowResidueID="no" ShowBondQuery="yes" ShowBondRxn="yes" ShowBondStereo="no" ShowTerminalCarbonLabels="no" ShowNonTerminalCarbonLabels="no" HideImplicitHydrogens="no" Magnification="666" LabelFont="174" LabelSize="10" LabelFace="96" CaptionFont="174" CaptionSize="10" HashSpacing="2.49" MarginWidth="1.59" LineWidth="0.60" BoldWidth="2.01" BondLength="14.40" BondSpacing="18" ChainAngle="120" LabelJustification="Auto" CaptionJustification="Left" AminoAcidTermini="HOH" ShowSequenceTermini="yes" ShowSequenceBonds="yes" ShowSequenceUnlinkedBranches="no" ResidueWrapCount="40" ResidueBlockCount="10" ResidueZigZag="yes" NumberResidueBlocks="no" PrintMargins="36 36 36 36" MacPrintInfo="0003000000480048000000000300024CFFF4FFF4030C02580367052803FC0002000000480048000000000300024C000100000064000000010001010100000001270F000100010000000000000000000000000002001901900000000000400000000000000000000100000000000000000000000000000000" ChemPropName="" ChemPropFormula="Chemical Formula: " ChemPropExactMass="Exact Mass: " ChemPropMolWt="Molecular Weight: " ChemPropMOverZ="m/z: " ChemPropAnalysis="Elemental Analysis: " ChemPropBoilingPt="Boiling Point: " ChemPropMeltingPt="Melting Point: " ChemPropCritTemp="Critical Temp: " ChemPropCritPres="Critical Pres: " ChemPropCritVol="Critical Vol: " ChemPropGibbs="Gibbs Energy: " ChemPropLogP="Log P: " ChemPropMR="MR: " ChemPropHenry="Henry&apos;s Law: " ChemPropEForm="Heat of Form: " ChemProptPSA="tPSA: " ChemPropID="" ChemPropFragmentLabel="" color="0" bgcolor="1" RxnAutonumberStart="1" RxnAutonumberConditions="no" RxnAutonumberStyle="Roman" RxnAutonumberFormat="(#)">
    <colortable>
        <color r="1" g="1" b="1"/>
        <color r="0" g="0" b="0"/>
        <color r="1" g="0" b="0"/>
        <color r="1" g="1" b="0"/>
        <color r="0" g="1" b="0"/>
        <color r="0" g="1" b="1"/>
        <color r="0" g="0" b="1"/>
        <color r="1" g="0" b="1"/>
    </colortable>
    <fonttable>
        <font id="1000000" charset="x-mac-roman" name="Arial"/>
    </fonttable>
    <page id="1000001" HeaderPosition="36" FooterPosition="36" PrintTrimMarks="yes" HeightPages="2" WidthPages="1">
        {content}
    </page>
</CDXML>
"""