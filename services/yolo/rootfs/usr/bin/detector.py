#!/usr/bin/python

## system
import sys,os,pdb,json,codecs

###
## darknet.py from github.com/dcmartin/openyolo/tree/master/darknet/python/darknet.py
###

from ctypes import *
import math
import random

class BOX(Structure):
    _fields_ = [("x", c_float),
                ("y", c_float),
                ("w", c_float),
                ("h", c_float)]

class DETECTION(Structure):
    _fields_ = [("bbox", BOX),
                ("classes", c_int),
                ("prob", POINTER(c_float)),
                ("mask", POINTER(c_float)),
                ("objectness", c_float),
                ("sort_class", c_int)]


class IMAGE(Structure):
    _fields_ = [("w", c_int),
                ("h", c_int),
                ("c", c_int),
                ("data", POINTER(c_float))]

class METADATA(Structure):
    _fields_ = [("classes", c_int),
                ("names", POINTER(c_char_p))]

# find library
lib = CDLL(os.environ['DARKNET'] + "/libdarknet.so", RTLD_GLOBAL)

lib.network_width.argtypes = [c_void_p]
lib.network_width.restype = c_int
lib.network_height.argtypes = [c_void_p]
lib.network_height.restype = c_int

predict = lib.network_predict
predict.argtypes = [c_void_p, POINTER(c_float)]
predict.restype = POINTER(c_float)

set_gpu = lib.cuda_set_device
set_gpu.argtypes = [c_int]

make_image = lib.make_image
make_image.argtypes = [c_int, c_int, c_int]
make_image.restype = IMAGE

get_network_boxes = lib.get_network_boxes
get_network_boxes.argtypes = [c_void_p, c_int, c_int, c_float, c_float, POINTER(c_int), c_int, POINTER(c_int)]
get_network_boxes.restype = POINTER(DETECTION)

make_network_boxes = lib.make_network_boxes
make_network_boxes.argtypes = [c_void_p]
make_network_boxes.restype = POINTER(DETECTION)

free_detections = lib.free_detections
free_detections.argtypes = [POINTER(DETECTION), c_int]

free_ptrs = lib.free_ptrs
free_ptrs.argtypes = [POINTER(c_void_p), c_int]

network_predict = lib.network_predict
network_predict.argtypes = [c_void_p, POINTER(c_float)]

reset_rnn = lib.reset_rnn
reset_rnn.argtypes = [c_void_p]

load_net = lib.load_network
load_net.argtypes = [c_char_p, c_char_p, c_int]
load_net.restype = c_void_p

do_nms_obj = lib.do_nms_obj
do_nms_obj.argtypes = [POINTER(DETECTION), c_int, c_int, c_float]

do_nms_sort = lib.do_nms_sort
do_nms_sort.argtypes = [POINTER(DETECTION), c_int, c_int, c_float]

free_image = lib.free_image
free_image.argtypes = [IMAGE]

letterbox_image = lib.letterbox_image
letterbox_image.argtypes = [IMAGE, c_int, c_int]
letterbox_image.restype = IMAGE

load_meta = lib.get_metadata
lib.get_metadata.argtypes = [c_char_p]
lib.get_metadata.restype = METADATA

load_image = lib.load_image_color
load_image.argtypes = [c_char_p, c_int, c_int]
load_image.restype = IMAGE

rgbgr_image = lib.rgbgr_image
rgbgr_image.argtypes = [IMAGE]

predict_image = lib.network_predict_image
predict_image.argtypes = [c_void_p, IMAGE]
predict_image.restype = POINTER(c_float)


## DARKNET functions
def classify(net, meta, im):
    out = predict_image(net, im)
    res = []
    for i in range(meta.classes):
        res.append((meta.names[i], out[i]))
    res = sorted(res, key=lambda x: -x[1])
    return res

def detect(net, meta, image, thresh=.5, hier_thresh=.5, nms=.45):
    im = load_image(image, 0, 0)
    num = c_int(0)
    pnum = pointer(num)
    predict_image(net, im)
    dets = get_network_boxes(net, im.w, im.h, thresh, hier_thresh, None, 0, pnum)
    num = pnum[0]
    if (nms): do_nms_obj(dets, num, meta.classes, nms);

    res = []
    for j in range(num):
        for i in range(meta.classes):
            if dets[j].prob[i] > 0:
                b = dets[j].bbox
                res.append((meta.names[i], dets[j].prob[i], (b.x, b.y, b.w, b.h)))
    res = sorted(res, key=lambda x: -x[1])
    free_image(im)
    free_detections(dets, num)
    return res
    
## input
narg = len(sys.argv)

if narg > 1:
  filename = sys.argv[1]
else:
  filename = "data/horses.jpg"

if narg > 2:
  threshold = float(sys.argv[2])
else:
  threshold = 0.5

if narg > 3:
  cfg = sys.argv[3]
  config = "manual"
else:
  config = "tiny-v2"

if narg > 4:
  weight = sys.argv[4]
  config = "manual"
else:
  config = cfg

if narg > 5:
  data = sys.argv[5]
  config = "manual"
else:
  config = cfg

if config == "tiny-v2" or config == "tiny":
  cfg = os.environ['DARKNET_TINYV2_CONFIG']
  weights = os.environ['DARKNET_TINYV2_WEIGHTS']
  data = os.environ['DARKNET_TINYV2_DATA']

if config == "tiny-v3":
  cfg = os.environ['DARKNET_TINYV3_CONFIG']
  weights = os.environ['DARKNET_TINYV3_WEIGHTS']
  data = os.environ['DARKNET_TINYV3_DATA']

if config == "v2":
  cfg = os.environ['DARKNET_V2_CONFIG']
  weights = os.environ['DARKNET_V2_WEIGHTS']
  data = os.environ['DARKNET_V2_DATA']

if config == "v3":
  cfg = os.environ['DARKNET_V3_CONFIG']
  weights = os.environ['DARKNET_V3_WEIGHTS']
  data = os.environ['DARKNET_V3_DATA']

try:
  gpu=os.environ['NVIDIA_VISIBLE_DEVICES'];
except:
  set_gpu(0)

net = load_net(cfg, weights, 0)
meta = load_meta(data)

raw = detect(net, meta, filename, threshold)

result = {}
result['config'] = config
result['cfg'] = cfg
result['weights'] = weights
result['data'] = data
result['threshold'] = threshold
result['filename'] = filename
result['count'] = len(raw)

entities = []
for k in range(len(raw)):
  # Prepare info for the prediction image
  record = {}
  record['id'] = str(k)
  record['entity'] = raw[k][0]
  record['confidence'] = raw[k][1] * 100.0

  center = {}
  center['x'] = int(raw[k][2][0])
  center['y'] = int(raw[k][2][1])
  record['center'] = center
  record['width'] = int(raw[k][2][2])
  record['height'] = int(raw[k][2][3])

  entities.append(record)

result['results'] = entities

json.dump(result, codecs.open('/dev/stdout', 'w', encoding='utf-8'), separators=(',', ':'), sort_keys=True, indent=2)
