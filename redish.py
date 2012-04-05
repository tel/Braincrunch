from __future__ import with_statement

"""Redis helper functions"""

import redis

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

def massget(redis, prefix, sufflist, transform = lambda(x): x):
    return dict((suff, transform(redis.get(rk(prefix, suff)))) for suff in sufflist)
