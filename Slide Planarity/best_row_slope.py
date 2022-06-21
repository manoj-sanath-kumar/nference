import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import statistics
import numpy as np
import warnings
import sqlite3
from scipy.stats import norm
import math
import cv2
import os
import json
import time
import sys
from numpy.lib.function_base import append
import xlsxwriter
import matplotlib.pyplot as plt
from os.path import join
from mpl_toolkits.mplot3d import Axes3D
from collections import deque
from scipy.signal import argrelextrema
import glob

##Computing least-squares solution to equation Ax = b
def plane_fitting_max_point(x,y,z):
    y = y
    x = x
    z = z
    num_points = len(x)
    z_step_size = 1.875

#     ax = plt.subplot(111, projection='3d')
#     ax.scatter(x, y, z, color='b')

    tmp_A = []
    tmp_b = []
    for i in range(len(x)):
        tmp_A.append([x[i], y[i], 1])
        tmp_b.append(z[i])

    b = np.matrix(tmp_b).T
    A = np.matrix(tmp_A)

    from scipy.linalg import lstsq
    fit, residual, rnk, s = lstsq(A, b)
    errors =  A * fit - b
    plane_z = A * fit
    
    index_min_plane_z = np.argmin(plane_z)
    index_max_plane_z = np.argmax(plane_z)

    x_z_min_in_microns = x[index_min_plane_z]
    x_z_max_in_microns = x[index_max_plane_z]
    y_z_min_in_microns = y[index_min_plane_z]
    y_z_max_in_microns = y[index_max_plane_z]

    max_plane_z_diff  = max(plane_z) - min(plane_z)
    
    slope = (max(plane_z) - min(plane_z))/(math.dist([x_z_max_in_microns, y_z_max_in_microns], [x_z_min_in_microns, y_z_min_in_microns]))
#     print("Slope: ", slope)
#     print("solution: %f x + %f y + %f = z" % (fit[0], fit[1], fit[2]))
    return(slope)

df = pd.DataFrame(columns = ['slide_name', 'best_row_slope'])
for filename in sorted(glob.glob("/home/adminspin/Desktop/Planarity/*/*.db",recursive=True)):
    try:
        file = filename
        lst = []
        name = file.split('/')[-1].split('.')[0]
        lst.append(name)
        conn = sqlite3.connect(file)
        c = conn.cursor()
        
        query = "select aoi_name, aoi_x_mic, aoi_y_mic, aoi_row_idx, aoi_col_idx, a.best_z , best_idx, stack_size, focus_metric from aoi as a join grid_info as b where a.aoi_row_idx = b.best_row_to_start and a.best_idx > -1 and b.grid_name = 'grid_1'"
        c.execute(query)
        aoi_info = c.fetchall()
        acc = pd.DataFrame(aoi_info)
        acc.rename(columns = {0:'aoi_name',1:'aoi_x_mic',2:'aoi_y_mic',3:'aoi_row_idx',4:'aoi_col_idx',5:'best_z',6:'best_idx',
                            7:'stack_size',8:'focus_metric'}, inplace = True)
        acc

        acc = acc[acc['best_z'] > -1]
        acc
        x = acc['aoi_x_mic'].tolist()
        y = acc['aoi_y_mic'].tolist()
        z = acc['best_z'].tolist()
        slope = plane_fitting_max_point(x,y,z).tolist()[0][0]
        lst.append(slope)

        df.loc[len(df)] = lst
    except: 
        continue
df.to_excel('/home/adminspin/Desktop/best_row_slope.xlsx')


