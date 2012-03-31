
# Redis Index

## Log

* Index started on Sat Mar 31 6p
  7400 images to process

## Slices

Currently these are assumed to be a big set of slices with a common set of
prefixes. 

* `Slices.count` counts the number of known slices
* `Slices.path` is the location of the slices
* `Slices.format` is the format string of the slices ('png' not '.png')
* `Slices:prefixes` is a list of slice prefixes, stored in z-order. Note that
  Redis is 0-based, but so are stack coordinates.

## Processes

* `Processes.count` counts the number of processes observed
* `Procseses:<id>` is the prefix for a particlar process
  * `:xc:<z>` is the x-center in the z-th plane
  * `:yc:<z>` is the y-center in the z-th plane
  * `:r` is the red color index
  * `:g` is the green color index
  * `:b` is the blue color index
  * `:xmin` is the minimim x value observed
  * `:xmax` is the maximum x value observed
  * `:ymin`, `:ymax`, `:zmin`, `:zmax`

## Colors 

Colors are the reverse process index, pixel color to process id

* `Colors:<r>:<g>:<b>:process` is the process id for the color (`r`, `g`, `b`)
