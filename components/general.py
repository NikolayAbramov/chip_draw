from numpy import *
import gdspy
import copy as cpy
from chip_draw.methods.geom import *
from chip_draw.components.helper_classes import *

class Meander():
	def __init__(self, lib, cell_name):
		self.layer = 1
		self.w = 5
		self.span = 50
		self.half_period = 10
		self.kind = 1
		self.n = 3
		self.lib = lib
		self.cell_name = cell_name
		self.cell = None
#	Kind 1
#	 ### ###
#	 # # # #
#	 # ### #
#	 |     |
#	 0     1		
#	Kind 2
#	  ### ###
#	  # # # #
#	0-# ### #-1
#	Kind 3
#	  ### ###
#	0-# # # #-1
#	    ###
	def draw(self):
		if self.n<1:
			raise ValueError("Meander n must be >1")
		self.cell = gdspy.Cell( self.cell_name )
		self.lib.add(self.cell)
		if (self.kind == 1) or (self.kind == 2):
			path = gdspy.Path(self.w, initial_point=(0,0))
			path.segment(self.span/2+self.w/2, direction = '+y', layer = self.layer)
		else:
			path = gdspy.Path(self.w, initial_point=(0,self.span/2))
			path.segment(self.w/2, direction = '+y', layer = self.layer)
		self.cell.add(path)
		
		step = self.half_period
		w = self.w
		span = self.span
		poly = gdspy.Polygon(	((-step/2-w/2, 0),
								(-step/2-w/2, span/2+w/2),
								(step/2+w/2, span/2+w/2),
								(step/2+w/2, 0),
								(step/2-w/2, 0),
								(step/2-w/2, span/2-w/2),
								(-step/2+w/2, span/2-w/2),
								(-step/2+w/2, 0)), layer = self.layer)
		poly.translate(step/2,0)						
		for i in range(self.n):
			if i%2:
				self.cell.add(cpy.copy(poly).mirror((1,0)).translate(i*self.half_period, self.span/2+self.w/2))
			else:
				self.cell.add(cpy.copy(poly).translate(i*self.half_period,self.span/2+self.w/2))
		
		path = gdspy.Path(self.w, initial_point=(self.half_period*self.n, self.span/2+self.w/2))
		if (self.kind == 1) or (self.kind == 2):
			if self.n%2:
				path.segment(self.span/2+self.w/2, direction = '-y', layer = self.layer)
			else:
				path.segment(self.span/2+self.w/2, direction = '+y', layer = self.layer)
		else:
			if self.n%2:
				path.segment(self.w/2, direction = '-y', layer = self.layer)
			else:
				path.segment(self.w/2, direction = '+y', layer = self.layer)
		self.cell.add(path)
	
	def place(self, top_cell, origin, direction = 0, port = 0):
		#Port directions are pointed inside
		origin = array(origin)
		p_coords = zeros((2,2))
		p_dirs = zeros(2)
		if self.kind == 1:
			p_coords[0] = (0, 0)
			p_dirs[0] = pi/2
			if self.n%2:
				p_coords[1] = array((self.half_period*self.n, 0))
				p_dirs[1] = pi/2
			else:
				p_coords[1] = array((self.half_period*self.n, self.span+self.w))
				p_dirs[1] = -pi/2 	
		elif self.kind == 2:
			p_coords[0] = (-self.w/2, self.w/2)
			p_dirs[0] = 0.
			if self.n%2:
				p_coords[1] = array((self.half_period*self.n+self.w/2, self.w/2))
				p_dirs[1] = pi
			else:
				p_coords[1] = array((self.half_period*self.n+self.w/2, self.span+self.w/2))
				p_dirs[1] = pi 
		elif self.kind == 3:
			p_coords[0] = (-self.w/2, self.span/2+self.w/2)
			p_dirs[0] = 0.
			p_coords[1] = array((self.half_period*self.n+self.w/2, self.span/2+self.w/2))
			p_dirs[1] = pi
		else:
			Raise(ValueError)
		place_origin, rotation, p_coords_new, p_dirs_new = place_ports(port, origin, direction, p_coords, p_dirs)
		top_cell.add(gdspy.CellReference(self.cell, place_origin, degrees(rotation)))	
		'''
		#Keepout polygon
		bb = self.cell.get_bounding_box()
		keepout_polygon = gdspy.Rectangle( bb[0], bb[1] )
		keepout_polygon.rotate(rotation)
		keepout_polygon.translate(place_origin[0], place_origin[1])
		return {'p1':place_p1,'p2':place_p2, 'keepout':keepout_polygon}
		pass
		'''
		#Port directions are pointed outside
		ports = []
		for p_coord, p_dir in zip(p_coords_new, p_dirs_new):
			ports += [{'point':p_coord,'direction':p_dir+pi},]
			
		inst = ComponentInstance()
		inst.ports = ports
		return inst