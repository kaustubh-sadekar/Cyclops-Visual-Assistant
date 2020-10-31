"""
Description : 
=============

This code is a simple example of how to get started with the depthai API. It shows how to :
1. Initialise the device.
2. Get the data packets from the device. (The bounding box and the rgb frame)
3. Draw the bounding box using the extracted bounding box information on the extracted image from the stream.
4. Read the distance information and print it along with the bounding box.
5. Display the output.

Useage:
    python3 code6.py
"""
import json
import sys
sys.path.append('/home/pi/depthai/')
import consts.resource_paths
import cv2
import depthai

device = depthai.Device()

if not device:
    raise RuntimeError("Error initializing device. Try to reset it.")

pipeline = device.create_pipeline(config={
    'streams': ['metaout','previewout'],
    'depth':
      {
          'calibration_file': consts.resource_paths.calib_fpath,
          'padding_factor': 0.3,
          'depth_limit_m': 10.0, # In meters, for filtering purpose during x,y,z calc
          'confidence_threshold' : 0.5, #Depth is calculated for bounding boxes with confidence higher than this number 
      },
    'ai': {
        "blob_file": consts.resource_paths.blob_fpath,
        "blob_file_config": "/home/pi/depthai/resources/nn/mobilenet-ssd/mobilenet-ssd_depth.json",
        "calc_dist_to_bb": True,
    },
})

if pipeline is None:
    raise RuntimeError('Pipeline creation failed!')

out_h,out_w = [300,300]
output_file = "ObjectDetetWithDistance.avi"
fps = 30
fourcc = cv2.VideoWriter_fourcc(*'XVID')
out_wr = cv2.VideoWriter(output_file,fourcc,fps,(out_w,out_h))

with open(consts.resource_paths.blob_config_fpath) as f:
    data = json.load(f)

try:
    labels = data['mappings']['labels']
except:
    labels = None
    print("Labels not found in json!")

entries_prev = []

while True:
    # Retrieve data packets from the device.
    # A data packet contains the video frame data.
    nnet_packets, data_packets = pipeline.get_available_nnet_and_data_packets()

    for _, nnet_packet in enumerate(nnet_packets):
        entries_prev = []
        for _, e in enumerate(nnet_packet.entries()):
            if e[0]['id'] == -1.0 or e[0]['confidence'] == 0.0:
                break
            if e[0]['confidence'] > 0.5:
                entries_prev.append(e[0])

    for packet in data_packets:
        # By default, DepthAI adds other streams (notably 'meta_2dh'). Only process `previewout`.
        if packet.stream_name == 'previewout':
            data = packet.getData()
            # change shape (3, 300, 300) -> (300, 300, 3)
            data0 = data[0, :, :]
            data1 = data[1, :, :]
            data2 = data[2, :, :]
            frame = cv2.merge([data0, data1, data2])

            img_h = frame.shape[0]
            img_w = frame.shape[1]

            for e in entries_prev:
                pt1 = int(e['left'] * img_w), int(e['top'] * img_h)
                pt2 = int(e['right'] * img_w), int(e['bottom'] * img_h)
                
                cv2.rectangle(frame, pt1, pt2, (0, 0, 255), 2)
                cv2.putText(frame,labels[int(e['label'])],(pt1[0],pt1[1]),5,1,(255,255,255))
                cv2.putText(frame,"Z: %.2f m"%e['distance_z'],(pt1[0],pt1[1]+30),5,1,(255,255,255))

            cv2.imshow('previewout', frame)
            # out_wr.write(frame)

    if cv2.waitKey(1) == ord('q'):
        break

out_wr.release()
# The pipeline object should be deleted after exiting the loop. Otherwise device will continue working.
# This is required if you are going to add code after exiting the loop.
del pipeline