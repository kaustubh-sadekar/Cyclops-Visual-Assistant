"""
MIT License

Copyright (c) 2020 kaustubh_sadekar, Malav_Bateriwala, Vishruth_Kumar

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

"""


__author__ = "Kaustubh Sadekar, Malav Bateriwala, Vishruth Kumar"
__copyright__ = "Copyright (C) 2020 Kaustubh Sadekar,\
                 Malav Bateriwala, Vishruth Kumar"
__license__ = "MIT"
__version__ = "1.0"


import json
import sys
sys.path.append('/home/pi/depthai/')
import consts.resource_paths
import cv2
import depthai
import time
import speech_recognition as sr
import os
import numpy as np
import random
from threading import *
import time


exit_flag = False
objects = []
distx = []
distz = []
subtitles = " "

time.sleep(5)

class BgListener(Thread):
    r"""Class for performing speech recognition audio feedback.

    The class performs speech recognition using the speech_recognition
    library and plays audio file to provide audio feedback to the user
    based on different conditions. It inherits the Thread class to
    enable multi-threading.

    Attributes
    ----------
    phrase : string
        Output of the speech recognition API stored as string.
    
    recog : object
        Instance used to access the method of speech_recognition 
        to listen in background for audio.
    
    search_object : string
        Class name for object to be searched.

    audio_root : string
        Absolute path to the folder containing all the audio files.

    """
    def __init__(self):
        super(BgListener, self).__init__()
        self.phrase = " "
        self.recog = sr.Recognizer()
        self.recog.listen_in_background(
                                        sr.Microphone(device_index=0),
                                        self.callback,phrase_time_limit=3
                                        )
        self.search_object = "None"
        self.audio_root = "/home/pi/depthai/cyclops_code/audio/"
        self.lock = Lock()

        # Playing the initial greeting audio.
        os.system("mpg123 /home/pi/depthai/cyclops_code/audio/greetings.mp3")

    def callback(self,recognizer,audio):
        r"""Callback function for listen_in_background method.

        The audio signal is converted to text using speech recognition API.
        The output of the speech recognition API is stored in the attribute
        phrase. This is the callback function for listen_in_background
        method of speech_recognition module.

        Parameters
        ----------
        recognizer: Object
            Instance of the Recognizer class of speech_recognition package.
        
        audio: Object
            Instance of the Microphone class of speech_recognition package.

        """
        try:
            self.phrase = recognizer.recognize_google(
                                                      audio,
                                                      language = 'en-US'
                                                      )
        except:
            print("Oops! didn't get that!")
            pass
    

    def run(self):
        r"""Overwrites the run method of Thread class.

        This method is called after the thread is started using the
        start method. The code under this method is run on a new thread.
        Global variables are used to share information between different
        threads.

        Global Variables
        ----------------

        objects : list
            List of objects that are detected by OAK-D
        
        distx : list
            List of corresponding object distance in x direction
        
        distz : list
            List of corresponding object distance in z direction
        
        exit_flag : bool
            Boolean to stop the thread. Both the threads stop when
            it is set to True.
        
        subtitles : string
            Sting representing the content played as audio feedback
            using different audio files.

        """
        global objects
        global distx
        global distz
        global exit_flag
        global subtitles

        while not exit_flag:

            # Checking for the trigger phrase in the audio input from user.
            if 'cyclops can you see' in self.phrase:
                self.search_object = self.phrase[20:]
                if self.search_object.lower() == "tv monitor":
                    self.search_object = "tvmonitor"
                print("Search object : %s"%self.search_object)
                self.phrase = " "
            
            # Checking if the object to be searched is in list 
            # of detected objects
            if self.search_object in objects:

                # Critical section starts 
                self.lock.acquire()
                object_index = objects.index(self.search_object)
                object_distance_z = distz[object_index]
                center_x = distx[object_index]
                self.lock.release()
                # Critical section ends

                # Feedback for object in right side of device
                if center_x > 0.66:
                    dirFile = "%sright.mp3"%self.audio_root
                    dirphrase = "in right"

                # Feedback for object in front of the device
                elif center_x > 0.33:
                    dirFile = "%sfront.mp3"%self.audio_root
                    dirphrase = "in front"

                # Feedback for object in left side of the device
                else:
                    dirFile = "%sleft.mp3"%self.audio_root
                    dirphrase = "in left"
                

                # Feedback for object at a distance greater than four meters
                if object_distance_z > 4:
                    os.system(
                              "mpg123 %sfar.mp3 %s"
                              %(self.audio_root,dirFile)
                              )
                    subtitles = "Yes but it is far "+dirphrase

                # Feedback for object at a distance greater than three meters
                elif object_distance_z > 3:
                    os.system(
                              "mpg123 %sobject.mp3 %sthreeMt.mp3 %s"
                              %(self.audio_root,self.audio_root,dirFile)
                              )
                    subtitles = "Object at Three meters "+dirphrase
                
                # Feedback for object at a distance greater than two meters
                elif object_distance_z > 2:
                    os.system(
                              "mpg123 %sobject.mp3 %stwoMt.mp3 %s"
                              %(self.audio_root,self.audio_root,dirFile)
                              )
                    subtitles = "Object at Two meters "+dirphrase
                
                # Feedback for object at a distance greater than one meter
                elif object_distance_z > 1:
                    os.system(
                              "mpg123 %sobject.mp3 %soneMt.mp3 %s"
                              %(self.audio_root,self.audio_root,dirFile)
                              )
                    subtitles = "Object at One meters "+dirphrase

                # Feedback for object at a distance less than one meter
                else:
                    os.system("mpg123 %sstopGrab.mp3"%self.audio_root)
                    subtitles = "Stop and stretch your hand grab object"
                    self.search_object = "None"
            
            if "cyclops shutdown" in self.phrase:
                exit_flag = True


class Vision(Thread):
    r"""Class for reading data from the OAK-D module.

    This class is responsible for converting extracting data from the OAK-D
    device. Depending on what data is required from OAK-D the pipeline is
    configured.

    Arguments
    ---------

    threshold : float32
        Confidence threshold above which the detections are to be considered.
        It should be between (0-1)
    
    display : bool
        Flag to enable display the processed data obtained from OAK-D.

    save_output : bool
        Flag to enable saving the processed data frames.



    Attributes
    ----------

    device : object
        Object of the Device class of depthai library.
    
    confidence_threshold : float32
        Confidence threshold above which the detections are to be considered.
        It should be between (0-1)
    
    display : bool
        Flag to enable display the processed data obtained from OAK-D.

    save_output : bool
        Flag to enable saving the processed data frames.

    nnet_packets : list
        List of dictionaries which contain the predictions from OAK-D.

    data_packets : list
        List of data obtained from OAK-D (camera frames, depth etc)

    entries_prev = list
        Buffer list to store the data from OAK-D at each step.

    lock : object
        Object of Lock() class of threading library    

    """

    def __init__(self,threshold=0.5,display=True,save_output=False):

        # initialize super class
        super(Vision, self).__init__()
        # initialize depthai Device object
        self.device = depthai.Device()
        self.confidence_threshold = threshold
        self.display = display
        self.save_output = save_output
        self.nnet_packets = None 
        self.data_packets = None
        self.entries_prev = []
        self.lock = Lock()

        # Saving frames to a video if flag is set.
        if self.save_output:
            self.out_h, self.out_w = [300, 300]
            self.output_file = "ObjectDetetWithDistance.avi"
            self.fps = 30
            self.fourcc = cv2.VideoWriter_fourcc(*'XVID')
            self.out_wr = cv2.VideoWriter(
                                        self.output_file,
                                        self.fourcc,
                                        self.fps,
                                        (self.out_w,self.out_h)
                                        )

        # Verify if the device is well connected and initialized properly
        if not self.device:
            raise RuntimeError("Error initializing device. Try to reset it.")

        # Define the pipeline for the OAK-D device
        self.pipeline = self.device.create_pipeline(config={
            'streams': ['metaout','previewout'],
            'depth':
            {
                'calibration_file': consts.resource_paths.calib_fpath,
                'padding_factor': 0.3,
                'depth_limit_m': 10.0,
                'confidence_threshold' : 0.5,
            },
            'ai': {
                "blob_file": consts.resource_paths.blob_fpath,
                "blob_file_config": "/home/pi/depthai/resources" +\
                    "/nn/mobilenet-ssd/mobilenet-ssd_depth.json",
                "calc_dist_to_bb": True,
            },
        })

        # Verify if pipeline creation is successful
        if self.pipeline is None:
            raise RuntimeError('Pipeline creation failed!')

        # Load the names of objects to be detected
        with open(consts.resource_paths.blob_config_fpath) as f:
            data = json.load(f)
    
        try:
            self.labels = data['mappings']['labels']
        except:
            self.labels = None
            print("Labels not found in json!")
    
    def run(self):
        r"""Overwrites the run method of Thread class.

        This method is called after the thread is started using the
        start method. The code under this method is run on a new thread.
        Global variables are used to share information between different
        threads.

        Global Variables
        ----------------

        objects : list
            List of objects that are detected by OAK-D
        
        distx : list
            List of corresponding object distance in x direction
        
        distz : list
            List of corresponding object distance in z direction
        
        exit_flag : bool
            Boolean to stop the thread. Both the threads stop when
            it is set to True.
        """
        
        global objects
        global distx
        global distz
        global exit_flag


        # keep running the loop where data is extracted from OAK-D and
        # various operations are performed using the data. The loop
        # continues till exit_flag is set to True when user says -
        # "cyclops shutdown"


        while not exit_flag:
            # Retrieve data packets from the device.
            # A data packet contains the video frame data.
            self.nnet_packets, self.data_packets =\
                self.pipeline.get_available_nnet_and_data_packets()
            self.entries_prev = []
            objects = []
            distx = []
            distz = []

            # filtering data for valid objects detected based on threshold.
            for nnet_packet in self.nnet_packets:
                self.entries_prev = []
                for e in nnet_packet.entries():
                    if e[0]['id'] == -1.0 or e[0]['confidence'] == 0.0:
                        break
                    if e[0]['confidence'] > self.confidence_threshold:
                        self.entries_prev.append(e[0])


            for packet in self.data_packets:
                # By default, DepthAI adds other streams 
                # (notably 'meta_2dh'). Only process `previewout`.
                if packet.stream_name == 'previewout':
                    data = packet.getData()
                    # change shape (3, 300, 300) -> (300, 300, 3)
                    data0 = data[0, :, :]
                    data1 = data[1, :, :]
                    data2 = data[2, :, :]
                    frame = cv2.merge([data0, data1, data2])
                    data = None
                    self.img_h = frame.shape[0]
                    self.img_w = frame.shape[1]
                    
                    # reading predictions from the model for valid objects
                    for e in self.entries_prev:
                        # saving uppper left corner of bounding box
                        pt1 = int(e['left'] * self.img_w),\
                            int(e['top'] * self.img_h)
                        # saving lower right corner of the bounding box
                        pt2 = int(e['right'] * self.img_w),\
                            int(e['bottom'] * self.img_h)
                        
                        self.lock.acquire()
                        # appending the label, z and x distance for
                        # the detected object
                        objects.append(self.labels[int(e['label'])])
                        distz.append(e['distance_z'])
                        distx.append((e['left'] + e['right'])*0.5)

                        # Reading the subtitles for audio feedback
                        subs = subtitles
                        self.lock.release()

                        # display the detections
                        if self.display or self.save_output:
                            cv2.rectangle(frame, pt1, pt2, (0, 0, 255), 2)
                            cv2.putText(
                                        frame,
                                        self.labels[int(e['label'])],
                                        (pt1[0],pt1[1]),
                                        1,
                                        1,
                                        (0,0,255),
                                        )
                            cv2.putText(
                                        frame,
                                        "Z: %.2f m"%e['distance_z'],
                                        (pt1[0],pt1[1]+30),
                                        1,
                                        1,
                                        (0,0,255),
                                        )
                            cv2.putText(
                                        frame,
                                        subs,
                                        (
                                         int(self.img_w*0.05), 
                                         int(self.img_h*0.9)
                                        ),
                                        1,
                                        1,
                                        (0,0,255),
                                        )
                    
                    if self.display:
                        cv2.imshow("preview", cv2.resize(frame, (500, 500)))
                        cv2.waitKey(1)    
                
        print("Completed running the detection loop") # Just for debugging
        

    def __del__(self):

        del self.pipeline
        if self.save_output:
            self.out_wr.release()


if __name__ == "__main__":
    # Creating the objects for threads for BgListener and Vision class
    bg_listener_thread = BgListener()
    vision_thread = Vision()

    # starting the threads
    bg_listener_thread.start()
    vision_thread.start()

    # waiting for both the threads to end before closing main program
    vision_thread.join()
    bg_listener_thread.join()

    # Playing a good bye note before closing the program.
    os.system("mpg123 /home/pi/depthai/cyclops_code/audio/bye.mp3")