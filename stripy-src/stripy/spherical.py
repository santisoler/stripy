"""
Copyright 2017 Louis Moresi, Ben Mather

This file is part of Stripy.

Stripy is free software: you can redistribute it and/or modify
it under the terms of the GNU Lesser General Public License as published by
the Free Software Foundation, either version 3 of the License, or any later version.

Stripy is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public License
along with Stripy.  If not, see <http://www.gnu.org/licenses/>.
"""

#!/usr/bin/python
# -*- coding: utf-8 -*-
from . import _stripack
from . import _ssrfpack
import numpy as np

try: range = xrange
except: pass

_ier_codes = {0:  "no errors were encountered.",
              -1: "N < 3 on input.",
              -2: "the first three nodes are collinear.\nSet permute to True or reorder nodes manually.",
              -3: "duplicate nodes were encountered.",
              -4: "an error flag was returned by a call to SWAP in ADDNOD.\n \
                   This is an internal error and should be reported to the programmer.",
              'L':"nodes L and M coincide for some M > L.\n \
                   The linked list represents a triangulation of nodes 1 to M-1 in this case.",
              1: "NCC, N, NROW, or an LCC entry is outside its valid range on input.",
              2: "the triangulation data structure (LIST,LPTR,LEND) is invalid.",
              'K': 'NPTS(K) is not a valid index in the range 1 to N.',
              9999: "Triangulation encountered duplicate nodes."}


class sTriangulation(object):
    """
    Define a Delaunay triangulation for given points on a sphere
    where lons and lats are 1D numpy arrays of equal length.

    Algorithm
    ---------
     R. J. Renka (1997), Algorithm 772; STRIPACK: Delaunay triangulation
     and Voronoi diagram on the surface of a sphere"
     ACM Trans. Math. Softw., Vol. 23, No. 3, pp 416-434
     doi:10.1145/275323.275329

    Parameters
    ----------
     lons    : 1D array of longitudinal coordinates in radians
     lats    : 1D array of latitudinal coordinates in radians
     refinement_levels (int)
             : refine the number of points in the triangulation
               (see uniformly_refine_triangulation)
     permute : (bool) randomises the order of lons and lats to improve
               triangulation efficiency and eliminate colinearity
               issues (see notes)
     tree    : (bool) construct a cKDtree for efficient nearest-
               neighbour lookup

    Attributes
    ----------
     lons : array of floats, shape (n,)
        stored longitudinal coordinates on a sphere
     lats : array of floats, shape (n,)
        stored latitudinal coordinates on a sphere
     x : array of floats, shape (n,)
        stored Cartesian x coordinates from input
     y : array of floats, shape (n,)
        stored Cartesian y coordinates from input
     z : array of floats, shape (n,)
        stored Cartesian z coordinates from input
     simplices : array of ints, shape (nsimplex, 3)
        indices of the points forming the simplices in the triangulation
        points are ordered anticlockwise
     lst : array of ints, shape (6n-12,)
        nodal indices with lptr and lend, define the triangulation as a set of N
        adjacency lists; counterclockwise-ordered sequences of neighboring nodes
        such that the first and last neighbors of a boundary node are boundary
        nodes (the first neighbor of an interior node is arbitrary).  In order to
        distinguish between interior and boundary nodes, the last neighbor of
        each boundary node is represented by the negative of its index.
        The indices are 1-based (as in Fortran), not zero based (as in python).
     lptr : array of ints, shape (6n-12),)
        set of pointers in one-to-one correspondence with the elements of lst.
        lst(lptr(i)) indexes the node which follows lst(i) in cyclical
        counterclockwise order (the first neighbor follows the last neighbor).
        The indices are 1-based (as in Fortran), not zero based (as in python).
     lend : array of ints, shape (n,)
        N pointers to adjacency lists.
        lend(k) points to the last neighbor of node K.
        lst(lend(K)) < 0 if and only if K is a boundary node.
        The indices are 1-based (as in Fortran), not zero based (as in python).

    Notes
    -----
     Provided the nodes are randomly ordered, the algorithm
     has expected time complexity O(N*log(N)) for most nodal
     distributions.  Note, however, that the complexity may be
     as high as O(N**2) if, for example, the nodes are ordered
     on increasing latitude.

     if permute=True, lons and lats are randomised on input before
     they are triangulated. The distribution of triangles will
     differ between setting permute=True and permute=False,
     however, the node ordering will remain identical.
    """
    def __init__(self, lons, lats, refinement_levels=0, permute=False, tree=False):

        # lons, lats = self._check_integrity(lons, lats)
        self.permute = permute
        self.tree = tree

        self._update_triangulation(lons, lats)

        for r in range(0,refinement_levels):
            lons, lats = self.uniformly_refine_triangulation(faces=False, trisect=False)
            self._update_triangulation(lons,lats)

        return

    def _generate_permutation(self, npoints):
        """
        Create shuffle and deshuffle vectors
        """
        i = np.arange(0, npoints)
        # permutation
        p = np.random.permutation(npoints)
        ip = np.empty_like(p)
        # inverse permutation
        ip[p[i]] = i
        return p, ip



    def _is_collinear(self, lons, lats):
        """
        Checks if first three points are collinear - in the spherical
        case this corresponds to all points lying on a great circle
        and, hence, all coordinate vectors being in a single plane.
        """

        x, y, z = lonlat2xyz(lons[:3], lats[:3])
        pts = np.column_stack([x, y, z])

        collinearity = (np.linalg.det(pts.T) == 0.0)

        return collinearity


    def _update_triangulation(self, lons, lats):

        npoints = len(lons)

        # Deal with collinear issue

        if self.permute:
            # Store permutation vectors to shuffle/deshuffle lons and lats
            niter = 0
            ierr = -2
            while ierr==-2 and niter < 5:
                p, ip = self._generate_permutation(npoints)
                lons = lons[p]
                lats = lats[p]
                # compute cartesian coords on unit sphere.
                x, y, z = _stripack.trans(lats, lons)
                lst, lptr, lend, ierr = _stripack.trmesh(x, y, z)
                niter += 1

            if niter >= 5:
                raise ValueError(_ier_codes[-2])
        else:
            p = np.arange(0, npoints)
            ip = p
            # compute cartesian coords on unit sphere.
            x, y, z = _stripack.trans(lats, lons)
            lst, lptr, lend, ierr = _stripack.trmesh(x, y, z)


        self._permutation = p
        self._invpermutation = ip


        if ierr > 0:
            raise ValueError('ierr={} in trmesh\n{}'.format(ierr, _ier_codes[9999]))
        if ierr != 0:
            raise ValueError('ierr={} in trmesh\n{}'.format(ierr, _ier_codes[ierr]))

        self.npoints = npoints
        self._lons = lons
        self._lats = lats
        self._x = x
        self._y = y
        self._z = z
        self._points = np.column_stack([x, y, z])
        self.lst = lst
        self.lptr = lptr
        self.lend = lend

        # Convert a triangulation to a triangle list form (human readable)
        # Uses an optimised version of trlist that returns triangles
        # without neighbours or arc indices
        nt, ltri, ierr = _stripack.trlist2(lst, lptr, lend)

        if ierr != 0:
            raise ValueError('ierr={} in trlist2\n{}'.format(ierr, _ier_codes[ierr]))

        # extract triangle list and convert to zero-based ordering
        self._simplices = ltri.T[:nt] - 1
        ## np.ndarray.sort(self.simplices, axis=1)

        ## If scipy is installed, build a KDtree to find neighbour points

        if self.tree:
            self._build_cKDtree()

    @property
    def lons(self):
        return self._deshuffle_field(self._lons)
    @property
    def lats(self):
        return self._deshuffle_field(self._lats)
    @property
    def x(self):
        return self._deshuffle_field(self._x)
    @property
    def y(self):
        return self._deshuffle_field(self._y)
    @property
    def z(self):
        return self._deshuffle_field(self._z)
    @property
    def points(self):
        return self._deshuffle_field(self._points)
    @property
    def simplices(self):
        return self._deshuffle_simplices(self._simplices)


    def _shuffle_field(self, *args):
        """
        Permute field
        """

        p = self._permutation

        fields = []
        for arg in args:
            fields.append( arg[p] )

        if len(fields) == 1:
            return fields[0]
        else:
            return fields

    def _deshuffle_field(self, *args):
        """
        Return to original ordering
        """

        ip = self._invpermutation

        fields = []
        for arg in args:
            fields.append( arg[ip] )

        if len(fields) == 1:
            return fields[0]
        else:
            return fields

    def _deshuffle_simplices(self, simplices):
        """
        Return to original ordering
        """
        p = self._permutation
        return p[simplices]


    def gradient_lonlat(self, data, nit=3, tol=1.0e-3, guarantee_convergence=False):
        """
        Return the lon / lat components of the gradient
        of a scalar field on the surface of the sphere.


        The method consists of minimizing a quadratic functional Q(G) over
        gradient vectors, where Q is an approximation to the linearized
        curvature over the triangulation of a C-1 bivariate function F(x,y)
        which interpolates the nodal values and gradients.

        Parameters
        ----------
         data : array of floats, shape (n,)
            field over which to evaluate the gradient
         nit: int (default: 3)
            number of iterations to reach a convergence tolerance, tol
            nit >= 1
         tol: float (default: 1e-3)
            maximum change in gradient between iterations.
            convergence is reached when this condition is met.

        Returns
        -------
         dfdlon : array of floats, shape (n,)
            derivative of f in the longitudinal direction
         dfdlat : array of floats, shape (n,)
            derivative of f in the lattitudinal direction

        Notes
        -----

        The gradient is computed via the Cartesian components using
        spherical.sTriangulation.gradient_xyz and the iteration parameters
        controling the spline interpolation are passed directly to this
        routine (See notes for gradient_xyz for more details).

        The gradient operator in this geometry is not well defined at the poles
        even if the scalar field is smooth and the Cartesian gradient is well defined.

        The routine spherical.dxyz2dlonlat is available to convert the Cartesian
        to lon/lat coordinates at any point on the unit sphere. This is helpful
        to avoid recalculation if you need both forms.
        """

        dfxs, dfys, dfzs = self.gradient_xyz(data, nit=nit, tol=tol, guarantee_convergence=guarantee_convergence)

        # get deshuffled versions
        lons = self.lons
        lats = self.lats
        z = self.z

        dlon = -dfxs * np.cos(lats) * np.sin(lons) + dfys * np.cos(lats) * np.cos(lons) # no z dependence
        dlat = -dfxs * np.sin(lats) * np.cos(lons) - dfys * np.sin(lats) * np.sin(lons) + dfzs * np.cos(lats)

        corr = np.sqrt((1.0-z**2))
        valid = ~np.isclose(corr,0.0)

        dlon[valid] = dlon[valid] / corr[valid]

        return dlon, dlat


    def gradient_xyz(self, f, nit=3, tol=1e-3, guarantee_convergence=False):
        """
        Return the cartesian components of the gradient
        of a scalar field on the surface of the sphere.

        The method consists of minimizing a quadratic functional Q(G) over
        gradient vectors, where Q is an approximation to the linearized
        curvature over the triangulation of a C-1 bivariate function F(x,y)
        which interpolates the nodal values and gradients.

        Parameters
        ----------
         f : array of floats, shape (n,)
            field over which to evaluate the gradient
         nit: int (default: 3)
            number of iterations to reach a convergence tolerance, tol
            nit >= 1
         tol: float (default: 1e-3)
            maximum change in gradient between iterations.
            convergence is reached when this condition is met.

        Returns
        -------
         dfdx : array of floats, shape (n,)
            derivative of f in the x direction
         dfdy : array of floats, shape (n,)
            derivative of f in the y direction
         dfdz : array of floats, shape (n,)
            derivative of f in the z direction

        Notes
        -----
         For SIGMA = 0, optimal efficiency was achieved in testing with
         tol = 0, and nit = 3 or 4.

         The restriction of F to an arc of the triangulation is taken to be
         the Hermite interpolatory tension spline defined by the data values
         and tangential gradient components at the endpoints of the arc, and
         Q is the sum over the triangulation arcs, excluding interior
         constraint arcs, of the linearized curvatures of F along the arcs --
         the integrals over the arcs of D2F(T)**2, where D2F(T) is the second
         derivative of F with respect to distance T along the arc.
        """

        if f.size != self.npoints:
            raise ValueError('f should be the same size as mesh')

        # gradient = np.zeros((3,self.npoints), order='F', dtype=np.float32)
        sigma = 0
        iflgs = 0

        f = self._shuffle_field(f)

        ierr = 1
        while ierr == 1:
            grad, ierr = _ssrfpack.gradg(self._x, self._y, self._z, f, self.lst, self.lptr, self.lend,\
                                   iflgs, sigma, nit, tol)
            if not guarantee_convergence:
                break

        if ierr < 0:
            raise ValueError('ierr={} in gradg\n{}'.format(ierr, _ier_codes[ierr]))

        return self._deshuffle_field(grad[0], grad[1], grad[2])


    def smoothing(self, f, w, sm, smtol, gstol):
        """
        Smooths a surface f by choosing nodal function values and gradients to
        minimize the linearized curvature of F subject to a bound on the
        deviation from the data values. This is more appropriate than interpolation
        when significant errors are present in the data.

        Parameters
        ----------
         f : array of floats, shape (n,)
            field to apply smoothing on
         w : array of floats, shape (n,)
            weights associated with data value in f
            w[i] = 1/sigma_f^2 is a good rule of thumb.
         sm : float
            positive parameter specifying an upper bound on Q2(f).
            generally n-sqrt(2n) <= sm <= n+sqrt(2n)
         smtol : float
            specifies relative error in satisfying the constraint
            sm(1-smtol) <= Q2 <= sm(1+smtol) between 0 and 1.
         gstol : float
            tolerance for convergence.
            gstol = 0.05*mean(sigma_f)^2 is a good rule of thumb.

        Returns
        -------
         f_smooth : array of floats, shape (n,)
            smoothed version of f
         (dfdx, dfdy, dfdz) : tuple of floats, tuple of 3 shape (n,) arrays
            first derivatives of f_smooth in the x, y, and z directions
        """

        if f.size != self.npoints or f.size != w.size:
            raise ValueError('f and w should be the same size as mesh')

        f, w = self._shuffle_field(f, w)

        sigma = 0
        iflgs = 0
        prnt = -1

        f_smooth, df, ierr = _ssrfpack.smsurf(self._x, self._y, self._z, f, self.lst, self.lptr, self.lend,\
                                             iflgs, sigma, w, sm, smtol, gstol, prnt)

        if ierr < 0:
            raise ValueError('ierr={} in gradg\n{}'.format(ierr, _ier_codes[ierr]))
        if ierr == 1:
            raise RuntimeWarning("No errors were encountered but the constraint is not active --\n\
                  F, FX, and FY are the values and partials of a linear function \
                  which minimizes Q2(F), and Q1 = 0.")
        if ierr == 2:
            raise RuntimeWarning("The constraint could not be satisfied to within SMTOL\
                  due to ill-conditioned linear systems.")

        return self._deshuffle_field(f_smooth), self._deshuffle_field(df[0], df[1], df[2])



    def _check_integrity(self, lons, lats):
        """
        Ensure lons and lats are:
         - 1D numpy arrays
         - equal size
         - within the appropriate range in radians
        """

        lons = np.array(lons).ravel()
        lats = np.array(lats).ravel()

        if len(lons.shape) != 1 or len(lats.shape) != 1:
            raise ValueError('lons and lats must be 1D')
        if lats.size != lons.size:
            raise ValueError('lons and lats must have same length')
        if (np.abs(lons)).max() > 2.*np.pi:
            raise ValueError("lons must be in radians (-2*pi <= lon <= 2*pi)")
        if (np.abs(lats)).max() > 0.5*np.pi:
            raise ValueError("lats must be in radians (-pi/2 <= lat <= pi/2)")
        return lons, lats





    def interpolate(self, lons, lats, zdata, order=1):
        """
        Base class to handle nearest neighbour, linear, and cubic interpolation.
        Given a triangulation of a set of nodes on the unit sphere, along with data
        values at the nodes, this method interpolates (or extrapolates) the value
        at a given longitude and latitude.

        Parameters
        ----------
         lons : float / array of floats, shape (l,)
                longitudinal coordinate(s) on the sphere
         lats : float / array of floats, shape (l,)
                latitudinal coordinate(s) on the sphere
         zdata : array of floats, shape (n,)
                value at each point in the triangulation
                must be the same size of the mesh
         order : int (default=1)
                order of the interpolatory function used
                 0 = nearest-neighbour
                 1 = linear
                 3 = cubic

        Returns
        -------
         zi : float / array of floats, shape (l,)
            interpolated value(s) at (lons, lats)
         err : int / array of ints, shape (l,)
            whether interpolation (0), extrapolation (1) or error (other)

        """


        shape = lons.shape

        lons, lats = self._check_integrity(lons, lats)

        if order not in [0,1,3]:
            raise ValueError("order must be 0, 1, or 3")
        if zdata.size != self.npoints:
            raise ValueError("data must be of size {}".format(self.npoints))

        zdata = self._shuffle_field(zdata)

        zi, zierr, ierr = _stripack.interp_n(order, lats, lons,\
                                      self._x, self._y, self._z, zdata,\
                                      self.lst, self.lptr, self.lend)

        if ierr != 0:
            print('Warning some points may have errors - check error array\n'.format(ierr))
            zi[zierr < 0] = np.nan

        return zi.reshape(shape), zierr.reshape(shape)


    def interpolate_nearest(self, lons, lats, data):
        """
        Interpolate using nearest-neighbour approximation
        Returns the same as interpolate(lons,lats,data,order=0)
        """
        return self.interpolate(lons, lats, data, order=0)

    def interpolate_linear(self, lons, lats, data):
        """
        Interpolate using linear approximation
        Returns the same as interpolate(lons,lats,data,order=1)
        """
        return self.interpolate(lons, lats, data, order=1)

    def interpolate_cubic(self, lons, lats, data):
        """
        Interpolate using cubic spline approximation
        Returns the same as interpolate(lons,lats,data,order=3)
        """
        return self.interpolate(lons, lats, data, order=3)


    def nearest_vertex(self, lons, lats):
        """
        Locate the index of the nearest vertex to points (lons,lats)
        and return the squared great circle distance between (lons,lats) and
        each nearest neighbour.

        Parameters
        ----------
         lons : float / array of floats, shape (l,)
            longitudinal coordinate(s) on the sphere
         lats : float / array of floats, shape (l,)
            latitudinal coordinate(s) on the sphere

        Returns
        -------
         index : array of ints
            the nearest vertex to each of the supplied points
         dist : array of floats
            great circle distance (angle) on the unit sphere to the closest
            vertex identified.


        Notes
        -----
         Faster searches can be obtained using a k-d tree.
         See sTriangulation.nearest_vertices() for details.
         There is an additional overhead associated with building and storing the k-d tree.

        """

        # translate to unit sphere

        xi = np.array(_stripack.trans(lats, lons))
        idx = np.empty_like(xi[0,:], dtype=np.int)
        dist = np.empty_like(xi[0,:], dtype=np.float)

        for pt in range(0, xi.shape[1]):
            xi0 = xi[:,pt]

            # i is the node at which we start the search
            # the closest x coordinate is a good place
            i = ((self._x - xi0[0])**2).argmin() + 1

            idx[pt], dist[pt] = _stripack.nearnd((xi0[0],xi0[1],xi0[2]), self._x, self._y, self._z, self.lst, self.lptr, self.lend, i)

        idx -= 1 # return to C ordering

        return self._deshuffle_simplices(idx), dist


    def containing_triangle(self, lons, lats):
        """
        Returns indices of the triangles containing lons / lats.

        Parameters
        ----------
         lons : float / array of floats, shape (l,)
            longitudinal coordinate(s) on the sphere
         lats : float / array of floats, shape (l,)
            latitudinal coordinate(s) on the sphere

        Returns
        -------
         tri_indices : array of ints, shape (l,)


        Notes
        -----
          The simplices are found as spherical.sTriangulation.simplices[tri_indices]

        """
        p = self._permutation
        pts = np.array(lonlat2xyz(lons,lats)).T

        sorted_simplices = np.sort(self._simplices, axis=1)

        triangles = []
        for pt in pts:
            t = _stripack.trfind(3, pt, self._x, self._y, self._z, self.lst, self.lptr, self.lend )
            tri = np.sort(t[3:6]) - 1

            triangles.append(np.where(np.all(p[sorted_simplices]==p[tri], axis=1))[0])

        return np.array(triangles).reshape(-1)


    def containing_simplex_and_bcc(self, lons, lats):
        """
        Returns the simplices containing (lons,lats)
        and the local barycentric, normalised coordinates.

        Parameters
        ----------
         lons : 1D array of longitudinal coordinates in radians
         lats : 1D array of latitudinal coordinates in radians

        Returns
        -------
         bcc  : normalised barycentric coordinates
         tri  : simplicies containing (lons,lats)

        Notes
        -----
         That the ordering of the vertices may differ from
         that stored in the self.simplices array but will
         still be a loop around the simplex.
        """

        pts = np.array(lonlat2xyz(lons,lats)).T

        tri = np.empty((pts.shape[0], 3), dtype=np.int) # simplices
        bcc = np.empty_like(tri, dtype=np.float) # barycentric coords

        for i, pt in enumerate(pts):
            t = _stripack.trfind(3, pt, self._x, self._y, self._z, self.lst, self.lptr, self.lend )
            tri[i] = t[3:6]
            bcc[i] = t[0:3]

        tri -= 1 # return to C ordering

        bcc /= bcc.sum(axis=1).reshape(-1,1)

        return bcc, self._deshuffle_simplices(tri)


    def identify_vertex_neighbours(self, vertex):
        """
        Find the neighbour-vertices in the triangulation for the given vertex
        (from the data structures of the triangulation)
        """
        vertex = self._permutation[vertex]

        lpl = self.lend[vertex-1]
        lp = lpl

        neighbours = []

        while True:
            lp = self.lptr[lp-1]
            neighbours.append(self.lst[lp-1]-1)
            if (lp == lpl):
                break

        return self._deshuffle_simplices(neighbours)


    def identify_vertex_triangles(self, vertices):
        """
        Find all triangles which own any of the vertices in the list provided
        """

        triangles = []

        for vertex in np.array(vertices).reshape(-1):
            triangles.append(np.where(self.simplices == vertex)[0])

        return np.unique(np.concatenate(triangles))



    def identify_segments(self):
        """
        Find all the segments in the triangulation and return an
        array of vertices (n1,n2) where n1 < n2
        """

        lst  = self.lst
        lend = self.lend
        lptr = self.lptr

        segments_array = np.empty((len(lptr),2),dtype=np.int)
        segments_array[:,0] = lst[:] - 1
        segments_array[:,1] = lst[lptr[:]-1] - 1

        valid = np.where(segments_array[:,0] < segments_array[:,1])[0]
        segments = segments_array[valid,:]

        return self._deshuffle_simplices(segments)


    def segment_midpoints_by_vertices(self, vertices):
        """
        Add midpoints to any segment connected to the vertices in the
        list / array provided.
        """

        segments = set()

        for vertex in vertices:
            neighbours = self.identify_vertex_neighbours(vertex)
            segments.update( min( tuple((vertex, n1)), tuple((n1, vertex))) for n1 in neighbours )

        segs = np.array(list(segments))

        new_midpoint_lonlats = self.segment_midpoints(segments=segs)

        return new_midpoint_lonlats


    def face_midpoints(self, simplices=None):
        """
        Identify the centroid of every simplex in the triangulation. If an array of
        simplices is given then the centroids of only those simplices is returned.
        """

        if type(simplices) == type(None):
            simplices = self.simplices

        mids = self.points[simplices].mean(axis=1)
        mids /= np.linalg.norm(mids, axis=1).reshape(-1,1)

        midlons, midlats = xyz2lonlat(mids[:,0], mids[:,1], mids[:,2])

        return midlons, midlats


    def segment_midpoints(self, segments=None):
        """
        Identify the midpoints of every line segment in the triangulation.
        If an array of segments of shape (no_of_segments,2) is given,
        then the midpoints of only those segments is returned. Note,
        segments in the array must not be duplicates or the re-triangulation
        will fail. Take care not to miss that (n1,n2) is equivalent to (n2,n1).
        """

        if type(segments) == type(None):
            segments = self.identify_segments()
        points = self.points

        mids = (points[segments[:,0]] + points[segments[:,1]]) * 0.5
        mids /= np.linalg.norm(mids, axis=1).reshape(-1,1)

        lons, lats = xyz2lonlat(mids[:,0], mids[:,1], mids[:,2])

        return lons, lats

    def segment_tripoints(self, ratio=0.33333):
        """
        Identify the trisection points of every line segment in the triangulation
        """

        segments = self.identify_segments()
        points = self.points

        mids1 = ratio * points[segments[:,0]] + (1.0-ratio) * points[segments[:,1]]
        mids1 /= np.linalg.norm(mids1, axis=1).reshape(-1,1)

        mids2 = (1.0-ratio) *  points[segments[:,0]] + ratio * points[segments[:,1]]
        mids2 /= np.linalg.norm(mids2, axis=1).reshape(-1,1)

        mids = np.vstack((mids1,mids2))

        midlls = xyz2lonlat(mids[:,0], mids[:,1], mids[:,2])

        return midlls


    def lons_map_to_wrapped(self, lon):

        lons = np.array(lon)
        lons = np.mod(lon+np.pi, 2*np.pi) - np.pi

        return lons

    def tri_area(self, lons, lats):
        """
        Calculate the area enclosed by 3 points on the unit sphere.

        Parameters
        ----------
         lons : array of floats, shape (3)
            longitudinal coordinates in radians
         lats : array of floats, shape (3)
            latitudinal coordinates in radians

        Returns
        -------
         area : float
            area of triangle on the unit sphere

        """
        lons, lats = self._check_integrity(lons, lats)

        # translate to unit sphere
        x, y, z = _stripack.trans(lats, lons)

        # compute area
        area = _stripack.areas(x, y, z)

        return area



    def areas(self):
        """
        Compute the area each triangle within the triangulation of points
        on the unit sphere.

        Returns
        -------
         area : array of floats, shape (nt,)
            area of each triangle in self.simplices where nt
            is the number of triangles.

        Notes
        -----
         This uses a Fortran 90 subroutine that wraps the AREA function
         to iterate over many points.
        """

        return _stripack.triareas(self.x, self.y, self.z, self.simplices.T+1)


    def edge_lengths(self):
        """
        Compute the edge-lengths of each triangle in the triangulation.
        """

        simplex = self.simplices.T

        # simplex is vectors a, b, c defining the corners
        a = self.points[simplex[0]]
        b = self.points[simplex[1]]
        c = self.points[simplex[2]]

        ## dot products to obtain angles
        ab = np.arccos((a * b).sum(axis=1))
        bc = np.arccos((b * c).sum(axis=1))
        ac = np.arccos((a * c).sum(axis=1))

        ## As this is a unit sphere, angle = length so ...

        return ab, bc, ac

    def angular_separation(self, lonp1, latp1, lonp2, latp2):
        """
        Compute the angles between lon / lat points p1 and p2 given in radians.
        On the unit sphere, this also corresponds to the great circle distance.
        p1 and p2 can be numpy arrays of the same length.

        This method simply calls the module-level function of the same name.
        Consider using the module function instead, as this method may be
        deprecated in favor of that function. For now, this method is
        retained to avoid issues with the Jupyter notebooks.
        """
        # Call the module-level function
        return angular_separation(lonp1, latp1, lonp2, latp2)

    def _add_spherical_midpoints(self):

        midlon_array, midlat_array = self.segment_midpoints()

        lonv2 = np.concatenate((self.lons, midlon_array), axis=0)
        latv2 = np.concatenate((self.lats, midlat_array), axis=0)

        return lonv2, latv2

    def _add_spherical_tripoints(self, ratio=0.333333):

        midlon_array, midlat_array = self.segment_tripoints(ratio=ratio)

        lonv2 = np.concatenate((self.lons, midlon_array), axis=0)
        latv2 = np.concatenate((self.lats, midlat_array), axis=0)

        return lonv2, latv2

    def _add_face_centroids(self):

        facelon_array, facelat_array = self.face_midpoints()

        lonv2 = np.concatenate((self.lons, facelon_array), axis=0)
        latv2 = np.concatenate((self.lats, facelat_array), axis=0)

        return lonv2, latv2


    def uniformly_refine_triangulation(self, faces=False, trisect=False):
        """
        return points defining a refined triangulation obtained by bisection of all edges
        in the triangulation
        """

        if faces:
            lonv1, latv1 = self._add_face_centroids()

        else:
            if not trisect:
                lonv1, latv1 = self._add_spherical_midpoints()
            else:
                lonv1, latv1 = self._add_spherical_tripoints(ratio=0.333333)


        return lonv1, latv1


    def midpoint_refine_triangulation_by_vertices(self, vertices):
        """
        return points defining a refined triangulation obtained by bisection of all edges
        in the triangulation connected to any of the vertices in the list provided
        """

        mlons, mlats = self.segment_midpoints_by_vertices(vertices=vertices)

        lonv1 = np.concatenate((self.lons, mlons), axis=0)
        latv1 = np.concatenate((self.lats, mlats), axis=0)

        return lonv1, latv1




    def edge_refine_triangulation_by_triangles(self, triangles):
        """
        return points defining a refined triangulation obtained by bisection of all edges
        in the triangulation that are associated with the triangles in the list
        of indices provided.

        Notes
        -----
         The triangles are here represented as a single index.
         The vertices of triangle i are given by self.simplices[i].
        """

        ## Note there should be no duplicates in the list of triangles
        ## but because we remove duplicates from the list of all segments,
        ## there is no pressing need to check this.

        # identify the segments

        simplices = self.simplices
        segments = set()

        for index in np.array(triangles).reshape(-1):
            tri = simplices[index]
            segments.add( min( tuple((tri[0], tri[1])), tuple((tri[1], tri[0]))) )
            segments.add( min( tuple((tri[1], tri[2])), tuple((tri[2], tri[1]))) )
            segments.add( min( tuple((tri[0], tri[2])), tuple((tri[2], tri[0]))) )

        segs = np.array(list(segments))

        mlons, mlats = self.segment_midpoints(segs)

        lonv1 = np.concatenate((self.lons, mlons), axis=0)
        latv1 = np.concatenate((self.lats, mlats), axis=0)

        return lonv1, latv1


    def edge_refine_triangulation_by_vertices(self, vertices):
        """
        return points defining a refined triangulation obtained by bisection of all edges
        in the triangulation connected to any of the vertices in the list provided
        """

        triangles = self.identify_vertex_triangles(vertices)

        return self.edge_refine_triangulation_by_triangles(triangles)



    def centroid_refine_triangulation_by_triangles(self, triangles):
        """
        return points defining a refined triangulation obtained by bisection of all edges
        in the triangulation that are associated with the triangles in the list provided.

        Notes
        -----
         The triangles are here represented as a single index.
         The vertices of triangle i are given by self.simplices[i].
        """

        # Remove duplicates from the list of triangles

        triangles = np.unique(np.array(triangles))

        mlons, mlats = self.face_midpoints(simplices=self.simplices[triangles])

        lonv1 = np.concatenate((self.lons, mlons), axis=0)
        latv1 = np.concatenate((self.lats, mlats), axis=0)

        return lonv1, latv1


    def centroid_refine_triangulation_by_vertices(self, vertices):
        """
        return points defining a refined triangulation obtained by bisection of all edges
        in the triangulation connected to any of the vertices in the list provided
        """

        triangles = self.identify_vertex_triangles(vertices)

        return self.centroid_refine_triangulation_by_triangles(triangles)



    def join(self, t2, unique=False):
        """
        Join this triangulation with another. If the points are known to have no duplicates, then
        set unique=True to skip the testing and duplicate removal
        """

        lonv1 = np.concatenate((self.lons, t2.lons), axis=0)
        latv1 = np.concatenate((self.lats, t2.lats), axis=0)

        ## remove any duplicates

        if not unique:
            lonv1, latv1 = remove_duplicate_lonlat(lonv1, latv1)

        return lonv1, latv1


    def _build_cKDtree(self):

        try:
            import scipy.spatial
            self._cKDtree =  scipy.spatial.cKDTree(self.points)

        except:
            self._cKDtree = None


    def nearest_vertices(self, lon, lat, k=1, max_distance=2.0 ):
        """
        Query the cKDtree for the nearest neighbours and Euclidean
        distance from x,y points.

        Returns 0, 0 if a cKDtree has not been constructed
        (switch tree=True if you need this routine)

        Parameters
        ----------
         lon : 1D array of longitudinal coordinates in radians
         lat : 1D array of latitudinal coordinates in radians
         k   : number of nearest neighbours to return
             (default: 1)
         max_distance
             : maximum Euclidean distance to search
               for neighbours (default: 2.0)

        Returns
        -------
         d    : Euclidean distance between each point and their
                nearest neighbour(s)
         vert : vertices of the nearest neighbour(s)
        """

        if self.tree == False or self.tree == None:
            return 0, 0

        lons = np.array(lon).reshape(-1,1)
        lats = np.array(lat).reshape(-1,1)

        xyz = np.empty((lons.shape[0],3))
        x,y,z = lonlat2xyz(lons, lats)

        xyz[:,0] = x[:].reshape(-1)
        xyz[:,1] = y[:].reshape(-1)
        xyz[:,2] = z[:].reshape(-1)

        dxyz, vertices = self._cKDtree.query(xyz, k=k, distance_upper_bound=max_distance)


        if k == 1:   # force this to be a 2D array
            vertices = np.reshape(vertices, (-1, 1))

        ## Now find the angular separation / great circle distance: dlatlon


        vertxyz = self.points[vertices].transpose(0,2,1)
        extxyz  = np.repeat(xyz, k, axis=1).reshape(vertxyz.shape)

        angles = np.arccos((extxyz * vertxyz).sum(axis=1))

        return angles, vertices




## Helper functions for the module

def remove_duplicate_lonlat(lon, lat):
    """
    remove duplicates from an array of lon / lat points
    """

    a = np.ascontiguousarray(np.vstack((lon, lat)).T)
    unique_a = np.unique(a.view([('', a.dtype)]*a.shape[1]))
    llunique = unique_a.view(a.dtype).reshape((unique_a.shape[0], a.shape[1]))

    lon1 = llunique[:,0]
    lat1 = llunique[:,1]

    return lon1, lat1


def lonlat2xyz(lon, lat):
    """
    Convert lon / lat (radians) for the spherical triangulation into x,y,z
    on the unit sphere
    """

    lons = np.array(lon)
    lats = np.array(lat)

    xs = np.cos(lats) * np.cos(lons)
    ys = np.cos(lats) * np.sin(lons)
    zs = np.sin(lats)

    return xs, ys, zs

def xyz2lonlat(x,y,z):
    """
    Convert x,y,z representation of points *on the unit sphere* of the
    spherical triangulation to lon / lat (radians).

    Note - no check is made here that (x,y,z) are unit vectors
    """

    xs = np.array(x)
    ys = np.array(y)
    zs = np.array(z)

    lons = np.arctan2(ys, xs)
    lats = np.arcsin(zs)

    return lons, lats


def dxyz2dlonlat(x,y,z, dfx, dfy, dfz):
    """
    Take stripack df/dx, df/dy, df/dz format and convert to
    surface gradients df/dlon, df/dlat

    Notes

    """

    xs = np.array(x)
    ys = np.array(y)
    zs = np.array(z)

    lons = np.arctan2(ys, xs)
    lats = np.arcsin(zs)

    dfxs = np.array(dfx)
    dfys = np.array(dfy)
    dfzs = np.array(dfz)

    dlon = -dfxs * np.cos(lats) * np.sin(lons) + dfys * np.cos(lats) * np.cos(lons) # no z dependence
    dlat = -dfxs * np.sin(lats) * np.cos(lons) - dfys * np.sin(lats) * np.sin(lons) + dfzs * np.cos(lats)

    corr = np.sqrt((1.0-zs**2))
    valid = ~np.isclose(corr,0.0)

    dlon[valid] = dlon[valid] / corr[valid]

    return dlon, dlat


def great_circle_Npoints(lonlat1r, lonlat2r, N):
    """
    N points along the line joining lonlat1 and lonlat2
    """

    ratio = np.linspace(0.0,1.0, N).reshape(-1,1)


    xyz1 = lonlat2xyz(lonlat1r[0], lonlat1r[1])
    xyz2 = lonlat2xyz(lonlat2r[0], lonlat2r[1])

    mids = ratio * xyz2 + (1.0-ratio) * xyz1
    norm = np.sqrt((mids**2).sum(axis=1))
    xyzN = mids / norm.reshape(-1,1)

    lonlatN = xyz2lonlat( xyzN[:,0], xyzN[:,1], xyzN[:,2])

    return lonlatN


def angular_separation(lonp1, latp1, lonp2, latp2):
    """
    Compute the angles between lon / lat points p1 and p2 given in radians.
    On the unit sphere, this also corresponds to the great circle distance.
    p1 and p2 can be numpy arrays of the same length.
    """

    xp1, yp1, zp1 = lonlat2xyz(lonp1, latp1)
    xp2, yp2, zp2 = lonlat2xyz(lonp2, latp2)

    ## dot products to obtain angles

    angles = np.arccos((xp1 * xp2 + yp1 * yp2 + zp1 * zp2))

    ## As this is a unit sphere, angle = length

    return angles

