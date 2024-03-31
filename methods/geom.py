from numpy import *
	
def rot_matrix(phi):
	return array(((cos(phi),-sin(phi)),(sin(phi),cos(phi))))

def transform(point, translation, phi):
	point = array(point)
	translation = array(translation)
	A = rot_matrix(phi)
	return dot(A,point) + translation
	
def place_ports(port, point, direction, p_coords, p_dirs):
	p_coords = array(p_coords)
	p_dirs = array(p_dirs)
	print(p_dirs)
	place_origin = point - transform(p_coords[port],(0,0),direction-p_dirs[port])
	rotation = direction - p_dirs[port]
	for i,p_coord in enumerate(p_coords):
			p_coords[i] = transform(p_coord, place_origin, rotation)
			print(p_dirs[i])
			p_dirs[i] += rotation
			print(rotation, p_dirs[i])
	print(p_dirs)		
	return place_origin, rotation, p_coords, p_dirs