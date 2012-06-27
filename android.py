#!/usr/bin/env python2

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
    image.add_layer( elastic, -1 )
    image.add_layer( content, -1 )

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
    imageWidth = image.width + 2
    imageHeight = image.height + 2

    elastic = image.get_layer_by_tattoo( ELASTIC_TATTOO )
    content = image.get_layer_by_tattoo( CONTENT_TATTOO )

    if( elastic is None or content is None ):
        # No work to be done
        return


    # Bundle everything into a single undo
    image.disable_undo()
    # pdb.gimp_undo_push_group_start( image )
    # pdb.gimp_context_push()

    # Create the transparent border layer
    image.resize( imageWidth, imageHeight, 1, 1 )
    border = gimp.Layer( image, "9-patch border",
                         imageWidth, imageHeight,
                         RGBA_IMAGE, 100, 0 )
    border.tattoo = 990
    image.add_layer( border, -1 )

    # Select the brush useful for drawing the border
    pdb.gimp_brushes_set_brush( "Circle (01)" )
    pdb.gimp_context_set_foreground( (0,0,0) )
    pdb.gimp_context_set_opacity( 100 )

    # Grab the dimensions of the elastic layer
    pdb.gimp_selection_layer_alpha( elastic )
    sel = pdb.gimp_selection_bounds( image )
    pdb.gimp_selection_clear( image )

    # Draw the top and left 9-patch borders
    top = left = 0
    pdb.gimp_pencil( border, 4,
                     (left, sel[2], left, sel[4] -1 ) )
    pdb.gimp_pencil( border, 4,
                     (sel[1], top, sel[3] - 1, top ) )

    # Grab the dimensions of the content layer
    pdb.gimp_selection_layer_alpha( content )
    sel = pdb.gimp_selection_bounds( image )
    pdb.gimp_selection_clear( image )

    # Now draw the bottom and right 9-patch borders
    right = imageWidth - 1
    bottom = imageHeight - 1
    pdb.gimp_pencil( border, 4,
                     (right, sel[2], right, sel[4] - 1) )
    pdb.gimp_pencil( border, 4,
                     (sel[1], bottom, sel[3] - 1, bottom) )

    # pdb.gimp_context_pop()
    # pdb.gimp_undo_push_group_end( image )
    image.enable_undo()

def mk9filename( image ):
    filename = pdb.gimp_image_get_filename( image )
    filename = os.path.basename( filename )
    return os.path.splitext( filename )[0] + ".9.png"

def android_ninepatch_save( image, layer, directory, scaleFactor ):
    """
    Render and save a 9-patch PNG.
    """

    print "Saving %s scaled by %f" % (directory, scaleFactor)
    print "Will use filename %s" % mk9filename( image )

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

    ### TODO: hide 9-elastic and 9-content

    # Create a new layer with all layers merged
    resultLayer = pdb.gimp_image_merge_visible_layers( newImage, EXPAND_AS_NECESSARY )

    # Now export to PNG, and then delete the image
    pdb.file_png_save2( newImage,
                        resultLayer, pngFile, pngFile,
                        0, 9, 0, 0, 0, 0, 0, 0, 0 )
    pdb.gimp_image_delete( newImage )

def android_save_resolutions( image, layer, directory ):
    """
    Save an image in many resolutions to a project.

    This takes a project directory as a parameter, and saves the image
    as low, medium, and high densities (scaled appropriately, of
    course) to the appropriate drawable directories within the project.
    """
    resolution = image.resolution[0]

    print "Saving all resolutions to %s" % directory

    android_ninepatch_save( image, layer,
                            os.path.join( directory, 'res', 'drawable-ldpi' ),
                            120 / resolution )
    android_ninepatch_save( image, layer,
                            os.path.join( directory, 'res', 'drawable-mdpi' ),
                            160 / resolution )
    android_ninepatch_save( image, layer,
                            os.path.join( directory, 'res', 'drawable-hdpi' ),
                            240 / resolution )

register(
    "android-ninepatch-prepare",
    "Prepare image as 9-patch",
    android_ninepatch_prepare.__doc__.strip(),
    "Greyson Fischer",
    "Copyright 2011-2012, Greyson Fischer",
    "June 26, 2012",
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
    "Copyright 2011-2012, Greyson Fischer",
    "June 26, 2012",
    "<Image>/Image/Android/Render 9-patch",
    "RGBA",
    [],
    [],
    android_ninepatch_render )

register(
    "android-save-resolutions",
    "Save an image in [lmh]dpi resolutions to a project",
    android_save_resolutions.__doc__.strip(),
    "Greyson Fischer",
    "Copyright 2011-2012, Greyson Fischer",
    "June 26, 2012",
    "<Image>/Image/Android/Save to project",
    "RGBA",
    [ (PF_DIRNAME, "directory", "Project directory", "/tmp") ],
    [],
    android_save_resolutions )

main()
