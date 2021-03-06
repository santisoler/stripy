# litho1pt0

A Python interface to TRIPACK and STRIPACK Fortran code for (constrained) triangulation in Cartesian coordinates and on a sphere. Stripy is an object-oriented package and includes routines from SRFPACK and SSRFPACK for interpolation (nearest neighbor, linear and hermite cubic) and to evaluate derivatives (Renka 1996a,b and 1997a,b).

`stripy` is bundled with `litho1pt0` which is a python interface to the _crust 1.0_ dataset and the lithospheric part of the _litho 1.0_ dataset (Laske et al, 2013 and Pasyanos et al, 2014) which both requires and demonstrates the triangulation / searching and interpolation on the sphere that is provided by `stripy`.


![Examples](https://github.com/University-of-Melbourne-Geodynamics/stripy/blob/master/Notebooks/Images/Examples.png?raw=true)


_Sample images created with `stripy` illustrating the meshing capability, the ability to refine meshes to match criteria such as data density, and the ability to create distance-weighted averages to meshes and continuous interpolating functions_

#### binder

Launch the demonstration at [mybinder.org](https://mybinder.org/v2/gh/lmoresi/stripy-binder/master)

[![Binder](https://mybinder.org/badge.svg)](https://mybinder.org/v2/gh/lmoresi/stripy-binder/master)


## Navigation / Notebooks


There are two matching sets of `stripy` notebooks - one set for [Cartesian Triangulations](#Cartesian) and one for [Spherical Triangulations](#Spherical). For most geographical applications, the spherical triangulations are the natural choice as they expect longitude and latitude coordinates (admittedly in radians).


Note: the Cartesian and Spherical notebooks can be obtained / installed from `stripy` itself as follows:

```bash
   python -c 'import stripy; stripy.documentation.install_documentation(path="Notebooks")'   
```

### Cartesian

  - [Ex1-Cartesian-Triangulations.ipynb](CartesianTriangulations/Ex1-Cartesian-Triangulations.ipynb)
  - [Ex2-CartesianGrids.ipynb](CartesianTriangulations/Ex2-CartesianGrids.ipynb)
  - [Ex3-Interpolation.ipynb](CartesianTriangulations/Ex3-Interpolation.ipynb)
  - [Ex4-Gradients.ipynb](CartesianTriangulations/Ex4-Gradients.ipynb)
  - [Ex5-Smoothing.ipynb](CartesianTriangulations/Ex5-Smoothing.ipynb)
  - [Ex6-Scattered-Data.ipynb](CartesianTriangulations/Ex6-Scattered-Data.ipynb)
  - [Ex7-Refinement-of-Triangulations.ipynb](CartesianTriangulations/Ex7-Refinement-of-Triangulations.ipynb)

### Spherical

  - [Ex1-Spherical-Triangulations.ipynb](SphericalTriangulations/Ex1-Spherical-Triangulations.ipynb)
  - [Ex2-SphericalGrids.ipynb](SphericalTriangulations/Ex2-SphericalGrids.ipynb)
  - [Ex3-Interpolation.ipynb](SphericalTriangulations/Ex3-Interpolation.ipynb)
  - [Ex4-Gradients.ipynb](SphericalTriangulations/Ex4-Gradients.ipynb)
  - [Ex5-Smoothing.ipynb](SphericalTriangulations/Ex5-Smoothing.ipynb)
  - [Ex6-Scattered-Data.ipynb](SphericalTriangulations/Ex6-Scattered-Data.ipynb)
  - [Ex7-Refinement-of-Triangulations.ipynb](SphericalTriangulations/Ex7-Refinement-of-Triangulations.ipynb)


### Examples

Note, these examples are the notebooks from `litho1pt0` which are installed from the
package itself:

```bash
   python -c 'import litho1pt0; litho1pt0.documentation.install_documentation(path="Notebooks")'
```

The first three notebooks are an introduction to `litho1pt0` that does not explicitly mention `stripy` but
the next two worked examples show how to search, interpolate and plot with the help of `stripy` routines.

  - [Ex1-Litho1Layers.ipynb](litho1pt0/Ex1-Litho1Layers.ipynb)
  - [Ex2-Litho1Properties.ipynb](litho1pt0/Ex2-Litho1Properties.ipynb)
  - [Ex3-CrustalRegionalisation.ipynb](litho1pt0/Ex3-CrustalRegionalisation.ipynb)
  - [WorkEx1-CratonAverageProperties.ipynb](litho1pt0/WorkEx1-CratonAverageProperties.ipynb)
  - [WorkEx2-OceanDepthAge.ipynb](litho1pt0/WorkEx2-OceanDepthAge.ipynb)




## Installation

To install ([numpy](http://numpy.org) and fortran compiler, preferably
[gfortran](https://gcc.gnu.org/wiki/GFortran), required):

```bash
python setup.py build
```
   - If you change the fortran compiler, you may have to add the
flags `config_fc --fcompiler=<compiler name>` when setup.py is run
(see docs for [numpy.distutils](http://docs.scipy.org/doc/numpy-dev/f2py/distutils.html)).
```bash
python setup.py install
```

Alternatively install using pip:

```bash
pip install [--user] stripy
```

## Usage

Two classes are included as part of the Stripy package:

- sTriangulation (Spherical coordinates)
- Triangulation (Cartesian coordinates)

These classes share similar methods and can be easily interchanged.
In addition, there are many helper functions provided for building

A series of tests are located in the *tests* subdirectory.


## Docker

A more straightforward installation which does not depend on specific compilers relies on the [docker](http://www.docker.com) virtualisation system.

To install the docker image and test it is working:

```bash
   docker pull lmoresi/stripy:latest
   docker run --rm lmoresi/stripy:latest help
```

To install the helper scripts for bash:

```bash
   docker run --rm lmoresi/stripy:latest bash_utils > bash_utils.sh
   source bash_utils.sh
```

( you may find it helpful to move/rename this file and source it from
  your bash profile at login time )

The bash_utils.sh script installs the following functions which are
available through the bash command line:

```bash
  stripy-docker-help
  stripy-docker-sh
  stripy-docker-nb
  stripy-docker-browse
  stripy-docker-serve
  stripy-docker-terminal
```

For more information on these functions, run

```bash
  source bash_utils.sh
  stripy-docker-help
```

To use the docker version as you would, say, using ipython to type on the command line:

```bash
   source bash_utils.sh  # (only needs to be done once)
   stripy-docker-terminal
   ls
   ipython
```

To use the docker version to run a script

```bash
   source bash_utils.sh  # (only needs to be done once)
   stripy-docker-sh my_python_script.py
```



## References

   1. Laske, G., G. Masters, and Z. Ma (2013), Update on CRUST1. 0—A 1-degree global model of Earth's crust, Geophys Research Abstracts, 15, EGU2013–2658.

   1. Pasyanos, M. E., T. G. Masters, G. Laske, and Z. Ma (2014), LITHO1.0: An updated crust and lithospheric model of the Earth, Journal of Geophysical Research-Solid Earth, 119(3), 2153–2173, doi:10.1002/2013JB010626.

   1. R. J. Renka, "ALGORITHM 751: TRIPACK: A Constrained Two- Dimensional Delaunay Triangulation Package" ACM Trans. Math. Software, Vol. 22, No. 1, 1996, pp. 1-8.

   1. R. J. Renka, "ALGORITHM 752: SRFPACK: Software for Scattered Data Fitting with a Constrained Surface under Tension", ACM Trans. Math. Software, Vol. 22, No. 1, 1996, pp. 9-17.

   1. R. J. Renka, "ALGORITHM 772: STRIPACK: Delaunay Triangulation and Voronoi Diagram on the Surface of a Sphere" ACM Trans. Math. Software, Vol. 23, No. 3, 1997, pp. 416-434.

   1. R. J. Renka, "ALGORITHM 773: SSRFPACK: Interpolation of Scattered Data on the Surface of a Sphere with a Surface under Tension", ACM Trans. Math. Software, Vol. 23, No. 3, 1997, pp. 437-439.
