import sys
import os
import glob
import tqdm
from PIL import Image
import cv2
import numpy
import random
import itertools

def create_all_masks(imdir):
    """
    Creates masks of all images and places them in a separate masks directory
    Mostly used for testing purposes
    
    Args:
    imdir: path to directory of images with transparent backgrounds (path does not end with a '/')
    
    Returns:
    Nothing
    """

    print('Creating Masks from: {}'.format(imdir))
    IMAGE_PATHS = glob.glob(imdir + '/**/*png', recursive=True)

    try:
        os.stat(imdir + '../masks/')    
    except:
        os.makedirs(imdir + '../masks/')

    #New directory of masks
    mask_directory = os.path.abspath(os.path.join(imdir, '../masks/'))

    for image_path in IMAGE_PATHS:
        class_name = image_path.split('/')[-2]

        #Set iteration as 255 since I will count transparency using iteration number
        #This method is just to test the mask method so iteration number doesn't really matter here
        create_mask(image_path, mask_directory, class_name, 255)

def create_mask(image_path, result_path, class_num, iteration):
    """
    Creates mask of a single image and places it in a separate masks directory.
    Notes: Could not create a 2 channel image unless in the format of JPEG 2000, so created a PNG image
    with 4 channels where I only modified the first 2 channels:
        Class_number is in the first channel
        Object iteration is in the second channel
    
    Args:
    image_path: path to image with transparent background
    result_path: path to directory where to save mask image
    class_name: name of image class (type)
    iteration: iteration number of this specific instance

    Returns:
    path to new image
    """
    image_name = image_path.split('/')[-1]

    original_image = Image.open(image_path)
    image = original_image.convert('RGBA')

    pixel_data = numpy.array(image)

    #If image has alpha channel for transparency.
    #If it does, convert transparent pixels to black and fully transparent
    #And convert non-transparent pixels to white and fully opaque
    if image.mode == 'RGBA':
        for y in range(pixel_data.shape[0]):
            for x in range(pixel_data.shape[1]):
                if pixel_data[y][x][3] == 0:
                    pixel_data[y][x] = [0, 0, 0, 0]
                else:
                    pixel_data[y][x] = [class_num, iteration, 0, 255]

    try:
        os.stat(result_path)
    
    except:
        os.makedirs(result_path)

    mask = Image.fromarray(pixel_data)
    path = result_path + '/{}'.format(image_name)
    mask.save(path)

    return path

def splice_img(realimg, fakeimgs, imgmasks):
    """
    Splice images of a number of synthetic images into a real image with random orientation. 
    At the same time, splice the mask into a new  equivalent mask image with 2 channels:
        - Channel 1: Class of image (type of flag)
        - Channel 2: Iteration of image

    Args:
    realimg: path to a single real image
    fakeimgs: list of paths to a number of synthetic images
    imgmasks: list of paths to corresponding number of image masks
    
    Returns:
    Path to directory of spliced images and path to directory of spliced mask
    """

    image_name = realimg.split('/')[-1]
    name = image_name.split('.')[0]

    real_image_directory = os.path.abspath(os.path.join(realimg, os.pardir)) 
    image_directory = os.path.abspath(os.path.join(real_image_directory, os.pardir))
    
    #Open real image
    real_image = Image.open(realimg)
    real_image = real_image.copy()
    rwidth, rheight = real_image.size

    #Create new mask image
    new_mask = Image.new('RGBA', (rwidth, rheight), (0, 0, 0, 0))

    #For loop will iterate through both lists in parallel 
    for fakeimg, imgmask in zip(fakeimgs, imgmasks):
        #Splice synthetic images into a real image
        fake_image = Image.open(fakeimg)
        fake_image.convert('RGBA')

        fwidth, fheight = fake_image.size

        #Create numbers to randomly translate, rotate, and scale fake_image without 
        #splicing it outside the bounds of the real image
        random_theta = random.randint(0, 359)
        
        #Sets the max scaling factor for synthetic image. I divided it by 2 to not have an image that big
        #Tune these numbers to not have a synthetic image scaled too small or too large
        maxscale = min((rheight/fheight)/2, (rwidth/fwidth)/2)
        random_scale = random.uniform(maxscale/4, maxscale)

        randomx = random.randint(0, int(rwidth - fwidth * random_scale))
        randomy = random.randint(0, int(rheight - fheight * random_scale))

        rot_image = fake_image.rotate(random_theta).resize((int(fwidth * random_scale), int(fheight * random_scale)))
        real_image.paste(rot_image, (randomx, randomy), rot_image)

        #Create mask image with same translation, rotation, scaling as spliced image
        mask_image = Image.open(imgmask)
        mask_image.convert('RGBA')
        
        rotated_mask = mask_image.rotate(random_theta).resize((int(fwidth * random_scale), int(fheight * random_scale)))
        new_mask.paste(rotated_mask, (randomx, randomy), rot_image)
        
    try:
        os.stat(image_directory + '/spliced_imgs/')
    
    except:
        os.makedirs(image_directory + '/spliced_imgs/')

    real_image.save(image_directory + '/spliced_imgs/{}'.format(image_name))

    try:
        os.stat(image_directory + '/spliced_masks/')
    
    except:
        os.makedirs(image_directory + '/spliced_masks/')

    new_mask.save(image_directory + '/spliced_masks/{}.png'.format(name))

def splice_all(imdir):
    """
    Run splice_img on all images. 
    Will edit this later to allow splice_all to splice a random list of fake_images into the
    real image and do the same for the corresponding masks. 

    Args:
    imdir: directory containing all images (real, synthetic, masks, spliced images)

    Returns:
    Path to directory of spliced images and path to directory of spliced mask
    """

    REAL_IMAGE_PATHS = glob.glob(imdir + 'real_imgs/**/*jpg', recursive=True) 
    FAKE_IMAGE_PATHS = glob.glob(imdir + 'flag_imgs/**/*png', recursive=True)

    mask_image_path = imdir + 'masks'
    NUMBER_OF_FAKE_IMAGES = 2

    print('Splicing Images')
    for real_image in tqdm.tqdm(REAL_IMAGE_PATHS):

        #Keeps track of number of synthetic flags in real image
        AN_COUNT = 0
        IIIP_COUNT = 0
        IC_COUNT = 0
        OR_COUNT = 0
        Others = 0
        count = 0

        #Creates random sample of images from all the flags
        fake_images = random.sample(FAKE_IMAGE_PATHS, NUMBER_OF_FAKE_IMAGES)
        mask_images = []
        
        #Creates random sample of masks (new images) from corresponding flag sample
        print('Creating Masks')
        for fake_image in tqdm.tqdm(fake_images):

            imgname = fake_image.split('/')[-1]
            class_name = fake_image.split('/')[-2]

            if class_name == 'Aryan Nations':
                class_num = 1
                AN_COUNT += 1
                count = AN_COUNT
            elif class_name == 'III Percenters':
                class_num = 2
                IIIP_COUNT += 1
                count = IIIP_COUNT
            elif class_name == 'Iron Cross':
                class_num = 3
                IC_COUNT += 1
                count = IC_COUNT
            elif class_name == 'Odal Rune':
                class_num = 4
                OR_COUNT += 1
                count = OR_COUNT
            else:
                class_num = 5
                OTHERS += 1
                count = OTHERS

            mask_images.append(create_mask(fake_image, mask_image_path, class_num, count)) 
        
        splice_img(real_image, fake_images, mask_images)

def main():
    path = 'data/'

    splice_all(path)


if __name__ == "__main__":
    main()
