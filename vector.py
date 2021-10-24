########################################
# Small Vector management class
########################################

import numpy as np

class Vector: 

    # Create Vector instance from list or values
    def __init__(self, x, y=0, z=0):

        if isinstance(x,list):
            (self.x, self.y, self.z) = (np.float64(x[0]),np.float64(x[1]),np.float64(x[2]))
        else:
            (self.x, self.y, self.z) = (np.float64(x), np.float64(y),np.float64( z))
        
    # Multiply vector
    def __mul__(self, factor):
        if isinstance(factor,(int,float)):
            x = factor * self.x
            y = factor * self.y
            z = factor * self.z
            return self.__class__(x,y,z)
        elif isinstance(factor, Vector):
            return self.dot(factor)
        return None

    # Calculate norm of the vector
    def norm(self):
        return ( self.x**2 + self.y**2 + self.z**2 ) ** 0.5

    # Enable use of * sign to multiply vector
    def __rmul__(self,factor):
        return self.__mul__(factor)
    
    # Enable use of + sign to add vector
    def __add__(self, v):

        if (isinstance(v,Vector)):
            v = v.to_list()

        if (not isinstance(v,list) or len(v) != 3):
            return None

        u = self.to_list()
        for i in range(len(u)):
            u[i] += v[i]
        return self.__class__(u)

    # Calculate dot of two vectors
    def dot(self, v):
        if not isinstance(v, Vector):
            return None
        return (self.x * v.x + self.y * v.y + self.z * v.z)
        return sum(a * b for a, b in zip(self, v))

    # Calculate cross of two vectors
    def cross(self,v):
        if not isinstance(v, Vector):
            return None
        
        x = self.y * v.z - self.z * v.y +.0
        y = self.z * v.x - self.x * v.z +.0
        z = self.x * v.y - self.y * v.x +.0

        return self.__class__(x,y,z)

    def angle2D(self):
        angle = np.arctan(self.y/self.x)
        if self.x<0: 
            return angle + np.pi

        return angle


    # Enable use of - sign to substracte vector
    def __sub__(self,v):
        return self.__add__(v*-1)


    def __truediv__(self,factor):
        if isinstance(factor,(int,float)):
            return self.__mul__(1/factor)

    def __iter__(self):
        return self.to_list().__iter__()

    # Convert vector to list
    def to_list(self):
        return [self.x, self.y, self.z]
        
    # Convert vector to str
    def __str__(self):
        return "[ %r, %r, %r]" %(self.x,self.y,self.z)

    # Unary operator
    def __neg__(self):
        return self.__mul__(-1)