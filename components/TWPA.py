from numpy import *
import gdspy
import copy as cpy
from chip_draw.components.base_classes import *
from chip_draw.methods.geom import *
import zlib
import scipy.constants as sc

class CNE_TWPACell_SiO2(Component):
	def __init__(self, lib, cell_name):
		Component.__init__(self, lib, cell_name)
		self.jj = {	'd':1,
					'd_via': 0.5,
					'layer':120,	
					'top_layer':30,
					'bottom_layer':20,
					'via_layer':121,
					'clear':1}
					
		self.cap = {'top_layer':20,
					'bottom_layer':10,
					'l':7,
					'c':50e-15,	#Capacitance
					'clear':1,	#Cap to cell border clearence
					'eps':3.6,	#SiO2 dielectric
					't':200e-9}
		self.gnd_layer = 10			
		self.bend_angle = 0	#Signed
		
	def draw(self):
		#Width of conductor connecting JJs in top layer
		conductor_w = self.jj['d']+self.jj['clear']*2
		#Capacitor
		cap_w = 1e6*self.cap['c']/( sc.epsilon_0*self.cap['eps']*self.cap['l']*1e-6/self.cap['t'] )
		#Cell length
		l = self.cap['l']+self.cap['clear']*2
		ymax = cap_w-conductor_w/2
		ymin = -conductor_w/2
		#Capacitor
		self.cell.add( gdspy.Rectangle( (-self.cap['l']/2, -conductor_w/2), (self.cap['l']/2, cap_w-conductor_w/2),
										layer = self.cap['top_layer']) ) 
		#JJs
		jj_x = self.cap['l']/2 - self.jj['d']/2 - self.jj['clear']
		self.cell.add(gdspy.Round((-jj_x,0), self.jj['d']/2, layer = self.jj['layer']))
		self.cell.add(gdspy.Round((-jj_x,0), self.jj['d_via']/2, layer = self.jj['via_layer']))
		self.cell.add(gdspy.Round((jj_x,0), self.jj['d']/2, layer = self.jj['layer']))
		self.cell.add(gdspy.Round((jj_x,0), self.jj['d_via']/2, layer = self.jj['via_layer']))
		#Keepout polygon
		dx_top = -sin(self.bend_angle) * ymax
		dx_bot = -sin(self.bend_angle) * ymin
		self.keepout = [gdspy.Polygon( ((-l/2-dx_bot/2, ymin),
										(-l/2-dx_top/2, ymax),
										(l/2+dx_top/2, ymax),
										(l/2+dx_bot/2, ymin)) ),]
		#Conductors
		dx = sin(self.bend_angle) * conductor_w/2
		conductor_l = self.cap['clear']+self.jj['d']+self.jj['clear']*2
		poly = gdspy.Polygon( ((-l/2-dx/2, -conductor_w/2),
								(-l/2+dx/2, conductor_w/2),
								(-l/2+conductor_l, conductor_w/2),
								(-l/2+conductor_l, -conductor_w/2)),
								layer = self.jj['top_layer'])
		
		self.cell.add(poly)
		self.cell.add( cpy.copy(poly).mirror((0,1)) )
		#Ground
		gnd = gdspy.copy(self.keepout[0])
		gnd.layers[0] = self.gnd_layer	
		self.cell.add(gnd)
		#Ports
		self.p_coords = array( ((-self.cap['l']/2-self.cap['clear'],0),
							(self.cap['l']/2+self.cap['clear'],0)) )
		self.p_dirs = array((-self.bend_angle/2, pi+self.bend_angle/2))	#Port directions are pointed inside
	
	def optimaze_bend(self, radius, angle):
		l = self.cap['l']+self.cap['clear']
		n = round( angle/(2*arcsin(l/(2*radius))) )
		self.bend_angle = angle/n
		return n, l/sin(self.bend_angle/2) #Optimized radius