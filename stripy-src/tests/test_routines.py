import numpy as np
import stripy
from time import clock

# global variables
permute = False
max_refinements = 2
npoints = 100000


def time_routine(routine, *args):
    t = clock()
    routine(*args)
    str_fmt = "- {:30} completed in  {:1.6f} seconds"
    print(str_fmt.format(str(routine.__name__), clock()-t))

"""
Test Triangulation routines
"""
print("==========\nTriangulation routines\n==========")

# Create some (semi) random points
np.random.seed(0)
x = np.random.random(npoints)
y = np.random.random(npoints)

xi = np.random.random(100)
yi = np.random.random(100)
rint = np.random.randint(0, len(xi), len(xi))

# triangulation
tri = stripy.Triangulation(x, y)

for refine in range(max_refinements):
    print("\nrefinement = {}\n".format(refine))
    time_routine(tri.__init__, x, y, refine, permute)

    z = np.hypot(tri.x, tri.y)

    time_routine(tri.areas)
    time_routine(tri.convex_hull)
    time_routine(tri.gradient, z)
    time_routine(tri.gradient_local, z, 0)
    time_routine(tri.interpolate_nearest, xi, yi, z)
    time_routine(tri.interpolate_linear, xi, yi, z)
    time_routine(tri.interpolate_cubic, xi, yi, z)
    time_routine(tri.nearest_vertex, xi, yi)
    time_routine(tri.containing_triangle, xi, yi)
    time_routine(tri.containing_simplex_and_bcc, xi, yi)


"""
Test  sTriangulation routines
"""
print("==========\nsTriangulation routines\n==========")

# Create some (semi) random points
np.random.seed(0)
lons = 2.*np.pi*np.random.random(npoints)
lats = np.arccos(2.*np.random.random(npoints) - 1.) - np.pi/2

lon = 2.*np.pi*np.random.random(100)
lat = np.arccos(2.*np.random.random(100) - 1.) - np.pi/2
rint = np.random.randint(0, len(lon), len(lon))

stri = stripy.sTriangulation(lons, lats)

for refine in range(max_refinements):
    print("\nrefinement = {}\n".format(refine))
    time_routine(stri.__init__, lons, lats)

    Z = np.exp(-stri.lons**2 - stri.lats**2)

    time_routine(stri.areas)
    time_routine(stri.gradient_lonlat, Z)
    time_routine(stri.interpolate_nearest, lon, lat, Z)
    time_routine(stri.interpolate_linear, lon, lat, Z)
    time_routine(stri.interpolate_cubic, lon, lat, Z)
    time_routine(stri.nearest_vertex, lon, lat)
    time_routine(stri.tri_area, lon[:3], lat[:3])
    time_routine(stri.identify_vertex_neighbours, rint[0])
    time_routine(stri.containing_triangle, lon, lat)
    time_routine(stri.containing_simplex_and_bcc, lon, lat)
