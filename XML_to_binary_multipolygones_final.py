#!/usr/bin/env python
# coding: utf-8

# author: Jaidip Jagtap

file1 = open("cortex.txt", "a") # It writes the log of updates
# In[1]:


def color_ref_match_xml(colors_to_use,custom_colors):    
    """Given a string or list of strings corresponding to colors to use, returns the hexcodes of those colors"""

    color_ref = [(65535,1,'yellow'),(65280,2,'green'),(255,3,'red'),(16711680,4,'blue'),(16711808,5,'purple'),(np.nan,6,'other')] + custom_colors

    if colors_to_use is not None:

        if isinstance(colors_to_use,str):
            colors_to_use = colors_to_use.lower()
        else:
            colors_to_use = [color.lower() for color in colors_to_use]

        color_map = [c for c in color_ref if c[2] in colors_to_use]
    else:
        color_map = color_ref        

    return color_map


# In[2]:

def get_points_xml(wsi_object,colors_to_use,custom_colors): 
    """Given a set of annotation colors, parses the xml file to get those annotations as lists of verticies"""
    color_map = color_ref_match_xml(colors_to_use,custom_colors)    

    color_key = ''.join([k[2] for k in color_map])
    full_map = color_ref_match_xml(None,custom_colors)

    # create element tree object
    tree = ET.parse(wsi_object["annotation_fname"])

    # get root element
    root = tree.getroot()        

    map_idx = []
    points = []

    for annotation in root.findall('Annotation'):        
        line_color = int(annotation.get('LineColor'))  
        line_name=annotation.get('Name')
        
        mapped_idx = [item[1] for item in color_map if item[0] == line_color]

        if(not mapped_idx and not [item[1] for item in full_map if item[0] == line_color]):
            if('other' in [item[2] for item in color_map]):
                mapped_idx = [item[1] for item in color_map if item[2] == 'other']                    

        if(mapped_idx):
            if(isinstance(mapped_idx,list)):
                mapped_idx = mapped_idx[0]
            print(line_color, line_name)
            file1.write("\n")
            file1.write(line_name)
            for regions in annotation.findall('Regions'):
                for annCount, region in enumerate(regions.findall('Region')):                                
                    map_idx.append(mapped_idx)

                    for vertices in region.findall('Vertices'):
                        points.append([None] * len(vertices.findall('Vertex')))                    
                        for k, vertex in enumerate(vertices.findall('Vertex')):
                            points[-1][k] = (int(float(vertex.get('X'))), int(float(vertex.get('Y'))))                                                                            

    sort_order = [x[1] for x in color_map]
    new_order = []
    for x in sort_order:
        new_order.extend([index for index, v in enumerate(map_idx) if v == x])

    points = [points[x] for x in new_order]
    map_idx = [map_idx[x] for x in new_order]

    return points, map_idx


# In[7]:


def get_points_base(wsi_object,colors_to_use,custom_colors=[]):
    
    color_key = ''.join([k for k in colors_to_use])
    
    # we can store the points for this combination to speed up getting it later
    if color_key in wsi_object["stored_points"]:
        return wsi_object["stored_points"][color_key].copy()
    
#     Path(wsi_object['annotation_fname']).suffix == '.xml':
    points, map_idx = get_points_xml(wsi_object,colors_to_use,custom_colors)
            
#     if Path(wsi_object['annotation_fname']).suffix == '.json':
#         points, map_idx = get_points_json(wsi_object,colors_to_use)
        
    point_polys = []
    for point in points:
        if len(point) < 3:
            continue
        point_polys.append(Polygon(point))
    wsi_object["stored_points"][color_key] = []
    wsi_object["stored_points"][color_key] = {'points':points.copy(),'map_idx':map_idx.copy(), 'polygons': point_polys.copy(), 'STRtree': STRtree(point_polys)}
    
    return wsi_object['stored_points'][color_key].copy()


# In[4]:


import openslide
from WSI_handling import wsi
import os
import numpy as np
import matplotlib.pyplot as plt
import xml.etree.ElementTree as ET
import numpy as np

from pathlib import Path
from shapely.geometry import Polygon, MultiPolygon
from shapely.strtree import STRtree
import shapely.affinity
import rasterio.features
import cv2
from tqdm import *
from skimage.util import view_as_blocks
import gc

# In[16]:

xml_path= '.../Test_xml_path/'
file_path = r".../Test_svsfiles/"
mask_output =r".../Mak_out"

if not os.path.exists(mask_output):
    os.makedirs(mask_output)


subdir, dirs, files = os.walk(file_path).__next__()
files = [k for k in files if ".svs" in k]

for filename in tqdm(files):
    if 'png' not in filename:
        pre,ext=filename.rsplit('.svs', 1)
        fname= os.path.join(file_path,filename) #os.rename(renamee, pre + new_extension)
        xml_fname=os.path.join(xml_path,pre+'.xml')
        
        newfname_class = "%s/%s_medullamasknsg1dGT.png" % (mask_output, os.path.basename(filename)[0:filename.rfind('.')])#glomtuftmaskGT
        if os.path.exists(newfname_class):
            print(f"Skipping as output file exists: \t {filename}")
            continue        
        print(f"working on file: \t {filename}")
        cv2.imwrite(newfname_class, np.zeros(shape=(1, 1)))  

        w = wsi(fname,xml_fname)       
        
        # Get mask
        dict_mask =get_points_base(w,"yellow",custom_colors=[]) # selected yellow color to extract mask of it 
        
        # Check if more than 1 polygon, if there is combine all into 1 polygon         
        try:
            if len(dict_mask["polygons"]) > 1:
                mask_poly = MultiPolygon(dict_mask["polygons"])
            else:
                mask_poly = shapely.affinity.scale(dict_mask['polygons'][0])
        except ValueError:
            print('small blue color artifact in', filename)
            continue
        except IndexError:
            print('No such color annotation present', filename)
            os.remove(newfname_class)
            continue
        file1.write("\n")
        file1.write(filename) 
        
            
        # plt.plot(*mask_poly.exterior.xy) # work if single polygon
        # Convert mask to binary image
        mask = rasterio.features.rasterize([mask_poly], out_shape= (w["img_dims"][0][1],w["img_dims"][0][0]))
        # plt.figure();plt.imshow(mask*255,cmap="gray")
        
        cv2.imwrite(newfname_class,mask)
        #cv2.imwrite(r"Newpath" + os.sep + file[:-4] + "_mask.png",mask_tosave*255)
        #gc.collect()
file1.close()        
# %% 
                
# %%                

# In[ ]:



