import copy
import functools
from typing import Self

class TargetNode:
    def __init__(self, docObj, tag: str, semantics:str) -> None:
        self.docObj = docObj
        self.tag = tag
        self.semantics = semantics
        if docObj:
            self.box = copy.deepcopy(docObj.box)
            self.hash = hash(docObj)
        self.father = None
        self.child = {"l": [], "t": [], "r": [], "b": []}
        self.childDistances = {}
    
    @property
    def childDict(self):
        child = {}
        for direction, tagList in self.child.items():
            if tagList:
                child[direction] = tagList
        return child

    def offsetScaleBorderLtrb(self, imgSize, ext=0):
        if not hasattr(self, "box") or not self.box:
            return None
        offset, scale = self.docObj.root.pngOffsetScale(imgSize)
        box = self.box.offsetAndScale(offset, scale)
        
        xSize, ySize = imgSize
        l = max(box.left - ext, 1)
        t = max(box.top - ext, 1)
        r = min(box.right + ext, xSize - 1)
        b = min(box.bottom + ext, ySize - 1)
        return l, t, r, b

    def addFather(self, fatherNode: Self, distance):
        self.father = fatherNode.tag
        direction = fatherNode.box.direction(self.box)
        fatherNode.childDistances[self.tag] = distance
        fatherNode.child[direction].append(self.tag)
        fatherNode.child[direction].sort(key=lambda x: fatherNode.childDistances[x])

    def drawGuideline(self, draw, color="red", ext=0, label=None):
        l, t, r, b = self.offsetScaleBorderLtrb(imgSize=draw.im.size, ext=ext)
        draw.rectangle(
            ((l, t), (r, b)),
            fill=None, outline=color, width=1
        )
        draw.text(
            (l, b), 
            (f"{self.docObj.xmlElement.tagName}\n%0.0f %0.0f %0.0f %0.0f" % tuple(self.docObj.coord)) 
                      if label is None else label, 
            font=self.docObj.root.font, 
            fill=color
        )
    
    def cutImgRegion(self, image, ext=0):
        l, t, r, b = self.offsetScaleBorderLtrb(imgSize=image.size, ext=ext)
        return image.crop((l,t,r,b))
         
