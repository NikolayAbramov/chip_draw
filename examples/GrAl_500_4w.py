import gdspy
from numpy import * 
import copy
import zlib
from chip_draw.old.chip_draw import *

class SpiralTwpaChip():

	def __init__(self, lib, cell, mod): 
		self.lib = lib
		self.cell = cell
		self.chip_params = {	'size':array([5000., 5000.]),
								'border_clear': 100.,
								'corner_marks': True}					
		self.corner_mark_params = {'l':200, 'w':50, 'layer': 'top_metal_cuts'}
		self.corner_mark_cell = None
		self.spiral_params = {		'n':17,
									'n_cut':3,
									'w':3000., 		#Spiral_width
									'r':4,			#Bend radius, int
									'method':'turn'} #Widenings drawing method
		self.pad_params = {	'size':(250., 200.), 
							'top_metal_clear': 40., 
							'dielectric_top_metal_clear': 20.,
							'top_metal_cover_w': 40.,
							'top_metal_cover_overlap': 10.  }
		self.layers = {'NbN':0,'dielectric_cuts':1, 'top_metal_cuts': 2}
		
		self.mod = mod #Path modulation
		
		self.test_structures = [	{ 	'cell': None,
										'origin': (self.chip_params['size'][0]/2.-1000, self.chip_params['size'][1]/2.-400),
										'rotation': 0.},
									{ 	'cell':None,
										'origin': (-self.chip_params['size'][0]/2.+1000, self.chip_params['size'][1]/2.-400),
										'rotation': 0.}]	
		self.text_descr = {	'text':'None',
							'origin':(-self.chip_params['size'][0]/2.+1000, -self.chip_params['size'][1]/2.+400),
							'size': 120.}
		
######################################################################
	def _draw_pad_cutouts(self, origin, direction):
		points = [	(0., 0. ),
					(0., self.pad_params['size'][1]/2.+self.pad_params['top_metal_clear'] ),
					(self.pad_params['size'][0]+self.chip_params['border_clear']+self.pad_params['top_metal_clear'], self.pad_params['size'][1]/2.+self.pad_params['top_metal_clear']),
					(self.pad_params['size'][0]+self.chip_params['border_clear']+self.pad_params['top_metal_clear'], self.pad_params['top_metal_cover_w']/2.),
					(self.pad_params['size'][0]+self.chip_params['border_clear']-self.pad_params['top_metal_cover_overlap'], self.pad_params['top_metal_cover_w']/2.),
					(self.pad_params['size'][0]+self.chip_params['border_clear']-self.pad_params['top_metal_cover_overlap'], 0.)]
		poly = gdspy.Polygon(points, layer = self.layers['top_metal_cuts'])
		poly = gdspy.boolean(poly, gdspy.copy(poly).mirror((1.,0.)), 'or', layer = self.layers['top_metal_cuts'])
		poly.rotate(direction)
		poly.translate(origin[0], origin[1])
		self.cell.add( poly )
		poly = gdspy.offset(poly, -self.pad_params['dielectric_top_metal_clear'], layer = self.layers['dielectric_cuts'])
		self.cell.add(poly)
		return poly
		
	def draw(self):	
		#Corner marks
		if self.chip_params['corner_marks']:
			if self.corner_mark_cell is None:
				name = self.cell.name+'_CORNER_MARK'
				layer = self.layers[ self.corner_mark_params['layer'] ]
				corner_mark_cell = corner_mark(self.corner_mark_params['l'], self.corner_mark_params['w'],layer = layer, name = name)
				self.lib.add(corner_mark_cell)
			else:
				corner_mark_cell = self.corner_mark
			place_corner_marks( self.cell, corner_mark_cell, self.chip_params['size'] )
		
		path = ModulatedPath(self.mod, (-self.chip_params['size'][0]/2.+self.chip_params['border_clear'],0.), 0)
		path.mode = self.spiral_params['method']
		
		#Left pad
		path.segment(self.pad_params['size'][0], modulation = False, width = self.pad_params['size'][1])
			
		origin = array( (-self.chip_params['size'][0]/2., 0.) )
		self._draw_pad_cutouts(origin, 0.)
		
		#Spiral
		final_point = (self.chip_params['size'][0]/2.-self.chip_params['border_clear']-self.pad_params['size'][0], 0.)
		square_spiral(path, final_point, self.spiral_params['w'], self.spiral_params['n'], n_cut = self.spiral_params['n_cut'], radius = self.spiral_params['r'])
		
		#Right pad
		path.segment(self.pad_params['size'][0], modulation = False, width = self.pad_params['size'][1])
		origin = array( (self.chip_params['size'][0]/2., 0.) )
		self._draw_pad_cutouts(origin, pi)
		
		for p in path.polygons:
			self.cell.add(p)
			
		for test_str in self.test_structures:
			if test_str['cell'] is not None:
				ref = gdspy.CellReference(test_str['cell'] , test_str['origin'], rotation = test_str['rotation'] )
				self.cell.add(ref)
				print(test_str['cell'].name)
		
		polygons = self.cell.get_polygons()
		polygons_flat = [item for sublist in polygons for subsublist in sublist for item in subsublist]
		b = bytes(str(polygons_flat), encoding = 'utf-8')
		checksum = zlib.crc32(b)
		self.cell.add( gdspy.Text("{:s}\n{:X}".format(self.text_descr['text'], checksum ), self.text_descr['size'], position = self.text_descr['origin'], layer = self.layers['top_metal_cuts']) )
		
		return path.length

class Modulation3w():
	def __init__(self):
		self.default_w = 8
		self.period = 27.
	#Every 3	
	def mod_func(self, n):
		if int(n)%3 == 0:
			w = self.default_w/0.57
			l = self.period*0.185
		else:	
			w = self.default_w/0.666
			l = self.period*0.185
		return(w,l)

class TestBridge3L(TestBridge):
	def __init__(self, *args, **kwargs):
		TestBridge.__init__(self, *args, **kwargs)
		self.layer_clear = {'top_metal_clear': 40., 
							'dielectric_top_metal_clear': 20.}
		self.layers = {'NbN':0,'dielectric_cuts':1, 'top_metal_cuts': 2}
		self.layer = self.layers['NbN']
	def draw(self):
		cell = TestBridge.draw(self)
		bounding_box = cell.get_bounding_box()
		top_cutout = gdspy.Rectangle(bounding_box[0],bounding_box[1])
		top_cutout = gdspy.offset(top_cutout, self.layer_clear['top_metal_clear'], layer=self.layers['top_metal_cuts'])
		cell.add(top_cutout)
		dielectric_cutout = gdspy.offset(gdspy.copy(top_cutout), -self.layer_clear['dielectric_top_metal_clear'], layer=self.layers['dielectric_cuts'])
		cell.add(dielectric_cutout)
		return cell
		
class TestCap():
	def __init__(self, lib, cell_name = 'TEST_CAP'):
		self.layers = {'NbN':0,'dielectric_cuts':1, 'top_metal_cuts': 2}
		self.params = {'l':250. ,'l_pad':300., 'w_bot': 290., 'w_top': 250.}
		self.layer_clear = {'top_metal_clear': 40., 'dielectric_top_metal_clear': 20.}
		self.cell_name = cell_name
		self.lib = lib
	def draw(self):
		cell = gdspy.Cell( self.cell_name )
		self.lib.add(cell)
		path = gdspy.Path(self.params['w_bot'], initial_point=(-self.params['l']/2.-self.params['l_pad'], 0))
		path.segment(self.params['l_pad']+self.params['l'], layer = self.layers['NbN'])
		cell.add(path)
		w = max( (self.params['w_bot'], self.params['w_top']) ) + self.layer_clear['top_metal_clear']*2.
		l = self.params['l']+self.params['l_pad']*2. + self.layer_clear['top_metal_clear']*2.
		top_cutout1 = gdspy.Rectangle( (-l/2.,-w/2.) , (l/2.,w/2.))
		top_cutout2 = gdspy.Rectangle( (-self.params['l']/2.,-self.params['w_top']/2.) , (self.params['l']/2.+self.params['l_pad'], self.params['w_top']/2.))
		top_cutout = gdspy.boolean( top_cutout1,top_cutout2, 'not' ,layer = self.layers['top_metal_cuts'])
		cell.add(top_cutout)
		w = max( (self.params['w_bot'], self.params['w_top']) ) + self.layer_clear['top_metal_clear']*2. - self.layer_clear['dielectric_top_metal_clear']*2.
		l = self.params['l']+self.params['l_pad']*2. + self.layer_clear['top_metal_clear']*2. - self.layer_clear['dielectric_top_metal_clear']*2.
		dielectric_cutout = gdspy.Rectangle( (-l/2.,-w/2.) , (-self.params['l']/2. - self.layer_clear['dielectric_top_metal_clear'],w/2.), layer = self.layers['dielectric_cuts'])
		cell.add(dielectric_cutout)
		return cell
		

fab_lib = gdspy.GdsLibrary('FAB', unit = 1e-6)
main = gdspy.Cell('MAIN')
fab_lib.add(main)
mod = Modulation3w()
test_bridge = TestBridge3L(fab_lib)
test_bridge.params['pad_size'] = (250, 250)
test_cell = test_bridge.draw()
test_cap_cell = TestCap(fab_lib).draw()

chip = SpiralTwpaChip(fab_lib, main, mod)
chip.text_descr['text'] = '3W'
chip.test_structures[0]['cell'] = test_cell
chip.test_structures[1]['cell'] = test_cap_cell
length = chip.draw()

print("Total length ",length/1e3, " mm")
gdspy.LayoutViewer(fab_lib)
fab_lib.write_gds('square_spiral_test.gds')
