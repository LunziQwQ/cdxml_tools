import io
import copy
from typing import List
from wand.image import Image as WandImage
from PIL import ImageDraw, Image

from .obj.cdxml.elements import CdxmlDoc
from .obj.svg.elements import SvgDoc
from .obj.target.elements import TArrow, TCompound, TCondition, TReaction, TText, TPlusSymbol
from .utils.exceptions import CdxmlHaveNoPageError


class CdxmlParser:
    semanticsToIdMap = {
        "reactant": "R",
        "reagent": "r",
        "product": "P",
        "catalyst": "ca",
        "solvent": "S",
        "condition": "C"
    }

    def __init__(self, cdxml: str, svg=None, png=None):
        self._svg = svg
        self._png = png
        self.cdxml = cdxml
        self.doc = None
        self.svgDoc = None
        self.tagMap = {}
        self._compounds = {}
        self._plusSymbols = {}
        self._arrows = {}
        self._reactions = {}
        self._conditions = {}
        self._texts = {}

        self.img = None
        if self._svg:
            try:
                svgBytes = self._svg.encode("utf-8") if isinstance(self._svg, str) else self._svg
                with WandImage(blob=svgBytes, format="svg") as image:
                    self.img = Image.open(io.BytesIO(image.make_blob("png")))
            except OSError:
                print("[WARNING] convert svg to png error. Can't show debug PNG")
        if self._png:
            pngBytes = self._png.encode("utf-8") if isinstance(self._png, str) else self._png
            self.img = Image.open(io.BytesIO(pngBytes))

    def getTag(self, semantics: str, number=None):
        if semantics in self.tagMap:
            self.tagMap[semantics] += 1
        else:
            self.tagMap[semantics] = 1

        if number is None:
            number = self.tagMap[semantics]
        if semantics in self.semanticsToIdMap:
            return "%s%d" % (self.semanticsToIdMap[semantics], number)
        else:
            return "%s_%d" % (semantics, number)

    def parse(self):
        # Parse Doc Obj
        self.doc = CdxmlDoc.fromXML(self.cdxml)
        if len(self.doc.pages) < 1:
            raise CdxmlHaveNoPageError()

        if self._svg:
            self.svgDoc = SvgDoc.fromXML(self._svg)

        # Parse Elements
        self._parseTexts()
        self._parsePlusSymbols()
        self._parseArrows()
        self._parseCompounds()

        # Parse logic elements
        self._parseReactions()

        # Reorder the role number
        self._formatTagNumber()

        # Parse other label
        self._parseTextsWithCompounds()

    def _parseCompounds(self):
        page = self.doc.pages[0]
        tags, xmls = [], []
        for fragment in page.fragments:
            c = TCompound(
                docObj=fragment,
                tag=self.getTag("compound"),
                semantics="compound"
            )
            self._compounds[c.tag] = c

            if not fragment.onlyText():
                if self.img:
                    c.img = c.cutImgRegion(self.img)

                if self.svgDoc:
                    c.svg = c.cutSvgRegion(self.svgDoc)
                tags.append(c.tag)
                xmls.append(fragment.xmlStr)

        # 批量查询，补充inchikey, MW分子量
        # infos = self.getInchikeysAndMwsByFragments(xmls)
        # for i, (inchikey, mw) in enumerate(infos):
        #     self._compounds[tags[i]].inchikey = inchikey
        #     self._compounds[tags[i]].mw = mw

    def _parsePlusSymbols(self):
        # Plus symbol text
        textNodes = []
        for t in self._texts.values():
            if t.text == "+":
                textNodes.append(t)
        for t in textNodes:
            self._texts.pop(t.tag)
            t.tag = self.getTag("plus")
            t.semantics = "plus"
            self._texts[t.tag] = t
            self._plusSymbols[t.tag] = TPlusSymbol(t.docObj, t.tag)

        # Plus symbol graphics
        page = self.doc.pages[0]
        for g in page.graphics:
            if g.type == "Symbol" and g.symbolType == "Plus":
                newTag = self.getTag("plus")
                self._plusSymbols[newTag] = TPlusSymbol(g, newTag)

    def _parseArrows(self):
        page = self.doc.pages[0]
        for arrow in page.arrows:
            tag = self.getTag("arrow")
            self._arrows[tag] = TArrow(
                docObj=arrow,
                tag=tag
            )

    def _parseTexts(self):
        page = self.doc.pages[0]
        for textDoc in page.texts:
            # 处理包含逗号的text标签
            if "," in textDoc.text:
                eachLetterWidth = textDoc.box.width / len(textDoc.text)
                nowCur = 0
                for subText in textDoc.text.split(","):
                    curOffset = len(subText) + 1     # 当前处理的字符+逗号，偏移字符数

                    # 处理前后空格问题
                    while subText.startswith(" "):
                        subText = subText[1:]
                        nowCur += 1
                        curOffset -= 1
                    while subText.endswith(" "):
                        subText = subText[:-1]

                    text = TText(
                        docObj=textDoc,
                        tag=self.getTag("text"),
                        text=subText
                    )
                    # 计算切分后的字符实际坐标（假想为等宽字体）
                    text.box.left += round(nowCur * eachLetterWidth, 2)
                    text.box.right = text.box.left + round(len(subText) * eachLetterWidth)
                    self._texts[text.tag] = text

                    nowCur += curOffset       # 已处理字符长度
            else:
                # 普通text
                tag = self.getTag("text")
                self._texts[tag] = TText(
                    docObj=textDoc,
                    tag=tag,
                    semantics="text"
                )

    def _parseReactions(self):
        for arrowTag, arrow in self._arrows.items():
            arrowDoc = arrow.docObj
            tag = arrowTag.replace("arrow", "reaction")
            reaction = TReaction(tag=tag)

            # 箭头附近的反应物
            for c_tag, compound in self._compounds.items():
                if compound.docObj.box.beHoldBy(arrowDoc.tailExtBox):
                    reaction.reactant.append(compound)
                if compound.docObj.box.beHoldBy(arrowDoc.headExtBox):
                    reaction.product.append(compound)
                if compound.docObj.box.beHoldBy(arrowDoc.topExtBox):
                    reaction.reagent.append(compound)
                if compound.docObj.box.beHoldBy(arrowDoc.bottomExtBox):
                    reaction.solvent.append(compound)

            # 箭头附近的文字
            for tTag, text in self._texts.items():
                if text.docObj.box.beHoldBy(arrowDoc.topExtBox):
                    reaction.reagent.append(text)
                if text.docObj.box.beHoldBy(arrowDoc.bottomExtBox):
                    if text.isTCondition():
                        reaction.condition.append(text)
                    else:
                        reaction.solvent.append(text)

            # 处理condition semantics变化
            reaction.condition = self._changeTextListSemanticsToConditionList(reaction.condition)
            for semantics, nodeList in reaction.semanticsMapIteritems():
                if semantics == "condition":
                    continue

                # 处理condition之外的其他id身份变化
                for i, node in enumerate(nodeList):
                    # 处理化合物
                    if node.tag.startswith("compound"):
                        self._changeCompoundSemantics(compound=node, semantics=semantics)

                        # 处理由加号连接的化合物扩散
                        for n in self._diffusionCompoundSemanticsByPlus(node):
                            # 更改语义可能导致重复添加，需要去重
                            if n not in nodeList:
                                nodeList.append(n)
                    # 处理文字表达的化合物
                    if node.tag.startswith("text"):
                        c = self._changeTextSemanticsToCompound(text=node, semantics=semantics)
                        nodeList[i] = c

            self._reactions[tag] = reaction

    def _parseTextsWithCompounds(self):
        """识别化合物上下的文本, 作为该化合物的child属性"""
        textFather = {}
        for tag, text in self._texts.items():
            if text.semantics != "text":
                continue
            textFather[tag] = []

            for compound in self._compounds.values():
                if text.box.beHoldBy(compound.box.extend(top=80, bottom=80)):
                    textFather[tag].append(compound)   # bottom 方向

        for textTag, fatherList in textFather.items():
            if len(fatherList) == 0:
                continue
            text = self._texts[textTag]

            if len(fatherList) > 1:        # 多个Father取边界距离最近
                disList = [c.box.distance(text.box, useMin4=True) for c in fatherList]
                dis = min(disList)
                compound = fatherList[disList.index(dis)]
            if len(fatherList) == 1:       # 仅有一个Father
                compound = fatherList[0]
                dis = compound.box.distance(text.box, useMin4=True)
            text.addFather(compound, dis)

    def _changeCompoundSemantics(self, compound: TCompound, semantics: str) -> TCompound:
        newTag = self.getTag(semantics)
        self._compounds.pop(compound.tag)
        compound.semantics = semantics
        compound.tag = newTag
        self._compounds[newTag] = compound
        return compound

    def _changeTextSemanticsToCompound(self, text: TText, semantics: str) -> str:
        newTag = self.getTag(semantics)
        self._texts.pop(text.tag)
        text.tag = newTag
        text.semantics = semantics
        self._texts[newTag] = text

        c = TCompound(
            docObj=text.docObj,
            tag=newTag,
            semantics=semantics,
            text=text.text,
            isCollection=True,
        )
        c.box = text.box
        self._compounds[newTag] = c
        return c

    def _changeTextListSemanticsToConditionList(self, texts: List[TText]) -> List[TCondition]:
        conditionList = []
        condition = {}
        for t in texts:
            self._texts.pop(t.tag)
            if t.hash not in condition:
                condition[t.hash] = []
            condition[t.hash].append(t)
        for _, tList in condition.items():
            newTag = self.getTag("condition")
            for i, t in enumerate(tList):
                t.semantics = "condition"
                t.tag = "%s_%d" % (newTag, i + 1)
                self._texts[t.tag] = t

            newCondition = TCondition(
                docObj=tList[0].docObj,
                tag=newTag,
                textList=[t.text for t in tList],
            )

            # 同一行文本框，取最左与总宽度
            l = min([t.box.left for t in tList])
            r = max([t.box.left + t.box.width for t in tList])
            newCondition.box.left = l
            newCondition.box.right = r
            self._conditions[newCondition.tag] = newCondition
            conditionList.append(newCondition)
        return conditionList

    def _diffusionCompoundSemanticsByPlus(self, compound, usedItems=None) -> List:
        usedItems = usedItems or [compound.hash]
        compounds = []
        for plus in self._findPlusNearCompound(compound):
            if plus.hash in usedItems:
                continue
            usedItems.append(plus.hash)
            for c in self._findCompoundNearPlus(plus):
                if c.hash in usedItems:
                    continue
                usedItems.append(c.hash)
                if c.semantics != compound.semantics:
                    self._changeCompoundSemantics(c, compound.semantics)
                    compounds.append(c)
                    compounds.extend(self._diffusionCompoundSemanticsByPlus(c, usedItems))
        return compounds

    def _findPlusNearCompound(self, compound) -> List:
        plusList = []
        for plus in self._plusSymbols.values():
            extBox = compound.docObj.box.extend(left=80, right=80)
            if plus.docObj.box.beHoldBy(extBox):
                plusList.append(plus)
        return plusList

    def _findCompoundNearPlus(self, plus) -> List:
        compoundList = []
        for compound in self._compounds.values():
            extBox = plus.docObj.box.extend(left=100, right=100, top=50, bottom=50)
            if compound.docObj.box.beHoldBy(extBox):
                compoundList.append(compound)
        return compoundList

    def _formatTagNumber(self):
        """
        参考ELN的排序方式, 以空间位置中心为基准
        "reactant", "product": 从左至右递增
        "reagent", "solvent":  从上至下递增
        若基准第一排序维度完全相同, 以第二排序细节为准
        """
        def centerCmpLt(node1, node2):
            if node1.semantics != node2.semantics:
                return 0
            (x1, y1), (x2, y2) = node1.box.center, node2.box.center
            if node1.semantics in ["reactant", "product"]:                            # L2R
                return x1 < x2 if x1 != x2 else (y1 < y2 if y1 != y2 else 0)
            if node1.semantics in ["reagent", "catalyst", "solvent", "condition"]:    # T2B
                return y1 < y2 if y1 != y2 else (x1 < x2 if x1 != x2 else 0)

        # 为涉及重排tagNumber的对象增加lt方法
        TCompound.__lt__ = centerCmpLt
        TCondition.__lt__ = centerCmpLt

        for nodeType in ["_compounds", "_conditions"]:
            for s in self.semanticsToIdMap.keys():
                nodeList = [node for node in getattr(self, nodeType).values() if node.semantics == s]
                if len(nodeList) <= 1:
                    continue

                nodeList.sort()
                for i, node in enumerate(nodeList):
                    getattr(self, nodeType).pop(node.tag)
                    node.tag = self.getTag(node.semantics, i + 1)
                for node in nodeList:
                    getattr(self, nodeType)[node.tag] = node
        TCompound.__lt__ = None
        TCondition.__lt__ = None

    def dumpAll(self, withPosition=False, withCdxml=True, withImg=True):
        data = {
            "graphic": self.getGraphicParams(),
            "label":
                [a.toDict(withPosition=withPosition) for a in self._arrows.values()]
                + [t.toDict(withPosition=withPosition) for t in self._texts.values()],
            "compound": [
                c.toDict(withPosition=withPosition, withCdxml=withCdxml, withImg=withImg)
                for c in self._compounds.values()
            ],
            "reaction": [r.toDict() for r in self._reactions.values()],
            "condition": [e.toDict() for e in self._conditions.values()]
        }
        return data

    def getGraphicParams(self):
        return {
            "size": {"w": self.doc.box.width, "h": self.doc.box.height}
        }

    def getDebugPng(self):
        if not self.img:
            return None

        img = copy.deepcopy(self.img)
        draw = ImageDraw.Draw(img)

        # 标记所有化合物
        for c in self._compounds.values():
            c.drawGuideline(draw)

        # 标记所有环境条件
        for e in self._conditions.values():
            e.drawGuideline(draw)

        for t in self._texts.values():
            if t.father:
                t.drawGuideline(draw, color="grey", ext=2, label="%s.text" % t.father)
        return img

    def getDebugPngBytes(self):
        png = self.getDebugPng()
        if png:
            stream = io.BytesIO()
            png.save(stream, format='PNG')
            return stream.getvalue()
        else:
            return b""
