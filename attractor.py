class Attractor:

    def __init__(self, r, diameter, mu=None, mass=None, soi=None):
        self.mass = mass
        self.soi =  soi
        self.parent = None
        self.child = []
        self.r = r
        self.mu = mu
        self.diameter = diameter

    def set_pos(self,r):
        self.r = r

    def set_mass(self, mass):
        self.mass = mass
    
    def set_soir(self, soi):
        self.soi = soi

    def get_pos(self):
        return self.r

