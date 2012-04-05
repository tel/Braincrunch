import time
import numpy as np
cimport numpy as np

cimport cython

DTYPE = np.uint8
ctypedef np.uint8_t DTYPE_t

@cython.boundscheck(False)
@cython.wraparound(False)
@cython.cdivision(True)
def exhaustive_centroid(np.ndarray[DTYPE_t, ndim=3] img not None, DTYPE_t r, DTYPE_t g, DTYPE_t b):

    """ exhaustive_centroid searches an entire image for pixels of a particular
    color, returning their count and that set's centroid.  """

    assert img.dtype == DTYPE
    assert img.shape[2] == 3

    cdef int h = img.shape[0]
    cdef int w = img.shape[1]
    cdef int hmid = h // 2
    cdef int wmid = w // 2

    cdef float xc = 0
    cdef float yc = 0
    cdef float count = 0
    cdef unsigned int x, y
    for x in range(w):
        for y in range(h):
            if img[y, x, 0] == r and img[y, x, 1] == b and img[y, x, 2] == g:
                count += 1
                xc += 1/count*(x - wmid - xc)
                yc += 1/count*(y - hmid - yc)
    xcf = xc + wmid
    ycf = yc + hmid
    return ([xcf, ycf], count)

@cython.boundscheck(False)
@cython.wraparound(False)
@cython.cdivision(True)
def diffusive_centroid(np.ndarray[DTYPE_t, ndim=3] img not None, int x0, int y0, DTYPE_t r, DTYPE_t g, DTYPE_t b, int walk_steps = 200):

    """ diffusive_centroid attempts to estimate the centroid by random walks
    starting from a (known) interior point.

    The estimation process proceeds by taking `walk_steps` iterated Gaussian
    jumps from the initial point on 4 independent chains. Each time the jump
    remains inside the colored set, its current position is averaged to compute
    the centroid. If the jump does not land in the colored set then it's
    ignored.

    It's fairly easy to see this process as an expectation operator on a MCMC
    produced by the (unnormalized) probability distribution Indicator[x colored
    r, g, b]. Thus, by that argument this estimation is probably convergent."""

    assert img.dtype == DTYPE
    assert img.shape[2] == 3

    cdef int h = img.shape[0]
    cdef int w = img.shape[1]

    # Tweaking parameters
    cdef int chaincount = 4
    cdef float jumping_stddev = 10

    cdef float xc = 0
    cdef float yc = 0
    cdef float xc1, yc1
    cdef float count = 0
    cdef int x, y, x1, y1
    cdef unsigned int chain, i, xidx, yidx
    cdef np.ndarray[DTYPE_t, ndim=2] jumps
    for chain in range(chaincount):
        x = 0
        y = 0
        xc1 = <float>x
        yc1 = <float>y
        count = 1
        # Preallocate jumps with fast vectorized numpy code
        jumps = np.uint8(np.round(np.random.normal(0, jumping_stddev, (walk_steps, 2))))
        for i in range(walk_steps):
            x1 = x + jumps[i, 0]
            y1 = y + jumps[i, 1]
            xidx = <unsigned int>(x1 + x0)
            yidx = <unsigned int>(y1 + y0)
            if x1 + x0 < 0 or y1 + y0 < 0 or x1 + x0 >= w or y1 + y0 >= h:
                # We're out of bounds, so just ignore this jump
                continue
            if img[yidx, xidx, 0] == r and img[yidx, xidx, 1] == g and img[yidx, xidx, 2] == b:
                # We're still in the color set
                x, y = x1, y1
                count += 1
                xc1 += 1/count*(<float>x - xc1)
                yc1 += 1/count*(<float>y - yc1)
        xc += xc1/chaincount
        yc += yc1/chaincount
    
    return [xc + x0, yc + y0] 
