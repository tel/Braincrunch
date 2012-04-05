from distutils.core import setup
from distutils.extension import Extension
from Cython.Distutils import build_ext

import numpy as np

try:
    numpy_include = np.get_include()
except AttributeError:
    numpy_include = np.get_numpy_include()

ext_modules = [Extension("cobjects", ["cobjects.pyx"], 
                         include_dirs=[numpy_include],
                         extra_compile_args=['-O3', '-ffast-math'])]

setup(
    name = 'Braincrunching!',
    cmdclass = {'build_ext': build_ext},
    ext_modules = ext_modules
)
