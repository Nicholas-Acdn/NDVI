import numpy as np
import rawpy
import imageio
import csv
import exifread
import image
from pydng.core import RPICAM2DNG

#set image path

path = '/home/anorman/Documents/NikScripts/RAW_photos/test.jpg'

#open image and print photo parameters

with open(path,'rb') as img:
    tags = exifread.process_file(img)
    for tag in tags.keys():
        if tag not in ('JPEGThumbnail', 'TIFFThumbnail', 'Filename', 'EXIF MakerNote'):
            print ("Key: %s, value %s" % (tag, tags[tag]))

#Read raw photo and linearly demosiac

with rawpy.imread(path) as raw:

    rgb = raw.postprocess(gamma=(1,1), no_auto_bright=True, output_bps=16, demosaic_algorithm=0)

    #saves the linearly processed photo as tiff file
    imageio.imsave('/home/anorman/Documents/NikScripts/RAW_photos/Outputs/linear.tiff', rgb)


    #prints shape of photo
    print (np.shape(rgb))

    #slices linearly processed photo into three seperate photos each corresponding to color channels
    raw_red = rgb[:,:,0]
    raw_green= rgb[:,:,1]
    raw_blue = rgb[:,:,2]


    #initiallization of the parameters used for reflectance averages
    n = 0
    r= 0
    g = 0
    b = 0


    #Goes through each pixel of reflectance calibrator in sliced color photos
    #Adds each pixels color value and divides by number of pixels to get average of each color channel

    #actually x then y
    for y in range(1934,2033):
        for x in range(1308,1404):

                n += 1
                r += raw_red[x,y]
                g += raw_green[x,y]
                b += raw_blue[x,y]

    #In case a color channel has no values, program can continue
    #Useful for instances where a bandpass filter is used (our application)

    if g == 0:
        g = b
    if b == 0:
        b = r




    #Calibration averages matrix
    CA = [r/n,g/n,b/n]

    #White balance matrix using green channel as a reference to luminance
    #White balance is not actually needed for anything,just a nice reference
    WB_matrix = [CA[1]/CA[0],1,CA[1]/CA[2]]

    print(CA)
    print(WB_matrix)

    #Scales each pixel value in linearly processed photo by white balance matrix
    tiff_WB_photo = rgb*WB_matrix

    #Divides each pixel value by reflectance calibration matrix, then multiplies by objects color refelctances
    #Change of data type is to prevent overflow of max value
    #multiplied by 65535 to convert back to tiff's color scale
    tiff_reflect_photo = (rgb.astype(np.uint32)/CA)*65535*[0.182,0.192,0.194]

    #Any saturated color value (over 65535) gets set to 65535
    for u in range(0,len(tiff_reflect_photo)):
        for v in range(0,len(tiff_reflect_photo[1])):
            for w in range(0,3):
                if tiff_reflect_photo[u,v,w] >= 65535:
                    tiff_reflect_photo[u,v,w] = 65535


    #Converts back to original data type and saves photos for use in calculations
    imageio.imsave("/home/anorman/Documents/NikScripts/RAW_photos/Outputs/CE1_1_VIS_WB.tiff",tiff_WB_photo.astype(np.uint16))
    imageio.imsave("/home/anorman/Documents/NikScripts/RAW_photos/Outputs/CE1_1_VIS_ref.tiff",tiff_reflect_photo.astype(np.uint16))
