#!/usr/bin/env python

import re, redis, rq
import numpy as np
from PIL import Image
import fabric as f

import objects as o
from redish import *

r = redis.StrictRedis()
rq.use_connection()

def color_objects():
    q = rq.Queue('coloring')

    # Clear old colorings
    for key in r.keys(rk('Objects', '*', 'colored')):
        r.delete(key)
    for col in ['r', 'g', 'b']:
        for key in r.keys(rk('Objects', '*', col)):
            r.delete(key)
    for key in r.keys(rk('Colors', '*')):
        r.delete(key)

    keys = r.keys(rk('Objects', '*', 'seeded'))
    for key in keys:
        id = re.split(':', key)[1]
        q.enqueue(o.color_object, id)

def read_txtdb(path):
    lines = list(open(path).readlines())
    for line in lines:
        line in line.strip()
        cs = re.split(' +', line)   
        nums = [int(x) for x in cs[0:24]] # treat as integers
        name = ''.join(cs[24:])[1:-1]

        id = nums[0]
        xseed, yseed, zseed = nums[10:13]
        seeded = xseed > 0 and yseed > 0 and zseed > 0
        xmin, ymin, zmin = nums[18:21]
        xmax, ymax, zmax = nums[21:24]
        xrange = xmax-xmin
        yrange = ymax-ymin
        zrange = zmax-zmin

        massset(r, rk('Objects', id),
                name = name,
                xmin = xmin,
                ymin = ymin,
                zmin = zmin,
                xmax = xmax,
                ymax = ymax,
                zmax = zmax,
                xrange = xrange,
                yrange = yrange,
                zrange = zrange)

        if seeded:
            massset(r, rk('Objects', id),
                    xseed = xseed,
                    yseed = yseed,
                    zseed = zseed,
                    seeded = seeded)

        if xrange == 0 or yrange == 0 or zrange == 0:
            pass
        else:
            massset(r, rk('Objects', id),
                    bounded = True,
                    log10footprint2 = np.log10(xrange) + np.log10(yrange),
                    log10footprint  = np.log10(xrange) + np.log10(yrange) + np.log10(zrange))

        print("Object ({}) :: pos({}, {}, {})".format(id, xseed, yseed, zseed))
