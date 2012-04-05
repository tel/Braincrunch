from __future__ import with_statement

import rq, redis
import numpy as np
from PIL import Image

from redish import *
import cobjects as co

r = redis.StrictRedis()
W, H = 8192, 8192

def objects_in_slice(z):
    ids = r.lrange('Objects.bounded', 0, -1)
    out = []
    for id in ids:
        zmin = r.get(rk('Objects', id, 'zmin'))
        zmax = r.get(rk('Objects', id, 'zmax'))
        if int(zmin) <= z <= int(zmax):
            out.append(int(id))
    return out

def subslice(xmin, xmax, ymin, ymax, y0x0, y0x1, y1x0, y1x1):

    """Pulls out a contiguous subslice on global coordinates across the four
    quadrants of a slice image."""

    w, h, d = y0x0.shape

def img_for_coordinate(x, y, z):
    prefix = r.lindex('Slices:prefixes', z)
    path = r.get('Slices.path')
    format = r.get('Slices.format')
    
    if x >= W:
        if y >= H:
            suff = "_Y1_X1"
        else:
            suff = "_Y0_X1"
    else:
        if y >= H:
            suff = "_Y1_X0"
        else:
            suff = "_Y0_X0"

    im = Image.open(path + prefix + suff + "." + format)
    return np.asarray(im)

def color_object(id):
    dat = massget(r, rk('Objects', id),
            ['xseed', 'yseed', 'zseed'], int)
    im = img_for_coordinate(dat['xseed'], dat['yseed'], dat['zseed'])

    red, green, blue = im[dat['yseed'] % W, dat['xseed'] % H, :]

    massset(r, rk('Objects', id), 
            r = red,
            b = blue,
            g = green)

    if red != 0 or blue != 0 or green != 0:
        massset(r, rk('Objects', id), colored = True)

    r.rpush(rk('Colors', red, green, blue, 'objects'), id)

def centroids_here(z):
    prefix = r.lindex('Slices:prefixes', z)
    path = r.get('Slices.path')
    format = r.get('Slices.format')

    print "Loading images"
    y0x0 = np.asarray(Image.open(path + prefix + "_Y0_X0." + format))
    y0x1 = np.asarray(Image.open(path + prefix + "_Y0_X1." + format))
    y1x0 = np.asarray(Image.open(path + prefix + "_Y1_X0." + format))
    y1x1 = np.asarray(Image.open(path + prefix + "_Y1_X1." + format))
    
    print "Merging images"
    img = np.vstack([np.hstack([y0x0, y0x1]), np.hstack([y1x0, y1x1])])

    id = '199'
    print id
    data = massget(r, rk('Objects', id),
            ['xmin', 'xmax', 'ymin', 'ymax', 'r', 'g', 'b'], int)
    simg = img[data['xmin']:(data['xmax']+1), data['ymin']:(data['ymax']+1), :]
    #centroid, tohit = co.exhaustive_search(simg, data['r'], data['g'], data['b'])
    return simg

def color_centroid(img, red, blue, green, nsamp = 5000):

    """ Computes the centroid of the pixels of a particular color in an image.
    The process is stochastic so as to get good speed even in large images, so
    if an object is very sparse within its bounding box then it is unlikely to
    be well estimated.
    
    Returns the centroid approximation and the probability of hitting the
    object within its bounding box."""

    w, h, d = img.shape
    if d != 3:
        print (w, h, d)
        raise Exception("Cannot compute color centroid unless image depth is 3")

    xc, yc = 0, 0
    wmid, hmid = np.floor(w/2), np.floor(h/2)
    count = 0
    for i in xrange(nsamp):
        x = np.floor(np.random.random()*w)-wmid
        y = np.floor(np.random.random()*h)-hmid
        if (img[x,y,:] == [red, blue, green]).all():
            count += 1
            xc += x
            yc += y

    if count == 0:
        raise Exception("Could not estimate centroid: never hit object!")
        
    xc = xc/count+wmid
    yc = yc/count+hmid
    hitprob = count/nsamp
    
    return [xc, yc], hitprob
