This code was written for a research project at Columbia University's DVMM Lab in conjunction with Columbia University's School of Journalism. The end goal is to create an app that would aid journalists in detecting the symbols identifying different alt-right and political groups using machine learning. This code was specifically used to splice synthetic images of symbols into real photos (randomly) to train the machine learning modeles due to the lack of royalty free real images of these symbols. The photos included in this repository deepict possibly offensive images. 

To run code, go to image_splicing directory and run: python image_splice.py

For images to be spliced, have a directory containing 2 subdirectories:
        1. flag_imgs: synthetic flag images to splice into real image
        2. real_imgs: Real images to splice flag images into

The result will be created in the data folder with 3 new subdirectories:
        1. masks: masks of individual synthetic flags
        2. splice_imgs: Real images with spliced flags
        3. splice_masks: Masks for the corresponding spliced real image

To change this, change image and directory paths in the code.

In line 132: change maximum and minimum scaling numbers to preference
