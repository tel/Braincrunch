from __future__ import with_statement
import numpy as np
import sys, time, redis, rq
from PIL import Image

from redish import *

r = redis.StrictRedis()

def find_processes_at(z, queue):

    """In some particular z-slice, `z`, update the database with the processes
    observed."""

    prefix = r.lindex('Slices:prefixes', z)
    path   = r.get('Slices.path')
    format = r.get('Slices.format')

    if prefix:
        queue.enqueue(find_processes_in, z, path + prefix + '_Y0_X0' + '.' + format, 0, 0)
        queue.enqueue(find_processes_in, z, path + prefix + '_Y0_X1' + '.' + format, 8192, 0)
        queue.enqueue(find_processes_in, z, path + prefix + '_Y1_X0' + '.' + format, 0, 8192)
        queue.enqueue(find_processes_in, z, path + prefix + '_Y1_X1' + '.' + format, 8192, 8192)

def find_processes_in(z, impath, xoff, yoff):

    """In some particular image, located at `impath`, update the database with
    the processes observed."""

    # This could be bad for memory, but we'll try it anyway
    img = np.asarray(Image.open(impath))
    w, h, d = img.shape

    Q = False
    for i in xrange(w):
        print i
        for j in xrange(h):
            x, y = i + xoff, j + yoff
            re, gr, bl = img[i, j, :]

            # Hashed for convenience
            pos = {'x': x, 'y': y, 'z': z}

            pid = r.get(rk('Colors', re, gr, bl, 'process'))

            if (re != 0 or gr != 0 or bl != 0):
                # Live pixel!
                if pid:
                    # Someone has seen this color before. Let's increase the
                    # bounding boxes, but ensure that this operation is atomic!
                    prefix = rk('Processes', pid)
                    with r.pipeline() as pipe:
                        while True:
                            try:
                                dims = ['x', 'y', 'z']
                                def trans(pipe):
                                    mins = {}
                                    maxs = {}
                                    for d in dims:
                                        mins[d] = min(int(pipe.get(rk(prefix, d + 'min'))), pos[d])
                                        maxs[d] = max(int(pipe.get(rk(prefix, d + 'max'))), pos[d])
                                    pipe.multi()
                                    for d in dims:
                                        pipe.set(rk(prefix, d + 'min'), mins[d])
                                        pipe.set(rk(prefix, d + 'max'), maxs[d])
                                r.transaction(trans, *([rk(prefix, d + 'min') for d in dims] + [rk(prefix, d + 'max') for d in dims]))
                                # After executing the writes, we're done so stop the repeat loop
                                break
                            except redis.WatchError:
                                # There was an atomicity conflict, repeat the operation
                                sys.stdout.write('.')
                                time.sleep(0.8)
                                continue
                else:
                    # This is a new color! Let's add it to the process index.
                    with r.pipeline() as pipe:
                        pid = r.incr("Processes.count")
                        massset(pipe, rk('Processes', pid), r = re, g = gr, b = bl, 
                                xmax = x, xmin = x, ymax = y, ymin = y, zmax = z, zmin = z)
                        massset(pipe, rk('Colors', re, gr, bl), process = pid)
                        pipe.execute()
