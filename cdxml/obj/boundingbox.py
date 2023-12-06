import math
from typing import Self, Tuple



class BoundingBox(object):
    __slots__ = ("left", "top", "right", "bottom")

    @classmethod
    def loadByLtwhDict(cls, ltwh):
        return cls((
            ltwh["l"], 
            ltwh["t"], 
            ltwh["l"] + ltwh["w"],
            ltwh["t"] + ltwh["h"]
        ))


    def __init__(self, coord: Tuple[float, float, float, float]):
        self.left = min(coord[0], coord[2])
        self.top = min(coord[1], coord[3])
        self.right = max(coord[0], coord[2])
        self.bottom = max(coord[1], coord[3])
    
    def beWrappedBy(self, bb: Self):
        """自身Box被传入Box包裹"""
        return (bb.left <= self.left) and \
               (bb.top <= self.top) and \
               (bb.right >= self.right) and \
               (bb.bottom >= self.bottom)
    
    def beHoldBy(self, bb: Self):
        """
            自身Box中心是否处于传入的Box范围内
        """
        x, y = self.center
        return (x >= bb.left and x <= bb.right) and \
               (y >= bb.top and y <= bb.bottom)
    
    def offsetAndScale(self, offset, scale):
        xScale, yScale = scale
        return BoundingBox((
            (self.left + offset[0]) * xScale,
            (self.top + offset[1]) * yScale,
            (self.right + offset[0]) * xScale,
            (self.bottom + offset[1]) * yScale,
        ))
    
    def extend(self, left=0, top=0, right=0, bottom=0):
        return BoundingBox((
            self.left - left,
            self.top - top,
            self.right + right,
            self.bottom + bottom
        ))
    
    def direction(self, bb):
        """
        传入Box相对自身Box的方位，两个维度均有差异时返回差异较大的维度
        return: t/b/l/r 表达上下左右
        """
        x, y = self.center
        bx, by = bb.center
        hDiff = y - by
        vDiff = x - bx
        if abs(hDiff) > abs(vDiff):
            return "t" if hDiff > 0 else "b"
        else:
            return "l" if vDiff > 0 else "r"

    def distance(self, bb, useMin4=False):
        # 传入Box中心距离自身边界最近距离
        if useMin4:
            x2, y2 = bb.center
            return min(
                math.sqrt((self.left-x2)**2 + (self.top-y2)**2),
                math.sqrt((self.left-x2)**2 + (self.bottom-y2)**2),
                math.sqrt((self.right-x2)**2 + (self.top-y2)**2),
                math.sqrt((self.right-x2)**2 + (self.bottom-y2)**2)
            )
        # 传入Box中心距离自身中心距离
        else:
            x1, y1 = self.center
            x2, y2 = bb.center
            return math.sqrt((x1-x2)**2 + (y1-y2)**2)
    
    def __str__(self):
        return str((self.left, self.top, self.right, self.bottom))
    
    def __repr__(self):
        return repr((self.left, self.top, self.right, self.bottom))
    
    @property
    def width(self):
        return self.right - self.left
    
    @property
    def height(self):
        return self.bottom - self.top
    
    @property
    def ratio(self):
        return self.width / self.height
    
    @property
    def area(self):
        return self.width * self.height
    
    @property
    def center(self):
        return self.left + self.width/2, self.top + self.height/2
    
    @property
    def ltrb(self):
        return self.left, self.top, self.right, self.bottom

    @property
    def ltwh(self):
        return round(self.left, 2), round(self.top, 2), round(self.width, 2), round(self.height, 2)

    @property
    def ltwhDict(self):
        return dict(zip(["l", "t", "w", "h"], self.ltwh))