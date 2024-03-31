from numpy import *
import gdspy
import copy as cpy
from chip_draw.components.base_classes import *
		
class CPWPad(Component):
	def __init__(self, lib, cell_name):
		Component.__init__(self, lib, cell_name)
		self.w_cpw = 10
		self.g_cpw = 10
		self.w_pad = 200
		self.l_pad = 300
		self.l_taper = 200
		self.g_pad = 50
		self.pad_layer = 0
		self.gnd_layer = 1
		self.cpw_layer = 2
		self.via_layer = 3
		self.via_size = 4
		self.via_clear = 2
		self.w_gnd = 300
		
	def draw(self):
		
		#Pad and taper
		path = gdspy.Path(self.w_pad, (0.,0.))
		path.segment(self.l_pad, layer = self.pad_layer)
		path.segment(self.l_taper, direction = '+x', final_width = self.w_cpw, layer = self.pad_layer)	
		self.cell.add(path)
		#CPW
		path = gdspy.Path(self.w_cpw, (self.l_pad+self.l_taper-self.via_size-self.via_clear*2,0.))
		path.segment(self.via_size+self.via_clear*2, layer = self.cpw_layer)
		self.cell.add(path)
		#GND
		poly = gdspy.Polygon( ((0, self.w_pad/2+self.g_pad), 
						(0, self.w_pad/2+self.g_pad+self.w_gnd), 
						(self.l_pad+self.l_taper, self.w_pad/2+self.g_pad+self.w_gnd), 
						(self.l_pad+self.l_taper, self.w_cpw/2+self.g_cpw),
						(self.l_pad, self.w_pad/2+self.g_pad), 
						(0, self.w_pad/2+self.g_pad)), 
						layer=self.gnd_layer)
		self.cell.add(poly)
		self.cell.add(cpy.copy(poly).mirror((1,0)))	
		#Vias
		n_vias = int((self.w_cpw-self.via_clear)/(self.via_size+self.via_clear))
		origin = array((self.l_pad+self.l_taper-self.via_clear-self.via_size/2, ((self.via_size+self.via_clear)*(n_vias-1))/2 ))
		for i in range(n_vias):
			rect = gdspy.Rectangle( origin+array((-self.via_size/2,-self.via_size/2)), origin+array((self.via_size/2,self.via_size/2)) , layer = self.via_layer)
			self.cell.add(rect)
			origin-=array((0,self.via_clear+self.via_size))
			
		#Ports
		bonding_box = self.cell.get_bounding_box()
		self.p_coords = array(((0,0),(bonding_box[1,0]-bonding_box[0,0],0)))
		self.p_dirs = array((0,pi)) 
		
		#Keepout
		keepout_polygon = gdspy.Rectangle( bb[0], bb[1] )
		keepout_polygon.rotate(rotation)
		keepout_polygon.translate(origin[0], origin[1])
		self.keepout = [keepout_polygon,]	
		
class CPW():
	def __init__(self, point, direction, width, gap):
		self.layer = 0
		self.keepout_layer = 0
		self.w = width
		self.g = gap
		self.point = array(point, dtype = float)
		self.direction = float(direction)
		self.length = 0.
		self.polygons = []
		self.keepout_polygons = []
		self.pad = None
		
	def segment(self, l):
		l = float(l)
		w = self.w
		g = self.g
		v = array( ((0.,w/2.) , (l,w/2.) , (l,-w/2) , (0.,-w/2)) )
		p = gdspy.Polygon(v, layer = self.layer)
		p.rotate(self.direction)
		p.translate( self.point[0], self.point[1] )
		self.polygons += [p,]
		self.length += l
		
		v = array( ((0.,w/2.+g) , (l,w/2.+g) , (l,-w/2-g) , (0.,-w/2-g)) )
		p = gdspy.Polygon(v, layer = self.keepout_layer)
		p.rotate(self.direction)
		p.translate( self.point[0], self.point[1] )
		self.keepout_polygons += [p,]
		
		self.point += array( ( l*cos(self.direction) , l*sin(self.direction) ) )
	
	def place(self, top_cell):	
		for p in self.polygons:
			top_cell.add(p)
		