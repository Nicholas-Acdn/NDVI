#I got this code working shortly after starting the project
#So it was developed for visible light photos with no filter
#Then I started fooling around with double thresholding for the mask
#Bandpass filter will severely affect thresholding
#Background subtraction might have to be substituted instead

from plantcv import plantcv as pcv
import cv2
import numpy as np

#Define options for plantCV
class options:
    def __init__(self):
        self.image = "RGB3.jpg"
        self.debug = "print" #plot
        self.writeimg= False
        self.result = "."
        self.outdir = "/home/anorman/Documents/NikScripts/WorkingImages"


args = options()
pcv.params.debug = args.debug


#Reads in calibrated rgb and NIR images
rgb_img,rgb_path,rgb_filename = pcv.readimage(filename="RGB2.jpeg")
NIR_img, NIR_path, NIR_filename = pcv.readimage(filename="NIR2.jpeg")


#Converts and slices image into green-magenta channel and blue-yellow channel
green_magenta_img = pcv.rgb2gray_lab(rgb_img= rgb_img, channel='a')
blue_yellow_img =   pcv.rgb2gray_lab(rgb_img= rgb_img,channel='l')


#Thresholds both sliced photos, creating two binary masks of plant material
img_binary1 = pcv.threshold.binary(gray_img=green_magenta_img, threshold=125, max_value=250, object_type='dark')
img_binary2 = pcv.threshold.binary(gray_img=blue_yellow_img, threshold=142, max_value=250, object_type='dark')


#and operator.Combines the two masks, keeping only the pieces contained in both
combined_thresh = pcv.logical_and(img_binary1, img_binary2)


#Fills small objects in mask
fill_image = pcv.fill(bin_img=combined_thresh, size=20)


#Dilates mask
dilated = pcv.dilate(gray_img=fill_image, ksize=2, i=1)


#Uses mask to identify objects
id_objects, obj_hierarchy = pcv.find_objects(img=rgb_img, mask=dilated)
id_objects, obj_hierarchy = pcv.find_objects(img=NIR_img, mask=dilated)


#Crops photos using the same mask
cropped_rgb = pcv.apply_mask(img=rgb_img, mask=dilated,mask_color='black')
cropped_NIR = pcv.apply_mask(img=NIR_img, mask=dilated, mask_color='black')


#Numpy slicing: Blue -[:,:,0] Green-[:,:,1]Red-[:,:,2] to create individual color channel photos
cropped_red_rgb = cropped_rgb[:,:,2]
cropped_red_NIR = cropped_NIR[:,:,2]


#Initializes NDVI value matrix
NDVI_data = []


#Goes through each pixel of rgb and NIR photos and does NDVI calculation for each
#Appends each pixel value in a single dimension matrix

for x in range(0,len(cropped_rgb)):

    for y in range(0,len(cropped_rgb[0])):

        p = float(cropped_red_NIR[x,y]) - float(cropped_red_rgb[x,y])
        q = float(cropped_red_NIR[x,y]) + float(cropped_red_rgb[x,y])

        #In case red and NIR are both 0 (0/0 division), sets ndvi value to -10
        if p == 0 and q == 0:
            NDVI_data.append(-10)

        else:
            NDVI_data.append(p/q)

#The ndvi matrix contains values ranging from -1 to 1 (plus safety values of -10)
#To create a greyscale photo out of this, we need to convert to a scale from 0-256


#Initialize ndvi average variables and greyscale photo matrix
k = 0
NDVI_sum = 0
grey_NDVI = []


#Sifts through NDVI data matrix, checking for -10 condition
#sums data values and counts pixels
#Converts into greyscale photo values and appends to matrix

for i in range(0,len(NDVI_data)):
    if NDVI_data[i] != -10:
        k += 1
        NDVI_sum += NDVI_data[i]
        grey_NDVI.append(((NDVI_data[i])+1)*127.5)
    else:
        grey_NDVI.append(0)


#Calculates average NDVI using NDVI sum and pixel count
NDVI_average = NDVI_sum/float(k)


print (NDVI_average)


#Reshapes greyscale NDVI photo into a real photo format
pseudocolor = np.reshape(grey_NDVI,(len(cropped_red_rgb),len(cropped_red_rgb[0])))


#Creates a pseudocolored photo of NDVI values
pcv.visualize.pseudocolor(pseudocolor, obj=None, mask=None, background="image", cmap='gist_rainbow', min_value=0, max_value=255,axes=True, colorbar=True, obj_padding=None)
