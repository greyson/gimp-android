GIMP Plugin for Android
=======================

When developing for Android, many resolutions may be needed (or
required) to take advantage of the screen of the device on which the
application is running.

The GIMP plugin for Android helps with standard and 9-patch pixel
density resolution independence by handling scaling issues
sufficiently for most application purposes.

Annotation of 9-Patch Images
----------------------------

9-patch is an ingenious means of marking elastic and content zones of
a normal PNG using a 1-pixel wide transparent border.  Unfortunately,
this border may only be 1 pixel wide regardless of the size of the
image, and therefore cannot be included in an image before scaling.

The GIMP plugin allows annotation of a GIMP-native RGBA image using
two layers for the elastic and content regions. The layers must be
created by using the *Prepare 9-patch* menu option from this
plugin. They are fully transparent, semi-opaque layers into which the
content and elastic regions sholud be defined by non-transparent
rectangles on their respective layers.

The rectangles will properly scale with the image, allowing a single
source image to be used to make fully-compliant 9-patch images in
several resolutions.

### Elastic layer

In the normal 9-patch, the elastic region of an image is defined by
the non-transparent stripes on the left and top border of the
image.  When the image is used in resources, the elastic region will
be allowed to stretch to make the image fit any area larger than its
original self.

The layer created by *Prepare 9-patch* is called `9-elastic`. Fill a
non-transparent rectangle somewhere over the image (in the `9-elastic`
layer). The horizontal and vertical elastic regions are defined by
this rectangle.

### Content layer

In the normal 9-patch, the content region of an image is defined by
the intersection of stripes extending from the non-transparent pixels
on the bottom and right borders of the image.  When the image is used
as a background drawable, the padding of the contents is adjusted to
ensure that the non-content area of the image is visible outside the
content of the `View` for which the image is the background.

The layer created by this plugin's *Prepare 9-patch* is called
`9-content`. Fill a non-transparent rectangle in this layer that
overlays the desired content area of the image.

Resolution independence
-----------------------

This plugin uses the `X` and `Y` resolution -- not pixel density,
rather the second set of numbers in the "Scale Image" dialog -- to
determine how to scale the image into the density-specific project
folders:

* `drawable-ldpi` at a resolution of 120
* `drawable-mdpi` at a resolution of 160
* `drawable-hdpi` at a resolution of 240

I recommend using a resolution of 480 for all images. 480 is the least
common multiple of all three resolutions, and therefore scales without
needing antialiasing of any kind.

Menu items added
----------------

All menu items presented by this plugin are under the `/Image/Android`
menu.

* Prepare 9-patch

  Prepares an image for 9-patch (resolution independent) annotation by
  adding the content and elastic layers.

* Render 9-patch

  Render an 9-patch (resolution independent) annotated image directly
  to a 9-patch, without further scaling. This will add the 1-pixel
  border, draw the non-transparent strips along this border
  representing the opaque area of the elastic and content layers, and
  finally hide the annotation layers themselves.

* Save to project

  Prompts for a project to which to save the images; uses the basename
  of the current image's filename, scales and saves PNG each of the
  `res/drawable-*/$basename.png`.  If the image has 9-patch annotation
  layers, then it is instead saved to `res/drawable-*/$basename.9.png`
  after the 9-patch has been rendered at each resolution.
