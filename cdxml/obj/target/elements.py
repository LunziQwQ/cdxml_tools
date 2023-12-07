import re
import io
import copy
import base64

from typing import List
from ..boundingbox import BoundingBox
from .node import TargetNode
from ..cdxml.elements import CdxmlFragment


class TText(TargetNode):
    @classmethod
    def buildByDict(cls, data):
        text = cls(None, data["tag"], data["semantics"], text=data["text"])
        text.box = BoundingBox.loadByLtwhDict(data["position"])
        return text

    def __init__(self, docObj, tag: str, semantics: str = "text", text: str = "", isCollection: bool = False) -> None:
        super(TText, self).__init__(tag=tag, semantics=semantics, docObj=docObj)
        self.text = text if text else docObj.text
        self.isCollection = isCollection
    
    def isTCondition(self):
        return TCondition.isConditionText(self.text)

    def toDict(self, withPosition=False):
        data = {
            "tag": self.tag,
            "semantics": self.semantics,
            "text": self.text,
            "is_collection": self.isCollection,
            "father": self.father
        }
        if withPosition:
            data["position"] = self.box.ltwhDict
        return data

class TPlusSymbol(TargetNode):
    def __init__(self, docObj, tag: str, semantics: str = "plus") -> None:
        super(TPlusSymbol, self).__init__(tag=tag, semantics=semantics, docObj=docObj)
    
    def toDict(self, withPosition=False):
        data = {
            "tag": self.tag,
            "semantics": self.semantics,
        }
        if withPosition:
            data["position"] = self.box.ltwhDict
        return data

class TArrow(TargetNode):
    @classmethod
    def buildByDict(cls, data):
        arrow = cls(None, data["tag"], data["semantics"])
        arrow.box = BoundingBox.loadByLtwhDict(data["position"])
        arrow.tailPosition = data["tail_position"]
        arrow.headPosition = data["head_position"]
        return arrow

    def __init__(self, docObj, tag: str, semantics: str = "arrow") -> None:
        super(TArrow, self).__init__(tag=tag, semantics=semantics, docObj=docObj)
        if docObj:
            self.tailPosition = dict(zip(["l", "t"], docObj.tailCoord))
            self.headPosition = dict(zip(["l", "t"], docObj.headCoord))

    
    def toDict(self, withPosition=False):
        data = {
            "tag": self.tag,
            "semantics": self.semantics,
        }
        if withPosition:
            data["position"] = self.box.ltwhDict
            data["tail_position"] = self.tailPosition
            data["head_position"] = self.headPosition
        return data


class TCompound(TargetNode):
    @classmethod
    def buildByDict(cls, data):
        c = cls(None, data["tag"], data["semantics"])
        c.box = BoundingBox.loadByLtwhDict(data["position"])
        c.cdxml = data.get("cdxml")
        c.text = data.get("text")
        c.img = data.get("img")
        c.svg = data.get("svg")
        return c

    def __init__(self, docObj, tag: str, semantics: str, isCollection: bool = False, img: str = None, text: str = None) -> None:
        super(TCompound, self).__init__(docObj=docObj, tag=tag, semantics=semantics)
        self.isCollection = isCollection
        self.img = img
        self.svg = None
        self.text = text
        if docObj and docObj.xmlElement.tagName == "fragment":
            self.cdxml = docObj.xmlStr
        else:
            self.cdxml = ""

        # 分子图为纯文本的特殊情况
        if docObj and isinstance(docObj, CdxmlFragment) and docObj.onlyText():
            self.cdxml = ""
            self.text = docObj.onlyText()

    def toDict(self, withPosition=False, withCdxml=True, withImg=True):
        imgStr = None
        if withImg and self.img:
            stream = io.BytesIO()
            self.img.save(stream, format='PNG')
            imgBytes = base64.b64encode(stream.getvalue())
            imgStr = imgBytes.decode("utf-8")
        
        data = {
            "tag": self.tag,
            "semantics": self.semantics,
            "is_collection": self.isCollection,
            "img": imgStr,
            "svg": self.svg,
            "text": self.text,
            "cdxml": self.cdxml if withCdxml else "",
            "child": self.childDict
        }
        if withPosition:
            data["position"] = self.box.ltwhDict
        return data

    def drawGuideline(self, draw):
        colorMap = {
            "reagent": "blue",
            "reactant": "purple",
            "catalyst": "orange",
            "solvent": "pink",
            "product": "darkblue",
            "compound": "darkgray"
        }
        super(TCompound, self).drawGuideline(
            draw = draw, 
            color = colorMap[self.semantics], 
            ext = 5 if self.cdxml else 2, 
            label = "%s%s(%s)" % (self.tag, "*" if self.isCollection else "", self.semantics)
        )

    def cutImgRegion(self, image):
        l, t, r, b = self.offsetScaleBorderLtrb(imgSize=image.size, ext=8)
        return image.crop((l,t,r,b))

    def cutSvgRegion(self, svgDoc):    
        doc = svgDoc.copy()
        l, t, r, b = self.offsetScaleBorderLtrb(imgSize=(doc.width, doc.height), ext=10)
        scaleBox = BoundingBox([l,t,r,b])
        removedNode = []
        for p in doc.paths:
            if not p.box.beWrappedBy(scaleBox):
                removedNode.append(p)
        for t in doc.texts:
            if not t.box.beWrappedBy(scaleBox):
                removedNode.append(t)
        
        for rn in removedNode:
            doc.removeNode(rn)
        doc.resetCanvas()
        return doc.xmlStr



class TReaction(TargetNode):
    def __init__(self, tag: str, semantics: str = "reaction") -> None:
        super(TReaction, self).__init__(docObj=None, tag=tag, semantics=semantics)
        self.reactant = []
        self.product = []
        self.reagent = []
        self.catalyst = []
        self.solvent = []
        self.condition = []
    
    def semanticsMapIteritems(self):
        return iter(zip(
            ["reactant", "reagent", "product", "catalyst", "solvent", "env"], 
            [self.reactant, self.reagent, self.product, self.catalyst, self.solvent, self.condition]
        ))

    def toDict(self):
        return {
            "tag": self.tag,
            "semantics": self.semantics,
            "reactant": sorted([n.tag for n in self.reactant]),
            "reagent": sorted([n.tag for n in self.reagent]),
            "product": sorted([n.tag for n in self.product]),
            "catalyst": sorted([n.tag for n in self.catalyst]),
            "solvent": sorted([n.tag for n in self.solvent]),
            "condition": sorted([n.tag for n in self.condition])
        }

class TCondition(TargetNode):
    def __init__(self, docObj, tag: str, semantics: str = "condition", textList: List[str] = None, is_collection: bool = False) -> None:
        super(TCondition, self).__init__(tag=tag, semantics=semantics, docObj=docObj)
        self.textList = textList if textList else []
        self.isCollection = is_collection
        self.temperature = None
        self.reactionTime = None
        self.stirSpeed = None
        self.pressure = None
        self.gas = None

        for t in textList:
            self.parseText(t)
    

    def parseText(self, text):
        funcMap = {
            "temperature": self.isTemperatureText,
            "reaction_time": self.isTimeText,
            "stir_speed": self.isStirSpeedText,
            "pressure": self.isPressureText,
            "gas": self.isGasText
        }
        for attr, func in funcMap.items():
            if func(text):
                if attr in ["temperature", "reaction_time", "stir_speed", "pressure"]:
                    setattr(self, attr, self.uniformAmount(text))
                else:
                    setattr(self, attr, text)


    def toDict(self):
        return {
            "tag": self.tag,
            "semantics": self.semantics,
            "text_list": self.textList,
            "is_collection": self.isCollection,
            "temperature": self.temperature,
            "reaction_time": self.reactionTime,
            "stir_speed": self.stirSpeed,
            "pressure": self.pressure,
            "gas": self.gas,
        }  

    def drawGuideline(self, draw):
        super(TCondition, self).drawGuideline(
            draw=draw, 
            color="yellowgreen", 
            ext=2, 
            label="%s%s(%s)" % (self.tag, "*" if self.isCollection else "", self.semantics)
        )



    _timeUnits = ["h", "hr", "hrs", "hour", "hours", "min"]
    _stirSpeedUnits = ["rpm", "RPM"]
    _temperatureUnits = ["C", "°", "°C", "℃"]

    @classmethod
    def uniformUnit(cls, unit):
        times = 1
        if unit in cls._timeUnits:
            if unit == "min":
                times = float(1) / float(60)
            return "hr", times
        if unit in cls._stirSpeedUnits:
            return "RPM", times
        if unit in cls._temperatureUnits:
            return "C", times
        
        return unit, times

    @classmethod
    def uniformAmount(cls, text):
        res = re.findall(r'^\d+', text)
        if res and len(res) == 1:
            num = res[0]
            unit = text.replace(num, "").strip()
            if bool(re.search(r'\d', unit)):
                return text
            
            unit, times = cls.uniformUnit(unit)
            num = str(float(num) * times)
            return num + " " + unit

        return text


    @classmethod
    def isConditionText(cls, text: str) -> bool:
        return True in [
            cls.isTemperatureText(text),
            cls.isTimeText(text),
            cls.isStirSpeedText(text),
            cls.isPressureText(text),
            cls.isGasText(text)
        ]

    @classmethod
    def _haveNumber(cls, text) -> bool:
        return bool(re.search(r'\d', text))      

    @classmethod
    def isTemperatureText(cls, text: str) -> bool:
        for t in ["rt", "RT"]:
            if t in text:
                return True

        if cls._haveNumber(text):
            for t in cls._temperatureUnits:
                if text.endswith(t):
                    return True
        return False

    @classmethod
    def isTimeText(cls, text: str) -> bool:
        # 无数字情况
        for t in ["overnight"]:
            if t in text:
                return True
        # 数字 + 单位
        if cls._haveNumber(text):
            for t in cls._timeUnits:
                if text.endswith(t):
                    return True
        return False

    @classmethod
    def isStirSpeedText(cls, text: str) -> bool:
        if cls._haveNumber(text):
            for t in cls._stirSpeedUnits:
                if text.endswith(t):
                    return True
        return False

    @classmethod
    def isPressureText(cls, text: str) -> bool:
        if cls._haveNumber(text):
            for t in ["bar", "psi", "Mpa", "MPa", "atm"]:
                if text.endswith(t):
                    return True
        return False
        
    @classmethod
    def isGasText(cls, text: str) -> bool:
        for t in ["N2", "H2", "O2", "He", "CO2"]:
            if t in text:
                return True
        return False
    
    