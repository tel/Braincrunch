# Redis Index

## Log

## Slices

Currently these are assumed to be a big set of slices with a common set of
prefixes. 

* `Slices.count` counts the number of known slices
* `Slices.path` is the location of the slices
* `Slices.format` is the format string of the slices ('png' not '.png')
* `Slices:prefixes` is a list of slice prefixes, stored in z-order. Note that
  Redis is 0-based, but so are stack coordinates.

## Objects

Any slice consists of a large number of objects, each with a different id and
color. This information is mostly just a copy of the information from
fullressegJV.txt but available for live editing and extension.

* `Objects.interesting` A list of "interesting" objects
* `Objects.bounded` A list of objects with known boundaries
* `Objects:<id>` prefix for a particular object
  * `:name` object name
  * `:x/y/zseed` x/y/z coordinate of a single pixel known to be in this object set
  * `:r`, `:g`, `:b` is the unique color code of this object
  * `:x/y/zmin` minimum observed x/y/z location
  * `:x/y/zmax` maximum observed x/y/z location
  * `:x/y/zrange` x/y/z/-linear size of bounding box
  * `:bounded` boolean for whether the boundary footprint has positive volume
  * `:log10footprint2` log10(xrange*yrange) (exists iff :bounded)
  * `:log10footprint` log10(xrange*yrange*zrange) (exists iff :bounded)
  * `:centered` boolean for whether this object has slice centroids (not
    relevant for, say, the background object)
  * `:<z>` slice specific observations prefix
	* `:xc`, `:yc` x and y centroid position (can't guarantee this to be in an
	   object's set/extent)

## Colors 

Colors are the reverse object index, pixel color to object id

* `Colors:<r>:<g>:<b>:object` is the object id for the color (`r`, `g`, `b`)
