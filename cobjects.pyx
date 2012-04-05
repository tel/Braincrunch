import time
import numpy as np
cimport numpy as np

cimport cython

DTYPE = np.uint8
ctypedef np.uint8_t DTYPE_t

cdef extern from "math.h":
    double floor(double)
    double ceil(double)

cdef inline double round(double x):
    return floor(x) if x-floor(x) < 0.5 else ceil(x)

def exhaustive_centroid(np.ndarray img not None, DTYPE_t r, DTYPE_t g, DTYPE_t b):

    """ exhaustive_centroid searches an entire image for pixels of a particular
    color, returning their count and that set's centroid.  """

    assert img.dtype == DTYPE
    assert img.shape[2] == 3

    cdef int h = img.shape[0]
    cdef int w = img.shape[1]
    cdef int hmid = h // 2
    cdef int wmid = w // 2

    cdef np.int32_t xc = 0
    cdef np.int32_t yc = 0
    cdef np.int32_t count = 0
    for x in range(w):
        for y in range(h):
            if img[y, x, 0] == r and img[y, x, 1] == b and img[y, x, 2] == g:
                count += 1
                xc += x - wmid
                yc += y - hmid
    cdef float xcf, ycf
    if count > 0:
        xcf = xc/count + wmid
        ycf = yc/count + hmid
        return ([xcf, ycf], count)

def diffusive_centroid(np.ndarray img not None, int x0, int y0, DTYPE_t r, DTYPE_t g, DTYPE_t b, int walk_steps = 200):

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
    cdef np.int32_t x, y, x1, y1
    cdef np.ndarray jumps
    for chain in range(chaincount):
        x = 0
        y = 0
        xc1 = <float>x
        yc1 = <float>y
        count = 1
        # Preallocate jumps with fast vectorized numpy code
        jumps = np.random.normal(0, jumping_stddev, (walk_steps, 2))
        for i in range(walk_steps):
            x1 = x + <np.int32_t>round(jumps[i, 0])
            y1 = y + <np.int32_t>round(jumps[i, 1])
            if x1 + x0 < 0 or y1 + y0 < 0 or x1 + x0 >= w or y1 + y0 >= h:
                # We're out of bounds, so just ignore this jump
                continue
            if img[y1+y0, x1+x0, 0] == r and img[y1+y0, x1+x0, 1] == g and img[y1+y0, x1+x0, 2] == b:
                # We're still in the color set
                x, y = x1, y1
                count += 1
                xc1 += 1/count*(<float>x - xc1)
                yc1 += 1/count*(<float>y - yc1)
        xc += xc1/chaincount
        yc += yc1/chaincount
    
    return [xc + x0, yc + y0] 
