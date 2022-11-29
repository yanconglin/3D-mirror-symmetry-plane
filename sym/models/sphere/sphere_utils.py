import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.autograd import gradcheck
from torch.nn.modules.utils import _pair
import scipy.io as sio
import random
import numpy as np
from scipy import ndimage
import matplotlib.pyplot as plt
import math
import time
import os
import collections.abc
container_abcs = collections.abc
from itertools import repeat
import scipy.io as sio
import numpy.linalg as LA
import scipy.spatial.distance as scipy_spatial_dist



def intx(x):
    return(int(x[0]), int(x[1]))

def cos_cdis(x, y, semi_sphere=False):
    # input: x: mxp, y: nxp
    # output: y, mxn
    # https://docs.scipy.org/doc/scipy/reference/generated/scipy.spatial.distance.cdist.html#scipy.spatial.distance.cdist
    ### compute cosine distance
    ### scipy: same 0, opposite 2, orthorgonal 1, dist = 1-AB/(|A||B|)
    dist_cos = scipy_spatial_dist.cdist(x, y, 'cosine')  # num_points_ x num_points
    # ### map to: same 1, opposite -1, orthorgonal 0, dist = AB/(|A||B|)
    dist_cos *= -1.0
    dist_cos += 1.0

    if semi_sphere is True: dist_cos = np.abs(dist_cos) #  dist = abs|AB/(|A||B|)|
    dist_cos_arc = np.arccos(dist_cos)
    return dist_cos_arc

def catersian_to_sphere(xyz):
    #  input: xyz, nx3, in the gaussian_catersian coordinate
    #  output: angles, (alpha, beta), nx2, in the gaussian sphere coordinate
    #  beta: elevation; alpha: azimuth.
    ### norm = [sin(alpha)cos(beta), sin(beta), cos(alpha)cos(beta)]
    num_points = len(xyz)
    angle = np.zeros((num_points,2))
    angle[:,1] = np.arcsin(xyz[:,1])
    inner = xyz[:,0] / np.cos(angle[:,1])
    inner = np.clip(inner, a_min=-1.0, a_max=1.0)
    # inner = np.minimum(inner, 1)
    # inner = np.maximum(inner, -1)
    angle[:,0] = np.arcsin(inner)
    # print("angle", angle)
    return angle


def sphere_to_catesian(angles):
    #  input: angles (alphas, betas), nx2, in the gasussian sphere coordinate
    #  output: xyz (x,y,z), nx3, in the gaussian_catersian coordinate
    #  beta: elevation; alpha: azimuth.
    ### n = [sin(alpha)cos(beta), sin(beta), cos(alpha)cos(beta)]
    num_points = len(angles)
    xyz = np.zeros((num_points,3))
    xyz[:,0] = np.sin(angles[:,0]) * np.cos(angles[:,1])
    xyz[:,1] = np.sin(angles[:,1])
    xyz[:,2] = np.cos(angles[:,0]) * np.cos(angles[:,1])

    return xyz


# # # https://stackoverflow.com/questions/9600801/evenly-distributing-n-points-on-a-sphere/44164075
# # # pts = gold_spiral_sampling_patch(np.array([0, 0, 1]), alpha=np.pi/2, num_pts=4096)
def gold_spiral_sampling_patch(v, alpha, num_pts):
    v1 = orth(v)
    v2 = np.cross(v, v1)
    v, v1, v2 = v[:, None], v1[:, None], v2[:, None]
    # print('v, v1, v2', v, v1, v2)
    indices = np.arange(num_pts) + 0.66
    phi = np.arccos(1 + (math.cos(alpha) - 1) * indices / num_pts)
    theta = np.pi * (1 + 5 ** 0.5) * indices
    r = np.sin(phi)
    return (v * np.cos(phi) + r * (v1 * np.cos(theta) + v2 * np.sin(theta))).T


def orth(v):
    x, y, z = v
    o = np.array([0.0, -z, y] if abs(x) < abs(y) else [-z, 0.0, x])
    o /= LA.norm(o)
    return o


def w2S(w):
    S = np.eye(4)
    S[:3, :3] = np.eye(3) - 2 * np.outer(w, w) / np.sum(w ** 2)
    S[:3, 3] = -2 * w / np.sum(w ** 2)
    return S



def w2P(w):
    # p = np.eye(4)
    # p[:3, :3] = np.eye(3) - np.outer(w, w) / np.sum(w ** 2)
    # p[:3, 3] = - w / np.sum(w ** 2)
    P = np.zeros((4))
    P[:3] = w
    P[3] = 1.0
    return P / LA.norm(w)
