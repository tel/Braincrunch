from __future__ import with_statement
import redis
import numpy as np
import rq
from PIL import Image

r = redis.StrictRedis()

def rk(*objs):
    
    """Makes a Redis key from some components"""

    sep = ':'

    return sep.join(['{}'.format(x) for x in objs])

def massset(redis, prefix, **args):
    """Atomically do a mass set"""
    with redis.pipeline() as pipe:
        for k, v in args.iteritems():
            pipe.set(rk(prefix, k), v)
        pipe.execute()

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

    for i in xrange(w):
        for j in xrange(h):
            x, y = i + xoff, j + yoff
            re, gr, bl = img[i, j, :]

            # Hashed for convenience
            pos = {'x': x, 'y': y, 'z': z}

            pid = r.exists(rk('Colors', re, gr, bl, 'process'))
            if pid:
                # Someone has seen this color before. Let's increase the
                # bounding boxes, but ensure that this operation is atomic!
                prefix = rk('Processes', pid)
                with r.pipeline() as pipe:
                    while True:
                        try:
                            dims = ['x', 'y', 'z']
                            # Check for changes to the bounds: they indicate competing writes!
                            for d in dims:
                                pipe.watch(rk(prefix, d + 'min'))
                                pipe.watch(rk(prefix, d + 'max'))
                            # Buffer the updates
                            pipe.multi()
                            for d in dims:
                                min0 = min(r.get(rk(prefix, d + 'min')), pos[d])
                                max0 = max(r.get(rk(prefix, d + 'max')), pos[d])
                                r.set(rk(prefix, d + 'min'), min0)
                                r.set(rk(prefix, d + 'max'), max0)
                            pipe.execute()
                            # After executing the writes, we're done so stop the repeat loop
                            break
                        except redis.WatchError:
                            # There was an atomicity conflict, repeat the operation
                            continue
            else:
                # This is a new color! Let's add it to the process index.
                with r.pipeline() as pipe:
                    pid = r.incr("Processes.count")
                    massset(pipe, rk('Processes', pid), r = re, g = gr, b = bl, 
                            xmax = x, xmin = x, ymax = y, ymin = y, zmax = z, zmin = z)
                    massset(pipe, rk('Colors', re, gr, bl), process = pid)
                    pipe.execute()
