from numpy import *
import gdspy
from numpy.linalg import *
import scipy.optimize as so

def meander_optimize(p1, p2, span, l, rotation = 0., type = 'odd'):
	#l - total line lenght
	#p1 p2 - start and end points
	p1 = array(p1)
	p2 = array(p2)
	
	v = p2 - p1
	start_v = array([cos(radians(rotation)), sin(radians(rotation))])
	
	#Additional lenght, appears if p1,p2 are not on the meander axis
	l_add = vdot(v, start_v)
	
	#Points on the meander axis
	p1_cent = p1 + start_v * l_add/2.
	p2_cent = p2 - start_v * l_add/2.

	#Meander lenght
	m_l = norm(p2_cent - p1_cent)

	#n is odd or even by type
	if(type=='odd'): n = 1
	elif(type=='even'): n = 2
	
	s = span + 1.
	while(s > span):
		s = (l - l_add - m_l*(pi/2.-1.) )/( float(n) + 1. )
		n += 2
		
	if s<=0:
		raise Exception("Distance between points p1 and p2 is too short or meander length is too long")
		
	n -= 2
	half_step = m_l/(n+1.)

	#Lenght of first and last straight segments
	l_fl = (s - half_step + l_add)/2.
	if l_fl<0:
		raise Exception("Distance between points p1 and p2 is too long or meander length is too short")
	#n - number of straight segments
	#print l_fl*2. + n*(s-half_step) + (n+1.)*pi*half_step/2.
	#s - optimized span	
	return n, s, half_step, l_fl
		
def meander( w, p1, p2, l, span, rotation = 0., type = 'odd'):
	ang = rotation
	p1 = array(p1)
	p2 = array(p2)
	
	n, span_opt, half_step, l_fl = meander_optimize( p1, p2, span, l, rotation = ang, type = type)
	l_fl = abs(l_fl)
	#Bend radius
	print (n, half_step)
	r = half_step/2.
	print(r)
	#Straight segment lenght
	seg_l = span_opt - half_step
	#First straight segment
	
	dir_v = array([cos(radians(rotation)), sin(radians(rotation)), 0] )
	if cross( dir_v, append( p2 - p1, 0.) )[-1] < 0:
		#path = gdspy.FlexPath([(0.,0.) ,(0., l_fl)], w)
		path = gdspy.Path( w)
		path.segment(l_fl, direction= 'y')
		arc_angle = -pi/2
		extra_rot = -90.
		ang = pi
	else:
		#path = gdspy.FlexPath([(0.,0.) ,(0., -l_fl) ], w)
		path = gdspy.Path( w)
		path.segment(l_fl, direction= '-y')
		arc_angle = pi/2.
		extra_rot = 90.
		ang = -pi
	#path.turn(r, arc_angle)
	
	path.arc(r, ang, ang+arc_angle)
	ang+=arc_angle
	
	for i in range( int(n) ):
		#1/4 arc
		##path.turn(r, arc_angle)
		path.arc(r, ang, ang+arc_angle)
		#ang+=arc_angle
		#straight segment
		#path.segment( (0, seg_l*sign(arc_angle) ), relative = True)
		path.segment(seg_l, direction= sign(arc_angle)*pi/2)
		arc_angle = -arc_angle
		ang = -pi*sign(arc_angle)
		#1/4 arc
		#path.turn(r, arc_angle)
		path.arc(r, ang, ang+arc_angle)
		ang+=arc_angle
		
	path.turn(r, arc_angle)
	#last straight segment
	#path.segment( (0, l_fl * sign(arc_angle)), relative = True )
	path.segment(l_fl, direction= sign(arc_angle)*pi/2)
	
	path.rotate(radians(rotation+extra_rot))
	path.translate(p1[0], p1[1])
	
	return path
	
def slightly_bended_microstrip(w, p1, p2, L, type = 'left'):
	p1 = array(p1)
	p2 = array(p2)
	
	dir_v = p2-p1
	
	l = norm(dir_v)
	
	def func(x):
		return sin(x) - x*l/L
		
	phi = so.newton(func, pi/2 )
	
	if phi>pi/2:
		raise Exception("Required length L is too big")
	
	path = gdspy.FlexPath([(0.,0.),], w)
	
	r = L/(4*phi)
	if type == 'right':
		path.arc(r, pi/2, pi/2-phi)
		path.turn(r,2*phi)
		path.turn(r,-phi)
	elif type == 'left':	
		path.arc(r, -pi/2, -pi/2+phi)
		path.turn(r,-2*phi)
		path.turn(r,phi)
	else:
		raise ValueError()
		
	path.rotate( angle(dir_v[0]+1.j*dir_v[1]) )
	path.translate(p1[0], p1[1])
	
	return path

class Modulation():
	def __init__(self):
		self.default_w = 1.5
		self.period = 6
	#Every 3	
	def mod_func(self, n):
		if int(n)%3 == 0:
			w = 10.
			l = 3.
		else:	
			w = 5.
			l = 3.
		return(w,l) 
	
class ModulatedPath():

	def __init__(self, mod, point, direction):
		self.point = array(point)
		self.direction = direction
		self.length = 0.
		#Modulation class instance, describing how to modulate the path
		self.mod = mod
		#Global modulation switch, works via logical and with function parameter "modulation"
		self.modulation = True
		
		self.polygons = []
		#Widenings drawing style
		#tilt or turn
		self.mode = 'tilt'
		#Start flag for tilted segment
		self.start = False
		#End flag for tilted segment
		self.end = False
		
		
	def _modulated_segment(self, draw_func, length):
		initial_length = self.length
		past_periods = int(self.length/self.mod.period)
		mod_points = int((self.length+length)/self.mod.period)-past_periods
		
		w,l = self.mod.mod_func( past_periods+1 )
		w_pre,l_pre = self.mod.mod_func( past_periods )
		
		if mod_points:
			l_start = (past_periods+1) * self.mod.period - self.length
			if l_start > self.mod.period - l_pre/2.:
				#End of previous modulated segment
				l_segm = l_pre/2. - (self.length - past_periods * self.mod.period)
				self.start = True
				draw_func( l_segm, w_pre )
				self.start = False
				l_segm = self.mod.period - l/2. - l_pre/2.
			elif l_start < l/2.:
				l_segm = l/2. + l_start
				self.start = True
				draw_func( l_segm, w )
				self.start = False
				l_segm = 0.
			else:	
				l_segm = l_start - l/2.	
			
			if l_segm:	
				draw_func( l_segm , self.mod.default_w)
				l_left = initial_length + length - self.length
				if l_left<l:
					draw_func( l_left,w )
					return
				else:	
					draw_func( l,w )
				
			if  mod_points > 1:
				for i in range(1, mod_points-1):
					l_pre = l
					w,l = self.mod.mod_func( past_periods+i+1 )
					
					l_segm = self.mod.period - l/2. - l_pre/2.
					
					draw_func( l_segm, self.mod.default_w )
					draw_func( l, w )
			
				l_pre = l
				w,l = self.mod.mod_func( past_periods+mod_points )
				w_next,l_next = self.mod.mod_func( past_periods+mod_points+1 )
				l_segm = self.mod.period - l/2. - l_pre/2.		
				draw_func( l_segm, self.mod.default_w )
			
				l_left = initial_length + length - self.length
				if l_left<0.: print('l_left<0 ', mod_points)
				
				if l_left <= l:
					self.end = True
					draw_func(l_left, w)
					self.end = False
				else:
					draw_func(l, w)
					if l_left <= self.mod.period:
						draw_func( l_left - l , self.mod.default_w)
					else:
						draw_func( self.mod.period - l/2. - l_next/2., self.mod.default_w )
						self.end = True
						draw_func( initial_length + length - self.length, w_next )
						self.end = False
			else:
				w_next,l_next = self.mod.mod_func( past_periods+mod_points+1 )
				l_left = initial_length + length - self.length
				l_default = self.mod.period - l/2. - l_next/2.
				if l_left <= l_default:
					draw_func( l_left, self.mod.default_w)
				else:
					draw_func( l_default, self.mod.default_w)
					self.end = True
					draw_func( l_left - l_default, w_next )
					self.end = False
		else:
			#0 modulation points inside interval
			l_left_pre = l_pre/2. - self.length + past_periods*self.mod.period
			if l_left_pre >0:
				if  l_left_pre < length:
					self.start = True
					draw_func( l_left_pre , w_pre )
					self.start = False
				else:
					draw_func( length , w_pre )
					return
			else:	
				l_left_next = (past_periods+1)*self.mod.period - self.length
				if l_left_next < l/2.:
					self.start = True
					draw_func( length , w )
					self.start = False
					return
			
			l_left = initial_length + length - self.length
			l_left_next = l/2. - (past_periods+1)*self.mod.period + initial_length + length
			if l_left_next > 0:
				if l_left > l_left_next:
					draw_func( l_left - l_left_next, self.mod.default_w)
				if l_left_next < lenght:
					self.end = True
					draw_func( l_left_next, w )
					self.end = False
				else:
					draw_func( lenght, w )
			else:
				draw_func( l_left, self.mod.default_w)
	
	def _straight_segment(self, l, w):
		v = array( ((0.,w/2.) , (l,w/2.) , (l,-w/2) , (0.,-w/2)) )
		p = gdspy.Polygon(v)
		p.rotate(self.direction)
		p.translate( self.point[0], self.point[1] )
		self.polygons += [p,]
		self.length += l
		self.point += array( ( l*cos(self.direction) , l*sin(self.direction) ) )
		
	def _turn(self, radius, ang, w, fake_draw = False):
		center = array( (0., sign(ang)*radius) )
		inner_radius = radius - w/2.
		outer_radius = radius + w/2.
		arc = gdspy.Round(center, outer_radius, inner_radius, initial_angle=-pi/2*sign(ang), final_angle= -pi/2*sign(ang) + ang)
		arc.rotate(self.direction)
		arc.translate( self.point[0], self.point[1] )
		if not fake_draw:
			self.polygons += [arc,]
			self.length += abs(ang)*radius
			shift_l = abs(2.*radius*sin(ang/2.))
			shift_ang = ang/2. + self.direction
			self.direction += ang
			self.point += array( (shift_l*cos(shift_ang), shift_l*sin(shift_ang)) )
		return arc
		
	def _tilted_segment(self, radius, ang, w):
		
		if w != self.mod.default_w:
			l = abs(ang)*radius
			if self.start:
				point = self.point + array( (l/2.*cos(self.direction), l/2.*sin(self.direction)) )
				direction = self.direction
			elif self.end:
				direction = self.direction + ang
				shift_l = abs(2.*radius*sin(ang/2.))
				shift_ang = ang/2. + self.direction
				point = self.point + array( (shift_l*cos(shift_ang), shift_l*sin(shift_ang)) ) - array( (l/2.*cos(direction), l/2.*sin(direction)) )
			else:
				shift_l = abs(2.*radius*sin(ang/4.))
				shift_ang = ang/4. + self.direction
				point = self.point + array( (shift_l*cos(shift_ang), shift_l*sin(shift_ang)) )
				direction = self.direction + ang/2.
			v = array( ((-l/2.,-w/2.) , (-l/2.,w/2.) , (l/2.,w/2) , (l/2.,-w/2)) )
			p = gdspy.Polygon(v)
			p.rotate(direction)
			p.translate( point[0], point[1] )
			self.polygons += [p,]
		
		self.length += abs(ang*radius)
		shift_l = abs(2.*radius*sin(ang/2.))
		shift_ang = ang/2. + self.direction
		self.direction += ang
		self.point += array( (shift_l*cos(shift_ang), shift_l*sin(shift_ang)) )
	
	def segment(self, length, direction = None, modulation = True, width = None ):
		if length:
			if direction is not None:
				self.direction = direction
			if self.modulation and modulation:	
				self._modulated_segment(self._straight_segment, length)
			else:
				if width is None:
					width = self.mod.default_w
				self._straight_segment(length, width)
				
			
	def turn(self, radius, ang , modulation = True, width = None ):
		if ang:
			if self.modulation and modulation:
				if self.mode == 'turn':
					draw_func = lambda l, w: self._turn(radius, sign(ang)*l/radius, w)
					self._modulated_segment(draw_func, radius * abs(ang) )
				elif self.mode == 'tilt':
					n_poly_init = len(self.polygons)
					arc = self._turn( radius, ang, self.mod.default_w, fake_draw = True )
					draw_func = lambda l, w: self._tilted_segment( radius,  sign(ang)*l/radius, w)
					self._modulated_segment(draw_func, radius * abs(ang) )
					n_poly = len(self.polygons) - n_poly_init
					bool_res = gdspy.boolean(self.polygons[-n_poly::], arc, 'or')
					del self.polygons[-n_poly::]
					self.polygons += [bool_res,]
			else:
				if width is None:
					width = self.mod.default_w
				self._turn(radius, ang, width)
				
def square_spiral(path, p2, size, n, n_cut = 0, radius = 1):
	#Radius is normalized by s and active only if n_cut > 0
	s = size/2./n #Spacing between nearest lines
	n = int(n)
	n_cut = int(n_cut)
	radius = int(radius)
	
	if size<=0 or n<=0 or n_cut<0 or radius<=0:
		raise ValueError()
	
	p2 = array(p2)
	dir_v = p2 - path.point
	l = norm(dir_v)
	
	if n_cut:
		#Use any radius
		bend_r = s/2.*radius
	else:
		#Radius is fixed
		bend_r = s/2.
	
	if l < size + bend_r*2:
		raise ValueError("Spiral won't fit between start point and p2!")
		
	path.direction = angle(dir_v[0]+1.j*dir_v[1])	
	path.segment(l/2. - size/2. - bend_r)
	path.turn(bend_r, -pi/2)
	
	for i in range(n-n_cut):
		j = 2*i+1
		if i==0:
			path.segment( (size - (j-1)*s) /2 -bend_r*2.)
		else:	
			path.segment( (size - (j-1)*s) /2 -bend_r)
		path.turn(bend_r, pi/2)
		path.segment( size - bend_r*2 - s*j)
		path.turn(bend_r, pi/2)
		path.segment((size - (j-1)*s)/2 - bend_r)
	if n_cut:
		bend_r_center = n_cut*s/2.
		path.turn(bend_r_center, pi)
		path.turn(bend_r_center, -pi)
	for i in range(n_cut,n):
		j = 2*(n-i-1)+1
		path.segment( (size - (j-1)*s) /2 -bend_r)
		path.turn(bend_r, -pi/2)
		path.segment( size - bend_r*2 - s*j)
		path.turn(bend_r, -pi/2)
		if i==n-1:
			path.segment( (size - (j-1)*s) /2 -bend_r*2.)
		else:	
			path.segment( (size - (j-1)*s) /2 -bend_r)
	path.turn(bend_r, pi/2)		
	path.segment( l/2. - size/2. - bend_r)

def corner_mark(l, w, layer = 0, name = 'CORNER_MARK'):
	corner_mark_cell = gdspy.Cell(name)
	points = [ 	(l, 0),
				(0, 0),
				(0, l),
				(w, l),
				(w, w),
				(l, w)]
	poly = gdspy.Polygon(points, layer = layer)						
	corner_mark_cell.add(poly)	
	return corner_mark_cell	
	
def place_corner_marks(target_cell, corner_mark_cell, chip_size, chip_center = (0.,0.)):
	chip_center = array(chip_center)
	origins = array( (	(-chip_size[0]/2., -chip_size[1]/2.), 
						(chip_size[0]/2., -chip_size[1]/2.),
						(chip_size[0]/2., chip_size[1]/2.),
						(-chip_size[0]/2., chip_size[1]/2.) )) + chip_center
	rotations = [0, 90, 180, 270]
	for origin, rotation in zip(origins, rotations):
		ref = gdspy.CellReference(corner_mark_cell, origin, rotation = rotation )
		target_cell.add(ref)
		
class TestBridge():
	def __init__(self,lib, cell_name = 'TEST_BRIDGE', layer = 0 ):
		self.cell_name = cell_name
		self.params = {'l':200 , 'w': 8,
						'pad_size': (300.,300.)}
		self.lib = lib
		self.layer = layer
		
	def draw(self):		
		cell = gdspy.Cell( self.cell_name )
		self.lib.add(cell)
		path = gdspy.Path(self.params['pad_size'][1], initial_point=(-self.params['l']/2-self.params['pad_size'][0], 0))
		path.segment(self.params['pad_size'][0], layer = self.layer)
		path.w = self.params['w']/2.
		path.segment(self.params['l'], layer = self.layer)
		path.w = self.params['pad_size'][1]/2.
		path.segment( self.params['pad_size'][0], layer = self.layer)
		cell.add(path)
		return cell

class MiteredPath():
	def __init__(self, point, direction, width, a):
		self.a = a
		self.w = width
		self.point = array(point, dtype = float)
		self.direction = float(direction)
		self.length = 0.
		self.polygons = []
		
	def segment(self, l):
		l = float(l)
		w = self.w
		v = array( ((0.,w/2.) , (l,w/2.) , (l,-w/2) , (0.,-w/2)) )
		p = gdspy.Polygon(v)
		p.rotate(self.direction)
		p.translate( self.point[0], self.point[1] )
		self.polygons += [p,]
		self.length += l
		self.point += array( ( l*cos(self.direction) , l*sin(self.direction) ) )
	
	def bend(self, direction):
		if direction not in ['r','l']:
			raise ValueError()
		w = self.w
		a = self.a
		v = array(( (0.,w/2.) , (a, w/2.) , (a, w/2+a) , (w+a, w/2+a), (0.,-w/2.)  ))
		p = gdspy.Polygon(v)
		if direction == 'r':
			p.mirror((1,0))
			ang =  -pi/2
		else:
			ang = pi/2
		p.rotate(self.direction)
		p.translate( self.point[0], self.point[1] )
		self.length += self.w/2.
		shift_l = sqrt(2)*(w/2+a)
		shift_ang = ang/2. + self.direction
		self.direction += ang
		self.point += array( (shift_l*cos(shift_ang), shift_l*sin(shift_ang)) )
		self.polygons += [p,]
		
def miter(w,h):
	D = w* sqrt(2)
	X= D* (0.52 + 0.65*exp(-1.35 * (w/h)))
	A = ( X - D/2) * sqrt(2)
	return A