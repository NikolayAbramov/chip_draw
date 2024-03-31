from numpy import *
import gdspy
import copy as cpy
from chip_draw.components.general import *
from chip_draw.components.base_classes import *
from chip_draw.methods.geom import *
import zlib

#CNE test structure
class SQLoopLumpedResonator():
	def __init__(self, lib, cell_name):
		self.cpw = {'layer':30 ,
					'GND_layer':30,
					'w':20, 
					'g':10,
					'bridge_w':3}
								
		self.cap = {'bottom_layer':30, 
					'top_layer':330,
					'cap_via_layer':331,
					'cap_via_clear': 10,
					'top_cond_layer':40,
					'via_layer':31,
					'via_size':2,
					'via_clear': 2,
					'bottom_to_bottom_clear':5,
					'w':100,
					'l':100}
		self.loop = {'layer':30,
					'w':50,
					'l':300,
					'line_w':5,
					'cpw_dist': 50}
		self.gnd_clear = 15
		self.gnd_w = 10
		self.cell_name = cell_name
		self.lib = lib
		self.cell = None
		self.ports = {1:array((0,0)),2:array((0,0))}
		
	def draw(self):
	
		cell = gdspy.Cell( self.cell_name )
		self.lib.add(cell)
		
		cell_size = array( (self.loop['l']+self.gnd_clear*2+self.loop['line_w']+self.gnd_w*2,
							self.cpw['w']/2+self.cpw['g']+self.gnd_clear+self.gnd_w*2+self.loop['cpw_dist']+
								+ self.loop['w']-self.loop['line_w']/2+self.cap['w']))						
		#CPW central
		path = gdspy.Path(self.cpw['w'], initial_point=(-cell_size[0]/2, 0))
		path.segment(cell_size[0], layer = self.cpw['layer'])
		cell.add(path)
		#GND
		cell.add( gdspy.Rectangle( (-cell_size[0]/2, self.cpw['w']/2 + self.cpw['g'] + self.gnd_w  ), 
									(cell_size[0]/2, self.cpw['w']/2 + self.cpw['g']),layer = self.cpw['GND_layer']) )
									
		rect1 = gdspy.Rectangle( (-cell_size[0]/2, -self.cpw['w']/2 - self.cpw['g']   ), 
									(cell_size[0]/2, -(cell_size[1]-self.cpw['w']/2-self.cpw['g']-self.gnd_w)))
		
		rect2 = gdspy.Rectangle( (-cell_size[0]/2+self.gnd_w, -self.cpw['w']/2 - self.cpw['g']   ), 
									(cell_size[0]/2-self.gnd_w, -(cell_size[1]-self.cpw['w']/2-self.cpw['g'])+2*self.gnd_w ))
		
		cell.add(gdspy.boolean(rect1, rect2, 'not', layer = self.cpw['GND_layer']))							
		#GND bridges
		rect1 = gdspy.Rectangle( (-self.cpw['bridge_w']/2, -self.cpw['w']/2-self.cpw['g']),
								(self.cpw['bridge_w']/2, self.cpw['w']/2+self.cpw['g']), layer = self.cpw['GND_layer'] )
		cell.add(cpy.copy(rect1).translate( -cell_size[0]/2+self.gnd_w-self.cpw['bridge_w']/2, 0))
		cell.add(cpy.copy(rect1).translate( cell_size[0]/2-self.gnd_w+self.cpw['bridge_w']/2, 0))
		#Loop
		path = gdspy.FlexPath( ((-self.cap['w']/2, 0),
							(-self.loop['l']/2, 0),
							(-self.loop['l']/2, self.loop['w']),
							(self.loop['l']/2, self.loop['w']),
							(self.loop['l']/2, 0),
							(self.cap['w']/2+self.cap['bottom_to_bottom_clear']+self.cap['via_size']+
								self.cap['via_clear']*2, 0)),
							self.loop['line_w'],
							gdsii_path = True,
							layer = self.loop['layer'])
		path.translate( 0, -self.loop['cpw_dist']-self.loop['w'])	
		cell.add(path)
		#Cap bottom electrode
		rect = gdspy.Rectangle( (-self.cap['l']/2, self.loop['line_w']/2 ),
						(self.cap['l']/2, -self.cap['w']+self.loop['line_w']/2 ),	
							layer = self.cap['bottom_layer'])
		rect.translate(0, -self.loop['cpw_dist']-self.loop['w'])				
		cell.add(rect)
		#Cap top electrode
		rect = gdspy.Rectangle( (-self.cap['l']/2, self.loop['line_w']/2 ),
						(self.cap['l']/2, -self.cap['w']+self.loop['line_w']/2 ),	
							layer = self.cap['top_layer'])
		rect.translate(0, -self.loop['cpw_dist']-self.loop['w'])				
		cell.add(rect)
		#Cap via
		rect = gdspy.Rectangle( (-self.cap['l']/2+self.cap['cap_via_clear'], self.loop['line_w']/2 - self.cap['cap_via_clear']  ),
						(self.cap['l']/2 - self.cap['cap_via_clear'], -self.cap['w']+self.loop['line_w']/2 + self.cap['cap_via_clear'] ),
							layer = self.cap['cap_via_layer'])
		rect.translate(0, -self.loop['cpw_dist']-self.loop['w'])				
		cell.add(rect)
		#Cap top conductor
		rect = gdspy.Rectangle( (-self.cap['l']/2, self.loop['line_w']/2   ),
						(self.cap['l']/2 + self.cap['bottom_to_bottom_clear'] + 
						self.cap['via_clear']*2 + self.cap['via_size'], -self.cap['w']+self.loop['line_w']/2 ),	
							layer = self.cap['top_cond_layer'])
		rect.translate(0, -self.loop['cpw_dist']-self.loop['w'])				
		cell.add(rect)
		#Conecting via
		rect = gdspy.Rectangle( (-self.cap['via_size']/2, -self.cap['via_size']/2), 
								(self.cap['via_size']/2, self.cap['via_size']/2),
								layer = self.cap['via_layer'])
		rect.translate( self.cap['l']/2+self.cap['via_clear']+self.cap['via_size']/2+self.cap['bottom_to_bottom_clear'],
						-self.loop['cpw_dist']-self.loop['w']+self.loop['line_w']/2-
						self.cap['via_clear']-self.cap['via_size']/2)
		cell.add(rect)
		#Conecting via bottom pad
		rect = gdspy.Rectangle( (-self.cap['via_size']/2-self.cap['via_clear'], -self.cap['via_size']/2-self.cap['via_clear']), 
								(self.cap['via_size']/2+self.cap['via_clear'], self.cap['via_size']/2+self.cap['via_clear']),
								layer = self.cap['bottom_layer'])
		rect.translate( self.cap['l']/2+self.cap['via_clear']+self.cap['via_size']/2+self.cap['bottom_to_bottom_clear'],
						-self.loop['cpw_dist']-self.loop['w']+self.loop['line_w']/2-
						self.cap['via_clear']-self.cap['via_size']/2)
		cell.add(rect)
		self.cell = cell
		#Ports coordinates
		self.ports[1] = array((-cell_size[0]/2,0))
		self.ports[2] = array((cell_size[0]/2,0))
		
	def place(self, top_cell, origin, direction = 0, port = 1):
		origon = array(origin)
		bonding_box = self.cell.get_bounding_box()
		l = bonding_box[1,0]-bonding_box[0,0]
		t = array((l*cos(direction), l*sin(direction)))
		place_origin = origin+t/2
		if port==1:
			rotation = direction
			top_cell.add(gdspy.CellReference(self.cell, place_origin, degrees(rotation)))
			p1  = origin
			p2  = origin + t
		elif port ==2:
			rotation = direction+pi
			top_cell.add(gdspy.CellReference(self.cell, place_origin, degrees(rotation)))
			p1 = origin + t
			p2 = origin
		else:
			Raise(ValueError)
		#Keepout polygon
		bb = self.cell.get_bounding_box()
		keepout_polygon = gdspy.Rectangle( bb[0], bb[1] )
		keepout_polygon.rotate(rotation)
		keepout_polygon.translate(place_origin[0], place_origin[1])
		return {'p1':p1,'p2':p2, 'keepout':keepout_polygon}
		
#CNE test structure
class SiO2LumpedResonator():
	def __init__(self, lib, cell_name):
		self.cpw = {'layer':30 ,
					'GND_layer':30,
					'w':20, 
					'g':10,
					'bridge_w':3}
								
		self.cap = {'bottom_layer':30,
					'top_cond_layer':40,
					'via_layer':31,
					'via_size':2,
					'via_clear': 2,
					'bottom_to_bottom_clear':5,
					'w':100,
					'l':100}
		self.ind = {'layer':30,
					'step':10,	#Meander step
					'n':3, 		#Number of meander half periods
					'step1':30, #Coupling section
					'l':300,
					'w':5,
					'cpw_dist': 50}
		self.gnd_clear = 15
		self.gnd_w = 10
		self.cell_name = cell_name
		self.lib = lib
		self.cell = None
		self.ports = {1:array((0,0)),2:array((0,0))}
		
	def draw(self):
	
		cell = gdspy.Cell( self.cell_name )
		self.lib.add(cell)
		#Inductor width calculation
		ind_w = self.ind['step1']+self.ind['step']*(self.ind['n']+1)
		#Cell size calculation
		cell_size = array( (self.ind['l'] + self.gnd_clear*2+self.ind['w'] + self.gnd_w*2,
							self.cpw['w']/2 + self.cpw['g'] + self.gnd_w + self.ind['cpw_dist']+
							+ ind_w + self.cap['w'] - self.ind['w']/2 + self.gnd_clear + self.gnd_w) )						
		#CPW central
		path = gdspy.Path(self.cpw['w'], initial_point=(-cell_size[0]/2, 0))
		path.segment(cell_size[0], layer = self.cpw['layer'])
		cell.add(path)
		#GND
		cell.add( gdspy.Rectangle( (-cell_size[0]/2, self.cpw['w']/2 + self.cpw['g'] + self.gnd_w  ), 
									(cell_size[0]/2, self.cpw['w']/2 + self.cpw['g']),layer = self.cpw['GND_layer']) )
									
		rect1 = gdspy.Rectangle( (-cell_size[0]/2, -self.cpw['w']/2 - self.cpw['g']   ), 
									(cell_size[0]/2, -(cell_size[1]-self.cpw['w']/2-self.cpw['g']-self.gnd_w)))
		
		rect2 = gdspy.Rectangle( (-cell_size[0]/2+self.gnd_w, -self.cpw['w']/2 - self.cpw['g']   ), 
									(cell_size[0]/2-self.gnd_w, -(cell_size[1]-self.cpw['w']/2-self.cpw['g'])+2*self.gnd_w ))
		
		cell.add(gdspy.boolean(rect1, rect2, 'not', layer = self.cpw['GND_layer']))							
		#GND bridges
		rect1 = gdspy.Rectangle( (-self.cpw['bridge_w']/2, -self.cpw['w']/2-self.cpw['g']),
								(self.cpw['bridge_w']/2, self.cpw['w']/2+self.cpw['g']), layer = self.cpw['GND_layer'] )
		cell.add(cpy.copy(rect1).translate( -cell_size[0]/2+self.gnd_w-self.cpw['bridge_w']/2, 0))
		cell.add(cpy.copy(rect1).translate( cell_size[0]/2-self.gnd_w+self.cpw['bridge_w']/2, 0))
		#Inductor
		path = gdspy.FlexPath( ((-self.cap['l']/2, 0),
							(-self.ind['l']/2, 0),
							(-self.ind['l']/2, ind_w ),
							(self.ind['l']/2, ind_w ),
							(self.ind['l']/2, ind_w - self.ind['step1']+self.ind['w']/2)),
							#(self.cap['w']/2+self.cap['bottom_to_bottom_clear']+self.cap['via_size']+self.cap['via_clear']*2, 0)),
							self.ind['w'],
							gdsii_path = True,
							layer = self.ind['layer'])
		path.translate( 0, -self.ind['cpw_dist']-ind_w )
		cell.add(path)
		name = "Meander_SiO2_lumped_res"
		meander = Meander(self.lib, name)
		meander.layer = self.ind['layer']
		meander.w = self.ind['w']
		meander.n = self.ind['n']
		meander.half_period = self.ind['step']
		meander.span = self.ind['l'] - self.ind['step']
		meander.kind = 2
		if name not in self.lib.cells.keys():
			meander.draw()
		else:
			meander.cell = self.lib.cells[name]
		meander_inst = meander.place( cell, path.points[-1], -pi/2, port = 1)
		origin = meander_inst.ports[0]['point']
		path = gdspy.FlexPath( (origin, 
								origin - array((0, self.ind['step']-self.ind['w']/2))),
								self.ind['w'],
								gdsii_path = True,
								layer = self.ind['layer'])
		origin -= array((0, self.ind['step']-self.ind['w']/2))
		path.segment( (self.cap['l']/2+self.cap['bottom_to_bottom_clear']+self.cap['via_size']+self.cap['via_clear']*2, origin[1]) )						
		cell.add(path)
		#Cap bottom electrode
		rect = gdspy.Rectangle( (-self.cap['l']/2, self.ind['w']/2 ),
						(self.cap['l']/2, -self.cap['w']+self.ind['w']/2 ),	
							layer = self.cap['bottom_layer'])
		rect.translate(0, -self.ind['cpw_dist']-ind_w)				
		cell.add(rect)
		#Cap top conductor
		rect = gdspy.Rectangle( (-self.cap['l']/2, self.ind['w']/2   ),
						(self.cap['l']/2 + self.cap['bottom_to_bottom_clear'] + 
						self.cap['via_clear']*2 + self.cap['via_size'], -self.cap['w']+self.ind['w']/2 ),	
							layer = self.cap['top_cond_layer'])
		rect.translate(0, -self.ind['cpw_dist']-ind_w)				
		cell.add(rect)
		#Conecting via
		rect = gdspy.Rectangle( (-self.cap['via_size']/2, -self.cap['via_size']/2), 
								(self.cap['via_size']/2, self.cap['via_size']/2),
								layer = self.cap['via_layer'])
		rect.translate( self.cap['l']/2+self.cap['via_clear']+self.cap['via_size']/2+self.cap['bottom_to_bottom_clear'],
						-self.ind['cpw_dist']-ind_w+self.ind['w']/2-
						self.cap['via_clear']-self.cap['via_size']/2)
		cell.add(rect)
		#Conecting via bottom pad
		rect = gdspy.Rectangle( (-self.cap['via_size']/2-self.cap['via_clear'], -self.cap['via_size']/2-self.cap['via_clear']), 
								(self.cap['via_size']/2+self.cap['via_clear'], self.cap['via_size']/2+self.cap['via_clear']),
								layer = self.cap['bottom_layer'])
		rect.translate( self.cap['l']/2+self.cap['via_clear']+self.cap['via_size']/2+self.cap['bottom_to_bottom_clear'],
						-self.ind['cpw_dist']-ind_w+self.ind['w']/2-
						self.cap['via_clear']-self.cap['via_size']/2)
		cell.add(rect)
		self.cell = cell
		#Ports coordinates
		self.ports[1] = array((-cell_size[0]/2,0))
		self.ports[2] = array((cell_size[0]/2,0))
		
	def place(self, top_cell, origin, direction = 0, port = 1):
		origon = array(origin)
		bonding_box = self.cell.get_bounding_box()
		l = bonding_box[1,0]-bonding_box[0,0]
		t = array((l*cos(direction), l*sin(direction)))
		place_origin = origin+t/2
		if port==1:
			rotation = direction
			top_cell.add(gdspy.CellReference(self.cell, place_origin, degrees(rotation)))
			p1  = origin
			p2  = origin + t
		elif port ==2:
			rotation = direction+pi
			top_cell.add(gdspy.CellReference(self.cell, place_origin, degrees(rotation)))
			p1 = origin + t
			p2 = origin
		else:
			Raise(ValueError)
		#Keepout polygon
		bb = self.cell.get_bounding_box()
		keepout_polygon = gdspy.Rectangle( bb[0], bb[1] )
		keepout_polygon.rotate(rotation)
		keepout_polygon.translate(place_origin[0], place_origin[1])
		return {'p1':p1,'p2':p2, 'keepout':keepout_polygon}

class CNEMultilayerPad(Component):
	def __init__(self, lib, cell_name):
		Component.__init__(self, lib, cell_name)
		self.l = 300
		self.w = 300
		self.via_size = 2
		self.via_spacing = 4
		self.metal_layers = {'M1':10, 'M2':20, 'M3':30, 'M4':40}
		self.via_layers = {'V1':11, 'V2':21, 'V3':31}

	def draw(self):
		#Via elementary cell
		checksum = zlib.crc32( bytes([x for x in self.via_layers.values()]+[self.via_size,self.via_spacing]))
		name = "Vias_for_pad_{:X}".format(checksum)
		if name not in self.lib.cells.keys():
			via_unit_cell = gdspy.Cell(name)
			self.lib.add( via_unit_cell )
			via_unit_cell.add(gdspy.Rectangle((-self.via_size/2,-self.via_size/2 ),(self.via_size/2, self.via_size/2 ), layer = self.via_layers['V2'] ))
			rect = gdspy.Rectangle((-self.via_size/2,-self.via_size/2 ),(self.via_size/2, self.via_size/2 ), layer = self.via_layers['V1'] )
			via_unit_cell.add( rect.translate(-self.via_spacing, -self.via_spacing) )
			rect = gdspy.Rectangle((-self.via_size/2,-self.via_size/2 ),(self.via_size/2, self.via_size/2 ), layer = self.via_layers['V3'] )
			via_unit_cell.add( rect.translate(-self.via_spacing, -self.via_spacing) )	
		else:	
			via_unit_cell = self.lib.cells[name]
	
		for layer in self.metal_layers.keys():
			path = gdspy.Path(self.w)
			path.segment(self.l, '+x', layer = self.metal_layers[layer])
			self.cell.add(path)
			
		nx = int((self.l-self.via_spacing*2)/self.via_spacing)
		nx -= nx%2
		ny = int((self.w-self.via_spacing*2)/self.via_spacing)
		ny -= ny%2
		
		origin = ( (self.l-(nx-1)*self.via_spacing)/2+self.via_spacing, (self.w-(ny-1)*self.via_spacing)/2-self.w/2+self.via_spacing ) 
		self.cell.add( gdspy.CellArray(via_unit_cell, int(nx/2), int(ny/2), (self.via_spacing*2,self.via_spacing*2) , origin ) )
		#Port directions are pointed inside
		self.p_coords = array( ((0,0),(self.l,0)) )
		self.p_dirs = array( (0.,pi) )