import numpy as np

class Vector: 


    def __init__(self, x, y=0, z=0):

        if isinstance(x,list):
            (self.x, self.y, self.z) = (np.float64(x[0]),np.float64(x[1]),np.float64(x[2]))
        else:
            (self.x, self.y, self.z) = (np.float64(x), np.float64(y),np.float64( z))
        
    
    def __mul__(self, factor):
        if isinstance(factor,(int,float)):
            x = factor * self.x
            y = factor * self.y
            z = factor * self.z
            return self.__class__(x,y,z)
        elif isinstance(factor, Vector):
            return self.dot(factor)
        return None


    def norm(self):
        return ( self.x**2 + self.y**2 + self.z**2 ) ** 0.5

    def __rmul__(self,factor):
        return self.__mul__(factor)
    
    def __add__(self, v):

        if (isinstance(v,Vector)):
            v = v.to_list()

        if (not isinstance(v,list) or len(v) != 3):
            return None

        u = self.to_list()
        for i in range(len(u)):
            u[i] += v[i]
        return self.__class__(u)

    def dot(self, v):
        if not isinstance(v, Vector):
            return None
        return (self.x * v.x + self.y * v.y + self.z * v.z)
        return sum(a * b for a, b in zip(self, v))


    def cross(self,v):
        if not isinstance(v, Vector):
            return None
        
        x = self.y * v.z - self.z * v.y
        y = self.z * v.x - self.x * v.z
        z = self.x * v.y - self.y * v.x

        return self.__class__(x,y,z)


    def __sub__(self,v):
        return self.__add__(v*-1)


    def __truediv__(self,factor):
        if isinstance(factor,(int,float)):
            return self.__mul__(1/factor)

    def __iter__(self):
        return self.to_list().__iter__()

    def to_list(self):
        return [self.x, self.y, self.z]

    def __str__(self):
        return "[ %r, %r, %r]" %(self.x,self.y,self.z)

if __name__ == '__main__':
    v = Vector(1,3,-5)
    print(v.cross(Vector(4,9,2)))
    print(v+Vector(1,2,3))    
    print(v-Vector(1,2,30))
    print(v.dot(Vector(4,-2,-1)))
    print(v/3.0)
    print(v.norm())