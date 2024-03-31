from chip_draw.methods.geom import *
import gdspy

class Component():
	def __init__(self, lib, cell_name):
		self.lib = lib
		self.cell_name = cell_name
		self.cell = gdspy.Cell( self.cell_name )
		self.lib.add(self.cell)
		
		self.keepout = [] 			#List of keepout polygons
		self.p_coords = array([])	#Array of port coordinates
		self.p_dirs = array([])		#Array of port directions pointed inside the component
	
	def place(self, top_cell, point, direction = 0, port = 0):
		#Port directions are pointed inside
		point = array(point)
		
		place_origin = point - transform(self.p_coords[port],(0,0),direction-self.p_dirs[port])
		rotation = direction - self.p_dirs[port]
		p_coords = zeros((len(self.p_coords),2))
		p_dirs = zeros(len(self.p_dirs))
		for i,p_coord in enumerate(self.p_coords):
			p_coords[i] = transform(p_coord, place_origin, rotation)
			p_dirs[i] = self.p_dirs[i] + rotation
		
		top_cell.add(gdspy.CellReference(self.cell, place_origin, degrees(rotation)))	
		
		#Port directions are pointed outside
		ports = []
		for p_coord, p_dir in zip(p_coords, p_dirs):
			ports += [{'point':p_coord,'direction':p_dir+pi},]
			
		inst = ComponentInstance()
		inst.ports = ports
		return inst

class ComponentInstance():
	def __init__(self):
		self.keepout = [] 	#Keepout polygons
		self.ports = []		#Ports