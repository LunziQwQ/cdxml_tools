from ..boundingbox import BoundingBox
from .node import SvgNode


class SvgDoc(SvgNode):
    def init(self):
        self.paths = self.childrenByTag("path", SvgPath)
        self.texts = self.childrenByTag("text", SvgText)
        self.width = float(self.attr("width").replace("px", ""))
        self.height = float(self.attr("height").replace("px", ""))

    def removeNode(self, node):
        if isinstance(node, SvgPath):
            self.paths.remove(node)
        if isinstance(node, SvgText):
            self.texts.remove(node)
        self.xmlElement.childNodes.remove(node.xmlElement)

    def setCanvasBox(self, width: float, height: float):
        self.width = width
        self.height = height
        self.setattr("width", str(width)+"px")
        self.setattr("height", str(height)+"px")
        self.setattr("viewBox", "0 0 %f %f" % (width, height))

    def resetCanvas(self):
        # 将剩余元素平移至左上角（10,10）并缩小画布
        allLtrb = [p.box.ltrb for p in self.paths] + [t.box.ltrb for t in self.texts]
        canvasL = min([l for l,t,r,b in allLtrb])
        canvasT = min([t for l,t,r,b in allLtrb])
        canvasR = max([r for l,t,r,b in allLtrb])
        canvasB = max([b for l,t,r,b in allLtrb])
        xOffset = 20 - canvasL
        yOffset = 20 - canvasT
        canvasWidth = canvasR - canvasL + 50
        canvasHeight = canvasB - canvasT + 50
        self.setCanvasBox(canvasWidth, canvasHeight)
        for p in self.paths:
            p.applyTransformOffset((xOffset, yOffset))
        for t in self.texts:
            t.applyTransformOffset((xOffset, yOffset))
    
    def copy(self):
        return SvgDoc.fromXML(self.xmlStr) 




class SvgPath(SvgNode):
    def init(self):
        self.d = self.attr("d")
        self.transform = self.attr("transform")
        self.box = BoundingBox(self.realLtrb)

    def applyTransformOffset(self, offset):
        xOffset, yOffset = offset
        newDStr = ""
        for d in self.dList:
            if len(d) <= 1:
                newDStr += str(d[0])
                continue
            x, y = self.transformer.transform(d[1], d[2])
            x += xOffset
            y += yOffset
            newX, newY = self.transformer.reverseTransform(x, y)
            newDStr += "%s %f,%f " % (d[0], newX, newY)

        self.d = newDStr
        self.setattr("d", newDStr)

    @property  
    def dList(self):
        chunks = self.d.split(" ")
        dList = []
        for i, t in enumerate(chunks):
            if t in ["M", "L"]:
                x, y = [float(c) for c in chunks[i+1].split(",")]
                dList.append((t, x, y))
                i += 1
                continue
            if t == "Z":
                dList.append(t)
        return dList
    
    @property
    def realLtrb(self):
        xyList = [self.transformer.transform(d[1], d[2]) for d in self.dList if len(d) == 3]
        xList, yList = zip(*xyList)
        return min(xList), min(yList), max(xList), max(yList)


class SvgText(SvgNode):
    def init(self):
        self.x, self.y = float(self.attr("x")), float(self.attr("y"))
        self.fontSize = float(self.attr("font-size").replace("px", ""))
        self.box = BoundingBox(self.realLt + self.realLt)

    def applyTransformOffset(self, offset):
        xOffset, yOffset = offset
        x, y, _, _ = self.box.ltrb
        x += xOffset
        y += yOffset
        newX, newY = self.transformer.reverseTransform(x, y)
        self.setattr("x", str(newX))
        self.setattr("y", str(newY)) 

    @property
    def realLt(self):
        return self.transformer.transform(self.x, self.y)

    @property
    def text(self):
        return self.xmlElement.childNodes[0].data
