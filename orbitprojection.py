from numpy import cos, sin, pi, tan, arccos, arctan, arcsin, cross, sinh, tanh, cosh, arctanh, arccos
from vector import Vector


class OrbitValues:
    def __init__(self, points, polar_points, perihelion, aphelion):
        self.points = points
        self.perihelion = perihelion
        self.aphelion = aphelion
        self.polar_points = polar_points
        self.child = None

class OrbitProjection:

    def __init__(self, attractor, orbit):
        self.attractor = attractor
        self.orbit = orbit
        self.cartesien = []
        self.orbit_values = None

    # Get r from angle
    def _get_polar_ellipse(self,angle):
        if self.orbit.e<1:
            r = self.orbit.a*(1-self.orbit.e**2)/(1+self.orbit.e*cos(angle))
        elif self.orbit.e==1:
            r = self.orbit.a/(1+self.orbit.e*cos(angle))
        else:
            if 1+self.orbit.e*cos(angle)!=0:
                r = self.orbit.a*(1-self.orbit.e**2)/(1+self.orbit.e*cos(angle))
            else:
                r  = self.orbit.a*(1-self.orbit.e**2)/(1+self.orbit.e*cos(angle+0.0000001))
        return r

           
    def get_collision_angle(self,R):
        angle_collision1 = arccos( self.orbit.a*(1-self.orbit.e**2)/(R*self.orbit.e)- 1/self.orbit.e )
        #("col",angle_collision1)
        #angle_collision2 = acos( self.orbit.a*(1-self.orbit.e**2)/(R2*self.orbit.e)- 1/self.orbit.e )
        return (angle_collision1,-angle_collision1)
    
    def get_collision_time(self,angle_collision,n):
        if angle_collision<0:
            angle_collision = 2 * pi + angle_collision 
        E = self.orbit.get_eccentric_from_true_anomaly(angle_collision)
        if self.orbit.e<1:
            M = E - self.orbit.e * sin(E)
        else:
            M = self.orbit.e * sinh(E) -E
        t = abs((M-self.orbit.M0)/n)+self.orbit.t0
        return t

    def get_position(self,angle):
        r=self._get_polar_ellipse(angle)
        return Vector(r*cos(angle),r*sin(angle),0)


    def intersect_child_attractor(self,attractor,aphelion):
        time_interval = []
        position_at_time = []
        n = (self.orbit.mu/(self.orbit.a**3))**0.5

        (a1, a2) = self.get_collision_angle(attractor.r.norm()-attractor.soi)
        (a1t, a2t) = (self.get_collision_time(a1,n),self.get_collision_time(a2,n))

        if (aphelion>attractor.r.norm()+attractor.soi):
            (a3,a4) = self.get_collision_angle( attractor.r.norm()+attractor.soi) 
            (a3t,a4t) =(self.get_collision_time(a3,n),self.get_collision_time(a4,n))
            time_interval.append([a1t,a3t])
            time_interval.append([a2t,a4t])
            position_at_time.append(self.get_position(a1))
            position_at_time.append(self.get_position(a3))
            position_at_time.append(self.get_position(a2))
            position_at_time.append(self.get_position(a4))

        else:
            time_interval.append([a1t,a2t])
            position_at_time.append(self.get_position(a1))
            position_at_time.append(self.get_position(a2))

        position_at_time = self.orbit.get_eci(position_at_time)
        
        for index,value in enumerate(time_interval):
            (t1,t2) = value 
            print(t1,t2)
            attractor_position1, attractor_speed1 = attractor.orbit.update_position(t1)
            attractor_position2, attractor_speed2 = attractor.orbit.update_position(t2)
            #attractor_position1 = self.orbit.get_eci(attractor_position1)
            #attractor_position2 = self.orbit.get_eci(attractor_position2)
            print(attractor.soi - (attractor_position1 - position_at_time[index*2]).norm())
            print(attractor.soi - (attractor_position2 - position_at_time[index*2+1]).norm())


    # return ellipse points
    def calculate_time_series(self, points=200, recursive = False):
        series=[]
        series_cartesien=[]
        escape_soi = False
        if (self.orbit == None or self.orbit.a==0):
            return (series, series_cartesien)
        angle = 0

        angle_max = 2*pi
        n = (self.orbit.mu/(abs(self.orbit.a)**3))**0.5


        # Calculate max and min
        perihelion,aphelion = self.orbit.get_limit()

        # Define min and max angle to draw
        if self.orbit.e==1:
            angle = 0
            angle_max = pi/3
        elif self.orbit.e>1:
            angle = -arccos(-1/self.orbit.e)
            angle_max = -angle-0.00000001

        
        #perihelion = self.orbit.get_eci(Vector(perihelion,0,0))


        # If we go outside the current attractor SOI
        # Calculate angle of exit and only draw points inside SOI
        if self.attractor.soi>0 and (aphelion > self.attractor.soi or self.orbit.e>=1):
            (angle1,angle2) = self.get_collision_angle(self.attractor.soi)
            angle = min(angle1,angle2)
            angle_max = max(angle1,angle2)


        # If we cross the attractor
        # Do not calculate point that are inside
        if perihelion<self.attractor.radius:
            (angle1,angle2) = self.get_collision_angle(self.attractor.radius)
            angle = max(angle1,angle2)
            angle_max = 2*pi - angle

        increment = (angle_max-angle) / points 

        # Calculate points
        while angle<(angle_max+increment) and not escape_soi:
            if angle>angle_max:
                angle = angle_max

            # Get distance for the angle
            r=self._get_polar_ellipse(angle)
            series.append((angle,r))

            # Populate cartesien coordonnates
            rv = self.orbit.get_eci(Vector(r*cos(angle),r*sin(angle),0))
            
            # If we are outside the attractor SOI, do not calculate 
            if self.attractor==None or self.attractor.soi==0 or r <= self.attractor.soi:
                if self.attractor.child == None:
                    series_cartesien.append(rv)
                else:
                    for att in self.attractor.child:
                        if rv.norm()>att.r.norm()-att.soi and rv.norm()<att.r.norm()+att.soi:
                            t = self.get_collision_time(angle, n)
                            print(t)

                            (r,v) = att.orbit.update_position(t) 
                            d = (r-rv).norm()
                            if (abs(d)<att.soi):
                                print(r,rv)
                                print("interception",att.name,t,r,rv,d,att.soi,d-att.soi)
                                escape_soi = True
                    series_cartesien.append(rv)
                
            # More point when near the aphelion
            if self.orbit.e>0.9 and self.orbit.e<1 and self.orbit.a>100000000:
                if angle > pi/2 and angle < 3*pi/2:
                    local_increment = increment/4
                else:
                    local_increment = increment*4
            else:
                local_increment = increment
            angle+=local_increment

        # Transform coordonnates to ECI
        #series_cartesien = self.orbit.get_eci(series_cartesien)
        perihelion = self.orbit.get_eci(Vector(perihelion,0,0))

        if self.orbit.e<1:
            if aphelion<self.attractor.soi:
                aphelion = Vector(-aphelion,0,0)
            else:
                aphelion = Vector(-self.attractor.soi, 0,0)

            aphelion = self.orbit.get_eci(aphelion)
             
        else:
            aphelion = None

        self.orbit_values = OrbitValues(series_cartesien,series, perihelion,aphelion)


