#!/usr/bin/env python

from array import array
from gimpfu import *
import os.path

ELASTIC_TATTOO = 991
CONTENT_TATTOO = 992

pdb = gimp.pdb

def android_ninepatch_prepare( image, current_layer ):
    """
    Prepare an image to be an android 9-patch image.

    This creates two layers "9-elastic" and "9-content" on which the
    user draws the elastic and content regions of the eventual 9-patch
    PNG. Since the regions mask off content and elastic regions, they
    are more durable against resizing, and using the function
    android_ninepatch_render will perform all the steps to change
    these regions into the border annotations of a 9-patch PNG.
    """
    width = image.width
    height = image.height

    # Create the new layers
    elastic = gimp.Layer( image, "9-elastic", width, height,
                          RGBA_IMAGE, 33, 0 )
    content = gimp.Layer( image, "9-content", width, height,
                          RGBA_IMAGE, 33, 0 )

    # Add their tatoos
    elastic.tattoo = ELASTIC_TATTOO
    content.tattoo = CONTENT_TATTOO

    # Then place the layers into the image
    pdb.gimp_undo_push_group_start( image )
    image.add_layer( elastic, -1 )
    image.add_layer( content, -1 )
    pdb.gimp_undo_push_group_end( image )

def get_alpha_pixels( layer ):
    reg = layer.get_pixel_rgn( 0, 0, layer.width, layer.height )
    arr = array( 'B', reg[ 0:layer.width, 0:layer.height ] )
    return arr[ 3::4 ] # Return only the alpha portions

def android_ninepatch_render( image, current_layer ):
    """
    Render a 9-patch border.

    The image must first have been prepared with the function
    android_ninepatch_prepare, and the content and elastic areas
    defined.  This will then increase the canvas size by a single
    pixel in every dimension, add a layer, and draw the 9-patch PNG
    annotations necessary to make the image (after flattening) a true
    9-patch PNG.

    This may safely be called on unprepared images, but will have no
    effect.
    """
    if not is_ninepatch( image ):
        # Nothing to be done
        return

    imageWidth = image.width + 2
    imageHeight = image.height + 2

    elastic = image.get_layer_by_tattoo( ELASTIC_TATTOO )
    content = image.get_layer_by_tattoo( CONTENT_TATTOO )

    # Bundle everything into a single undo
    pdb.gimp_undo_push_group_start( image )

    # Create the transparent border layer
    image.resize( imageWidth, imageHeight, 1, 1 )
    border = gimp.Layer( image, "9-patch border",
                         imageWidth, imageHeight,
                         RGBA_IMAGE, 100, 0 )
    border.tattoo = 990
    image.add_layer( border, -1 )

    # Select the brush useful for drawing the border
    pdb.gimp_brushes_set_brush( "1. Pixel" )
    pdb.gimp_context_set_brush_size( 1 )
    pdb.gimp_context_set_foreground( (0,0,0) )
    pdb.gimp_context_set_opacity( 100 )

    # Use pixel regions to brute-force opacities
    target = border.get_pixel_rgn( 0, 0, image.width, image.height )
    targetArray = array( 'B', target[ 0:target.width, 0:target.height ] )

    eArray = get_alpha_pixels( elastic )
    cArray = get_alpha_pixels( content )

    # Coordinate parts for the border
    (et, el) = elastic.offsets;
    (ct, cl) = content.offsets;
    top = 0;
    left = 0;
    bottom = imageHeight -1;
    right = imageWidth -1;

    # Mark left (elastic) side
    for row in xrange( 0, elastic.height ):
        if any( a > 0 for a in eArray[ (row * elastic.width) :
                                       ((row + 1) * elastic.width) ] ):
            pdb.gimp_pencil( border, 2, (left, row + et) )

    # Mark right (content) side
    for row in xrange( 0, content.height ):
        if any( a > 0 for a in cArray[ (row * content.width) :
                                       ((row+1) * content.width) ] ):
            pdb.gimp_pencil( border, 2, (right, row + ct) )

    # Mark top (elastic) side
    for col in xrange( 0, elastic.width ):
        if any( a > 0 for a in eArray[ col::elastic.width ] ):
            pdb.gimp_pencil( border, 2, (col + el, top) )

    # Mark bottom (content) side
    for col in xrange( 0, content.width ):
        if any( a > 0 for a in cArray[ col::elastic.width ] ):
            pdb.gimp_pencil( border, 2, (col + cl, bottom ) )

    elastic.visible = False
    content.visible = False

    pdb.gimp_undo_push_group_end( image )

def is_ninepatch( image ):
    elastic = image.get_layer_by_tattoo( ELASTIC_TATTOO )
    content = image.get_layer_by_tattoo( CONTENT_TATTOO )

    return (elastic is not None) and (content is not None)

def mk9filename( image ):
    filename = pdb.gimp_image_get_filename( image )
    filename = os.path.basename( filename )

    if( is_ninepatch( image ) ):
        ext = ".9.png"
    else:
        ext = ".png"

    return os.path.splitext( filename )[0] + ext

def android_ninepatch_save( image, layer, directory, scaleFactor ):
    """
    Render and save a 9-patch PNG.
    """

    # Figure out what our filenames should be (temporary, and later)
    newFile = pdb.gimp_temp_name( "xcf" )
    pngFile = os.path.join( directory, mk9filename( image ) )
    #pngFile.mkdirs()

    # Save (and then load) the temporary file
    pdb.gimp_xcf_save( 0, image, layer, newFile, newFile )
    newImage = pdb.gimp_xcf_load( 0, newFile, newFile )

    # Scale the image then render the 9-patch
    pdb.gimp_image_scale_full( newImage,
                               scaleFactor * image.width,
                               scaleFactor * image.height,
                               INTERPOLATION_CUBIC )
    android_ninepatch_render( newImage, None )

    # Create a new layer with all layers merged
    resultLayer = pdb.gimp_image_merge_visible_layers( newImage, EXPAND_AS_NECESSARY )

    # Now export to PNG, and then delete the image
    pdb.file_png_save2( newImage,
                        resultLayer, pngFile, pngFile,
                        0, 9, 0, 0, 0, 0, 0, 0, 0 )
    pdb.gimp_image_delete( newImage )

def mkdirs( path ):
    try:
        os.makedirs( path )
    except: pass

def android_save_resolutions( image, layer, directory ):
    """
    Save an image in many resolutions to a project.

    This takes a project directory as a parameter, and saves the image
    as low, medium, and high densities (scaled appropriately, of
    course) to the appropriate drawable directories within the project.
    """
    resolution = image.resolution[0]

    print "Saving all resolutions to %s" % directory

    res = os.path.join( directory, 'res' )
    mdpi = os.path.join( res, 'drawable-mdpi' )
    hdpi = os.path.join( res, 'drawable-hdpi' )
    xhdpi = os.path.join( res, 'drawable-xhdpi' )

    mkdirs( mdpi )
    mkdirs( hdpi )
    mkdirs( xhdpi )

    android_ninepatch_save( image, layer, mdpi, 160 / resolution )
    android_ninepatch_save( image, layer, hdpi, 240 / resolution )
    android_ninepatch_save( image, layer, xhdpi, 320 / resolution )

register(
    "android-ninepatch-prepare",
    "Prepare image as 9-patch",
    android_ninepatch_prepare.__doc__.strip(),
    "Greyson Fischer",
    "Copyright 2011-2014, Greyson Fischer",
    "October 16, 2014",
    "<Image>/Image/Android/Prepare 9-patch",
    "RGBA",
    [],
    [],
    android_ninepatch_prepare )

register(
    "android-ninepatch-render",
    "Render image as 9-patch",
    android_ninepatch_render.__doc__.strip(),
    "Greyson Fischer",
    "Copyright 2011-2014, Greyson Fischer",
    "October 16, 2014",
    "<Image>/Image/Android/Render 9-patch",
    "RGBA",
    [],
    [],
    android_ninepatch_render )

register(
    "android-save-resolutions",
    "Save an image in {m,h,xh}dpi resolutions to a project",
    android_save_resolutions.__doc__.strip(),
    "Greyson Fischer",
    "Copyright 2011-2014, Greyson Fischer",
    "October 16, 2014",
    "<Image>/Image/Android/Save to project",
    "RGBA",
    [ (PF_DIRNAME, "directory", "Project directory", "/tmp") ],
    [],
    android_save_resolutions )

main()

__author__ = "Greyson Fischer <gfischer@foosoft.us>"
__copyright__ = "Copyright 2012 Greyson Fischer"
