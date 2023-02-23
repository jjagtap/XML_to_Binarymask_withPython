# XML_to_Binarymask_withPython
This script helps to create binary mask files from XML based on the color of annotation. If you want to change the color of annotation, refer to another code in my repository for XML modification.

## Provide the folder paths:
xml_path= '.../Test_xml_path/' <br />
file_path = r".../Test_svsfiles/" <br />
mask_output =r".../Mak_out" <br />

dict_mask =get_points_base(w,"yellow",custom_colors=[]) # selected "yellow" color to extract mask of it

## required python library:
import openslide <br />
from WSI_handling import wsi <br />
import os <br />
import numpy as np <br />
import matplotlib.pyplot as plt <br />
import xml.etree.ElementTree as ET <br />
import numpy as np <br />

from pathlib import Path <br />
from shapely.geometry import Polygon, MultiPolygon <br />
from shapely.strtree import STRtree  <br />
import shapely.affinity  <br />
import rasterio.features   <br />
import cv2  <br />
from tqdm import *   <br />
from skimage.util import view_as_blocks  <br />
import gc  <br />

        
