from numpy import *
from numpy.linalg import *
import dxfwrite as dw
from dxfwrite import DXFEngine as dxf
import scipy.optimize as so
from matplotlib.pyplot import *
import copy as cpy

class cpw_style:
	def __init__(self, width = 50., gap = 25.):
		self.width = width #Central conductor
		self.gap = gap

class cpw_pad_style:
	def __init__(self, width = 200., lenght = 200., gap = 100., edge_gap = 100.):
		self.width = width
		self.gap = gap
		self.edge_gap = edge_gap
		self.lenght = lenght
		
#Functional cpw defined by pointwise w-g profile
#x - coordinate along cpw
#w - cpw widths
#g - cpw gaps
class fcpw_style:
	def __init__(self,x,w,g):
		self.x = asarray(x)
		self.w = asarray(w)
		self.g = asarray(g)
		self.lenght = 0.
		if ((len(x) != len(w)) or (len(x) != len(g))):
			raise ValueError

#All objects assumed to be closed polylines with bulge. We don't need other DXF entyties 			
class polyline:
	def __init__(self, vertexes, layer = '0', bulges = None ):
		self.layer = layer
		self.vertexes = array(vertexes)
		if bulges is not None:
			self.bulges = array(bulges)
		else: self.bulges = zeros(len(vertexes))
		
class entity:
	def __init__(self):
		self.polylines = []
		#self.origin = (0,0)
		#self.name = ''
		
	def add_polyline(self, polyline):
		self.polylines.append( polyline )
			

class project:
	def __init__(self, prj_filename):
		self.drw = dxf.drawing(prj_filename)
		self.layer = "0"
		self.entity = "0"
		self.lenght = 0. #Total lenghht drawn 
		#self.data = {self.layer:{'color':0, 'polylines':[]}}
		self.layers = {self.layer:{'color':0}}
		self.entities = {self.entity: entity()}
	
	def __rot_matrix(self, phi):
		return array([[cos(phi),-sin(phi)],[sin(phi),cos(phi)]])
	
	def __transform(self, vertexes, point, phi):
		A = self.__rot_matrix(phi)
		for vert in vertexes:
			for i in range(0,len(vert)):
				vert[i] = dot(A,vert[i]) + point
		return vertexes
		
	#Polar to cartesian
	def __pol_to_cart(self, r, phi):
		if hasattr(r,"__len__"):
			cart = vstack( ( r*cos(phi), r*sin(phi) ) ).T
		else:
			cart = array([r*cos(phi), r*sin(phi)])
		return cart
	
	def __mirror_x(self,vert):
		vert1 = copy(vert)
		vert1.T[1] = -1.*vert1.T[1]
		return vert1
	'''
	def __draw_polylines(self, vertexes):
		for vert in vertexes:
			pl = dxf.polyline( flags = dw.POLYLINE_CLOSED)
			for v in vert:
				pl.add_vertex(v, layer = self.layer, thickness = 0.)
			self.drw.add(pl)
		self.drw.save()
	'''	
	def __draw_polyline(self, vert, bulges = None):
		if not(self.layer in self.layers.keys()):
			raise Exception("Layer {:s} doesn't exist".format(self.layer))
		pl = polyline(vert, layer = self.layer, bulges = bulges)
		if not(self.entity in self.entities.keys()):
			raise Exception("Entity {:s} doesn't exist".format(self.entity))
		self.entities[self.entity].add_polyline(pl)
		return pl
		
	def	draw_polyline(self, pl):
		self.entities[self.entity].add_polyline(pl)
		
		#self.data[self.layer]['polylines'].append(pl)
	
		#Sick polyline point data acces
		#point_num = 0
		#axis = 0 #x
		#print pl.vertices[point_num]['location'].point[axis].value	, 	pl.vertices[point_num]['bulge']
		
		#self.drw.add(pl)
		
		#self.drw.save()
	#def set_units(self):
	 #   self.drw.header["$INSUNITS"]=8
	
	def new_layer(self, layer, color = 2):
		if not(layer in self.layers.keys()):
			self.layers[layer] = {'color':color}
		else:
			raise Warning( "Layer {:s} already exists".format(layer) )
		self.layer = layer

	def new_entity(self, name, obj = None):
		if not(name in self.entities.keys()):
			if obj is None:
				self.entities[name] = entity()
			else:
				self.entities[name] = obj
		else:
			raise Exception( "Entity {:s} already exists".format(name) )
		self.entity = name
		
	#Draw dxf and save	
	def draw(self):
		for layer in self.layers.keys(): 
			self.drw.add_layer(layer, color = self.layers[layer]['color'])
			
		for entity in self.entities.keys():	
			for pl in self.entities[entity].polylines:
				pl_dxf = dxf.polyline(flags = dw.POLYLINE_CLOSED)
				for v,b in zip(pl.vertexes, pl.bulges):
						pl_dxf.add_vertex(v, layer = pl.layer, bulge = b, thickness = 0.)
				self.drw.add(pl_dxf)	
		self.drw.save()
	
	def mirror_y(self, entity_name):
		mirror = cpy.deepcopy(self.entities[entity_name])
		#mirror = self.entities[entity_name]
		#print mirror
		for pl in mirror.polylines:
			pl.vertexes[...,0] = -pl.vertexes[...,0]
			pl.bulges = -pl.bulges
		return mirror
		
	def mirror_x(self, entity_name):
		mirror = cpy.deepcopy(self.entities[entity_name])
		#mirror = self.entities[entity_name]
		#print mirror
		for pl in mirror.polylines:
			pl.vertexes[...,1] = -pl.vertexes[...,1]
			pl.bulges = -pl.bulges
		return mirror
	
	#Mirror polyline	
	def pl_mirror_y(self, pl):
		mirror = cpy.deepcopy(pl)
		pl.vertexes[...,0] = -pl.vertexes[...,0]
		pl.bulges = -pl.bulges
		return mirror
		
	def pl_mirror_x(self, pl):
		mirror = cpy.deepcopy(pl)
		pl.vertexes[...,1] = -pl.vertexes[...,1]
		pl.bulges = -pl.bulges
		return mirror	
		
	#Draw centred rectangle	
	def rect(self,point, w, h, rotation = 0.):
		vert = [(-w/2.,-h/2.),(-w/2.,h/2.),(w/2.,h/2.),(w/2.,-h/2.)]
		self.__transform( (vert,), point, radians(rotation) )
		self.__draw_polyline(vert)
	#Draw arbitrary shape
	def shape(self, vert, bulges = None):
		return self.__draw_polyline(vert, bulges = bulges)
		
	#Draw straight cpw
	def cpw(self, point, lenght, rotation = 0., cpw_style = cpw_style()):
		width = cpw_style.width
		gap = cpw_style.gap
		point = array(point)
		
		vert1 = [(0., width/2.),(0., width/2.+gap),(lenght, width/2.+gap),(lenght, width/2.)]
		vert2 = self.__mirror_x(vert1)
		end = (lenght,0.)
		
		(vert1,vert2,[end]) = self.__transform( (vert1,vert2,[end,]), point, radians(rotation))
		self.__draw_polyline(vert1)
		self.__draw_polyline(vert2)
		
		self.lenght+=lenght
		return end
	
	def cpw_round(self, start, r, arc_angle = 180., rotation = 0., cpw_style = cpw_style()):
		width = cpw_style.width
		gap = cpw_style.gap
		start = array(start)
		phi = radians(arc_angle)
		A = self.__rot_matrix(phi)
		
		if arc_angle >= 0.:
			end = (0.,r) + dot( A, (0.,-r) )
			vert1 = [(0., width/2.),
			   (0., width/2.+gap),
			   (0.,r) + dot( A, (0.,-r+width/2.+gap) ),
			   (0.,r) + dot( A, (0.,-r+width/2.) )
			  ]
			vert2 = [(0., -width/2.),
			   (0., -width/2.-gap),
			   (0.,r) + dot( A, (0.,-r-width/2.-gap) ),
			   (0.,r) + dot( A, (0.,-r-width/2.) )
			  ]
		else:
			end = (0.,-r) + dot( A, (0.,r) )
			vert1 = [(0., width/2.),
					 (0., width/2.+gap),
					 (0.,-r) + dot( A, (0.,r+width/2.+gap) ),
					 (0.,-r) + dot( A, (0.,r+width/2.) )
					]
			vert2 = [(0., -width/2.),
					 (0., -width/2.-gap),
					 (0.,-r) + dot( A, (0.,r-width/2.-gap) ),
					 (0.,-r) + dot( A, (0.,r-width/2.) )
					]
			
		bulge = [0., tan(phi/4.), 0., -tan(phi/4.)] 

		(vert1,vert2,[end]) = self.__transform( (vert1,vert2, [end,] ), start, radians(rotation))
		self.__draw_polyline(vert1, bulges = bulge)
		self.__draw_polyline(vert2, bulges = bulge)
		'''
		pl1 = dxf.polyline(flags = dw.POLYLINE_CLOSED)
		pl2 = dxf.polyline(flags = dw.POLYLINE_CLOSED)

		A = self.__rot_matrix(radians(rotation))
		for v1, v2, b in zip(vert1, vert2, bulge):
			pl1.add_vertex(dot(A,v1)+start, bulge = b, layer = self.layer,thickness = 0.)
			pl2.add_vertex(dot(A,v2)+start, bulge = b, layer = self.layer,thickness = 0.)	   

		self.drw.add(pl2)
		self.drw.add(pl1)
		self.drw.save()
		self.lenght += r*pi/2.
		
		return dot(A,end) + start, rotation + arc_angle
		'''
		return end, rotation + arc_angle
		
	def cpw_taper(self, point, lenght, rotation = 0., cpw_style1 = cpw_style(), cpw_style2 = cpw_style()):
		w1 = cpw_style1.width
		g1 = cpw_style1.gap
		w2 = cpw_style2.width
		g2 = cpw_style2.gap
		
		vert1 = [(0.,w1/2.),(0.,w1/2.+g1),(lenght,w2/2.+g2),(lenght,w2/2.)]
		vert2 = self.__mirror_x(vert1) 
		end = (lenght, 0.)
		
		(vert1,vert2,[end]) = self.__transform( (vert1,vert2, [end,] ), point, radians(rotation))
		
		self.__draw_polyline(vert1)
		self.__draw_polyline(vert2)
		
		self.lenght += lenght
		return end
		
	def cpw_open(self, point, rotation = 0., cpw_style = cpw_style(), lenght = 0. ):
		point = array(point)
		
		if lenght == 0:
			w = cpw_style.gap
		else:
			w = lenght
		
		h =	cpw_style.gap*2. + cpw_style.width
			
		vert = [(0., -h/2.),(0., h/2.),(w, h/2.),(w, -h/2.)]
		
		self.__transform( (vert,), point, radians(rotation) )
		self.__draw_polylines( (vert,) )
		
	#Couplers
	
	#Through couplers
	def ind_coupler(self, point, lenght, rotation = 0.,  cpw_style1 = cpw_style(), cpw_style2 = cpw_style()):
		w1 = cpw_style1.width
		g1 = cpw_style1.gap
		w2 = cpw_style2.width
		g2 = cpw_style2.gap
		
		vert1 = [(0.,w1/2.),(0.,w1/2.+g1),(lenght,w1/2.+g1),(lenght,w1/2.)]
		vert2 = [(0.,w2/2.),(0.,w2/2.+g2),(lenght,w2/2.+g2),(lenght,w2/2.)]
		vert3 = self.__mirror_x(vert2)
		vert4 = self.__mirror_x(vert1)
		end = (lenght,0.)
		
		(vert1,vert2,vert3,vert4,[end]) = self.__transform( (vert1,vert2,vert3,vert4,[end]),
																 point, radians(rotation))
		self.__draw_polylines( (vert1,vert2,vert3,vert4) )
		self.lenght += lenght
		return end
	
	#Notch couplers	
	def coupled_cpw(self, point, l, w, rotation = 0, cpw_style1 = cpw_style(), cpw_style2 = cpw_style(), side = "right" ):
		#l - lenght
		#w - width of groung strip between cpw's
		#side - whe to draw coupled line
		
		w1 = cpw_style1.width
		g1 = cpw_style1.gap
		w2 = cpw_style2.width
		g2 = cpw_style2.gap
		
		#Through cpw
		point_out = self.cpw(point, l, rotation = rotation, cpw_style = cpw_style1)
		
		#Coupled cpw
		if side == 'right':
			ang = radians(rotation-90.)
		elif side == 'left':
			ang = radians(rotation+90.)
		
		point_coup2 = (w1/2.+g1 + w2/2.+g2 + w)*array( [cos( ang ), sin( ang )] )
		point_coup2 = add( point, point_coup2 )
		point_coup1 = self.cpw(point_coup2, l, rotation = rotation, cpw_style = cpw_style2 )
		#point_out - through cpw end point
		#point_coup1 - coupled cpw front end point
		#point_coup2 - coupled cpw rear end point
		self.lenght += l
		return point_out, point_coup1, point_coup2
		
	def cpw_pad(self, point, rotation = 0., pad_style = cpw_pad_style(), point_type = "cpw"):
		w = pad_style.width
		g = pad_style.gap
		l = pad_style.lenght
		eg = pad_style.edge_gap
		
		vert1 = [(0.,0.), (0.,w/2.+g), (eg+l,w/2.+g), (l+eg,w/2.), (eg,w/2.), (eg,0.)]
		end = (l+eg,0.)
		if point_type == 'cpw':
			vert1 = array(vert1) - (eg+l,0.)
			rotation = rotation+180.
		vert2 = self.__mirror_x(vert1)
		(vert1,vert2,[end]) = self.__transform((vert1,vert2,[end]), point, radians(rotation))
		#self.__draw_polylines((vert1,vert2))
		self.__draw_polyline(vert1)
		self.__draw_polyline(vert2)
		
		return end
		
	def smp_pad(self, point, rotation = 0., cpw_style1 = cpw_style(), cpw_style2 = cpw_style()):
		big_conn_w = 5000
		slot_w = 200
		slot_l = 3500

		vert1 = [(-slot_l/2., -big_conn_w/2.),
				(-slot_l/2., -big_conn_w/2.-slot_w),
				(slot_l/2., -big_conn_w/2.-slot_w),
				(slot_l/2., -big_conn_w/2.),
				(-slot_l/2., -big_conn_w/2.)]
		self.__draw_polyline(vert1)			
	
	def meander_optimize(self, p1, p2, span, l, rotation = 0., type = 'odd'):
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
		n -= 2
		half_step = m_l/(n+1.)
		
		#Lenght of first and last straight segments
		l_fl = (s - half_step + l_add)/2.
		
		#n - number of straight segments
		#print l_fl*2. + n*(s-half_step) + (n+1.)*pi*half_step/2.
		#s - optimized span	
		return n, s, half_step, l_fl
		
	def cpw_meander(self, p1, p2, l, span, rotation = 0., cpw_style = cpw_style(), type = 'odd'):
		ang = rotation
		p1 = array(p1)
		p2 = array(p2)
		
		n, span_opt, half_step, l_fl = self.meander_optimize( p1, p2, span, l, rotation = ang, type = type)
		
		#Bend radius
		r = half_step/2.
		#Straight segment lenght
		seg_l = span_opt - half_step
		#First straight segment
		p = self.cpw(p1, l_fl, rotation = ang, cpw_style=cpw_style)
		
		perp_v = array([cos(radians(rotation-90)), sin(radians(rotation-90))])
		
		if vdot(p2-p1, perp_v)>0:
			arc_angle = -90.
		else:
			arc_angle = 90.
			
		p, ang = self.cpw_round(p, r, arc_angle = arc_angle, rotation = ang, cpw_style=cpw_style)
		
		for i in range( int(n) ):
			#1/4 arc
			p, ang = self.cpw_round(p, r, arc_angle = arc_angle, rotation = ang, cpw_style=cpw_style)
			#straight segment
			p = self.cpw(p, seg_l, rotation = ang, cpw_style=cpw_style)
			arc_angle = -arc_angle
			#1/4 arc
			p, ang = self.cpw_round(p, r, arc_angle = arc_angle, rotation = ang, cpw_style=cpw_style)

		p, ang = self.cpw_round(p, r, arc_angle = arc_angle, rotation = ang, cpw_style=cpw_style)
		#last straight segment
		p = self.cpw(p, l_fl, rotation = ang, cpw_style=cpw_style)
		return p, ang
	
	def cpw_meander_line(self, p1, p2, l, r, span, cpw_style = cpw_style()):
		p1 = array(p1)
		p2 = array(p2)
		
		d = norm(p2-p1)
		if l<d : raise ValueError
		if 2.*r*(pi-2.)>(l-d):
			r = (l-d)/(pi-2.)/2.
		
		n=0
		s = span+1.
		L = d+1.
		while(s>span or L>d):
			n+=1
			s = (l - d - 2.*n*r*(1.+1./n)*(pi/2.-2.))/n
			L = 2.*n*r*(1.+1./n)
			if L > d: 
				r= d/( 2.*(n+1)*(1.+1./(n+1)) )
				s = span+1.
				continue
				
			if s/2.-r < r :
				r = s/4.
				s = span+1.
				n=1
				continue
		
		L_extra = (l - n*s - r*2.*n*(pi/2.-1.)*(1.+1./n))/2.
		
		seg_l = s - 2.*r
		
		
		vec = p2-p1
		ang = arctan2(vec[1],vec[0])*180./pi
		
		p = self.cpw(p1, L_extra, rotation = ang, cpw_style=cpw_style)
		p, ang = self.cpw_round(p, r, arc_angle = 90., rotation = ang, cpw_style=cpw_style)
		
		if seg_l/2. != r:
			p = self.cpw(p, seg_l/2.-r, rotation = ang, cpw_style=cpw_style)
		arc_angle = -90.
		p, ang = self.cpw_round(p, r, arc_angle = arc_angle, rotation = ang, cpw_style=cpw_style)
		if n>1:
			for i in range( n-1 ):
				#1/4 arc
				p, ang = self.cpw_round(p, r, arc_angle = arc_angle, rotation = ang, cpw_style=cpw_style)
				#straight segment
				p = self.cpw(p, seg_l, rotation = ang, cpw_style=cpw_style)
				arc_angle = -arc_angle
				#1/4 arc
				p, ang = self.cpw_round(p, r, arc_angle = arc_angle, rotation = ang, cpw_style=cpw_style)
				
		p, ang = self.cpw_round(p, r, arc_angle = arc_angle, rotation = ang, cpw_style=cpw_style)
		p = self.cpw(p, seg_l/2.-r, rotation = ang, cpw_style=cpw_style)
		arc_angle = -arc_angle
		p, ang = self.cpw_round(p, r, arc_angle = arc_angle, rotation = ang, cpw_style=cpw_style)
			
		p = self.cpw(p, L_extra, rotation = ang, cpw_style=cpw_style)
		return p, ang
		
	
	def cpw_meander_simple(self, p1, span, r, n, shift, rotation = 0., orient = 'r', cpw_style = cpw_style()):
		ang = rotation
		#First straight segment
		p = self.cpw(p1, span-r-shift, rotation = ang, cpw_style=cpw_style)
		if orient == 'r':
			arc_angle = -90.
		elif orient == 'l':
			arc_angle = 90.
			
		p, ang = self.cpw_round(p, r, arc_angle = arc_angle, rotation = ang, cpw_style=cpw_style)
		for i in range( int(n-1) ):
			#1/4 arc
			p, ang = self.cpw_round(p, r, arc_angle = arc_angle, rotation = ang, cpw_style=cpw_style)
			#straight segment
			p = self.cpw(p, span-2.*r, rotation = ang, cpw_style=cpw_style)
			arc_angle = -arc_angle
			#1/4 arc
			p, ang = self.cpw_round(p, r, arc_angle = arc_angle, rotation = ang, cpw_style=cpw_style)
		p, ang = self.cpw_round(p, r, arc_angle = arc_angle, rotation = ang, cpw_style=cpw_style)
		return p, ang	
		
		
	def meander_boxed(self, point, w, s, d, n, a, rotation = 0., box_w = 0.):
		#w - line width
		#s - span
		#d - half of the period
		#n - number of half periods
		#a - lenght of connecting wires
		#w - box width
		point = array(point)
		if box_w < s:
			box_w = s*1.5
		
		vert1 = [(0., w/2.), (a, w/2.)]
		vert2 = [(0., -w/2.), (a+w, -w/2.)]
		
		for i in range(1,n+1):
			x0 = (i-1)*d + a
			if 2*(i/2) != i:
				v1 = [(x0, s/2.+w/2.), (x0+d+w, s/2.+w/2.)]
				v2 = [(x0+w, s/2.-w/2.), (x0+d, s/2.-w/2.)]
			else:
				v1 = [(x0+w, -s/2.+w/2.),(x0+d, -s/2.+w/2.)]
				v2 = [(x0, -s/2.-w/2.),(x0+d+w,-s/2.-w/2.)]
			
			vert1 = vert1 + v1
			vert2 = vert2 + v2
		
		if 2*(i/2) != i:
			v1 = [(x0+d+w, w/2.), (x0+d+a+w, w/2.)]
			v2 = [(x0+d, -w/2.), (x0+d+a+w, -w/2.)]
		else:
			v1 = [(x0+d, w/2.), (x0+d+a+w, w/2.)]
			v2 = [(x0+d+w, -w/2.), (x0+d+a+w, -w/2.)]
		#Wires	
		vert1 = vert1 + v1
		vert2 = vert2 + v2
		#Box
		vert1 = vert1 + [(vert1[-1][0], box_w/2.), (0., box_w/2.)]
		vert2 = vert2 + [(vert2[-1][0], -box_w/2.), (0., -box_w/2.)]
		
		end = (vert1[-1][0],0.)
		
		(vert1,vert2,[end]) = self.__transform( (vert1,vert2,[end,]), point, radians(rotation))
		self.__draw_polylines( (vert1,vert2) )
		return end
		
	def meander_boxed_side(self, point, w, s, d, n, rotation = 0., box_w = 0., box_l = 0., orient = 'r', w1 = 0.):	
		#w - line width
		#w1 - line width at the bend
		#s - span
		#d - half of the period
		#n - number of half periods
		#w - box width
		
		if w1 == 0.:
			w1 = w
		point = array(point)
		if box_w < s:
			box_w = s*1.5
		if box_l < n*d + w:
			box_l = (n*d + w)*1.5	
			
		vert1 = [(0., w/2.), ((box_w + s + w)/2., w/2. ) ]
		vert2 = [(0., -w/2.), ((box_w + s - w)/2., -w/2. )]
		
		for i in range(1,n+1):
			y0 = (i-1)*d
			if 2*(i/2) != i:#odd
				v1 = [( (box_w+s+w1)/2., -d-w/2.-y0 ),( (box_w-s+w1)/2., -d-w/2.-y0 )]
				v2 = [( (box_w+s-w1)/2., -d+w/2.-y0 ),( (box_w-s-w1)/2., -d+w/2.-y0 )]
			else:#even
				v1 = [( (box_w-s+w1)/2., -d+w/2.-y0 ),( (box_w+s+w1)/2., -d+w/2.-y0 )]
				v2 = [( (box_w-s-w1)/2., -d-w/2.-y0 ),( (box_w+s-w1)/2., -d-w/2.-y0 )]
			
			vert1 = vert1 + v1
			vert2 = vert2 + v2
			
		if 2*(i/2) != i:
			vert1[-1] = (0. ,vert1[-1][1])
			vert2[-1] = (0. ,vert2[-1][1])
			vert1 += [( 0., -(box_l+n*d)/2. ),( box_w, -(box_l+n*d)/2. ),(box_w,(box_l-n*d)/2.),
						(0., (box_l-n*d)/2.)]
			end = (vert1[-1][0],vert1[-1][0]+w/2.)		
		else:
			vert1[-1] = (box_w ,vert1[-1][1])
			vert2[-1] = (box_w ,vert2[-1][1])
			vert1 += [( box_w, (box_l-n*d)/2. ),( 0., (box_l- n*d)/2. )]
			vert2 += [( box_w,-(box_l+n*d)/2.), ( 0.,-(box_l+n*d)/2.) ]	
			end = (vert1[-1][0],vert1[-1][0]-w/2.)
			
		if orient == 'l':
			vert1 = self.__mirror_x(vert1)
			vert2 = self.__mirror_x(vert2)
			
		(vert1,vert2,[end]) = self.__transform( (vert1,vert2,[end,]), point, radians(rotation))
		self.__draw_polylines( (vert1,vert2) )
		return
	
	#Straight section of fcpw
	def fcpw(self, fcpw_style, point, lenght, rotation = 0.):
		p = array(point)
		
		x,w,g = self.__fcpw_mk_periodic(fcpw_style, lenght)
		
		v1 = vstack([x, w/2.]).T
		v1_1 = vstack([x, w/2.+g]).T
	
		v1 = concatenate( (v1, v1_1[::-1]) )
		v2 = self.__mirror_x(v1)
		end = (lenght,0.)
		
		(v1,v2,[end]) = self.__transform( (v1,v2,[end,]), p, radians(rotation))
		self.__draw_polyline( v1 )
		self.__draw_polyline( v2 )
		
		if (lenght !=0):
			fcpw_style.lenght += lenght
			self.lenght += lenght
		else:
			fcpw_style.len_drawn += x[-1]
		return end
		
	def fcpw_round(self, fcpw_style, point, r, arc_angle = 180., rotation = 0.):
		lenght = abs(radians(arc_angle)*r)
		p = array(point)
		
		x,w,g = self.__fcpw_mk_periodic(fcpw_style, lenght)
			
		#Center point	
		pc = (0., sign(arc_angle)*r)
		x = sign(arc_angle)*(-pi/2. + x/r)
		x = concatenate( (x, x[::-1]) )
		r1 	= concatenate( (r + w/2., (r + w/2.+g)[::-1] ) )
		b = append(tan(diff(x)/4.),0.)
		r2 = concatenate( (r - w/2., (r-w/2.-g)[::-1]) )
		
		v1 = self.__pol_to_cart(r1, x) + pc
		v2 = self.__pol_to_cart(r2, x) + pc
		end = self.__pol_to_cart(r, -pi/2.*sign(arc_angle)+radians(arc_angle)) + pc
		
		(v1,v2,[end]) = self.__transform( (v1,v2,[end,]), p, radians(rotation))
		
		self.__draw_polyline(v1, bulges = b)
		self.__draw_polyline(v2, bulges = b)
		
		fcpw_style.lenght += lenght
		self.lenght += lenght
		
		return end, rotation + arc_angle
		
	def __fcpw_mk_periodic(self, fcpw_style, lenght):
		x_start = fcpw_style.lenght - trunc(fcpw_style.lenght/fcpw_style.x[-1])*fcpw_style.x[-1]
		
		ind = argwhere( (fcpw_style.x >= x_start) & (fcpw_style.x <= (x_start+lenght)) ).flatten()
		#if len[ind] == 0:
		#	ind = argwhere( fcpw_style.x >= x_start ).flatten()[0:1]
		x = fcpw_style.x[ind]
		w = fcpw_style.w[ind]
		g = fcpw_style.g[ind]
		
		if (x_start+lenght > fcpw_style.x[-1]):
		
			n = trunc((x_start+lenght)/fcpw_style.x[-1])
			if n >= 2. :
				for i in range(int(n-1)):
					x = concatenate( (x, fcpw_style.x + x[-1]) )
					w = concatenate( (w, fcpw_style.w ) )
					g = concatenate( (g, fcpw_style.g ) )
			
			x_stop = x_start + lenght - n*fcpw_style.x[-1]
			
			ind = argwhere( fcpw_style.x <= x_stop ).flatten()
			x = concatenate( (x, fcpw_style.x[ind] + x[-1]) )
			w = concatenate( (w, fcpw_style.w[ind]) )
			g = concatenate( (g, fcpw_style.g[ind]) )
		
		if(x[0] != x_start):
			dx = x[1]-x[0]
			if(dx!=0):
				dwdx = (w[1]-w[0])/dx
				dgdx = (g[1]-g[0])/dx
				dx = x[0]-x_start
			w =	append(w[0] - dwdx*dx, w)
			g = append(g[0] - dgdx*dx, g)	
			x = append(x_start,x)
		if(x[-1] != x_start + lenght):
			dx = x[-1]-x[-2]
			if(dx!=0):
				dwdx = (w[-1]-w[-2])/dx
				dgdx = (g[-1]-g[-2])/dx
				dx = (x_start + lenght)-x[-1]
			w =	append(w, w[-1] + dwdx*dx)
			g = append(g, g[-1] + dgdx*dx)
			x = append(x, x_start + lenght)
		return (x-x[0], w, g)
	
	#Constrain angle to interval -pi to pi	
	def __angnorm(self,ang):
		ang = ang - trunc(ang/(2.*pi))*2.*pi
		return ang - 2.*pi * trunc(ang/pi)
	
	#Route from p1 to p2 with straight line with two round bends
	def route(self,p1,p2,ang1,ang2,r0):
		p1 = array(p1)
		p2 = array(p2)
		ang1 = self.__angnorm(radians(ang1))
		ang2 = self.__angnorm(radians(ang2))
		
		Rang1 = self.__rot_matrix(ang1)
		Rang2 = self.__rot_matrix(ang2+pi)
		
		a2f = lambda a1: self.__angnorm(ang2-ang1-a1)
		
		def dp_f(a1,a2):
			Ra1 = self.__rot_matrix(a1)
			Ra2 = self.__rot_matrix(-a2)
			pr = array((0.,r0))
			p1_ = dot( Rang1, dot(Ra1, (0.,-sign(a1)*r0) ) + sign(a1)*pr ) + p1
			p2_ = dot( Rang2, dot(Ra2, (0.,sign(a2)*r0) ) + -sign(a2)*pr ) + p2
			return p2_-p1_
		
		def f(A1):
			A2 = a2f(A1)
			ang = zeros(len(A1))
			i=0
			for a1,a2 in zip(A1, A2):
				dp_ = dp_f(a1,a2)
				ang[i] = arctan2(dp_[1], dp_[0])
				i+=1
			return ang1 + self.__angnorm(A1) - ang
		'''	
		X = linspace(-pi,pi,1000)
		Y = f(X)
		plot(X,Y)
		show()
		'''
		dp = p2-p1
		a10 = arctan2(dp[1], dp[0])-ang1
		
		a1 = so.fsolve(f, a10)[0]
		a2 = a2f(a1)
		l = norm(dp_f(a1,a2))
		
		return degrees(a1),degrees(a2),l