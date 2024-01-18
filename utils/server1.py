#communication with raspberry pi
import cv2
import zmq
import numpy as np
import threading
import time
import os
from pathlib import Path
import argparse
import math
import json

import warnings

try:
        from utils.Comms import getnewlatlong, init_socket
except:
       from Comms import getnewlatlong, init_socket

try:
       import rospy
       from sensor_msgs.msg import Image
       from cv_bridge import CvBridge
       from geometry_msgs.msg import PoseStamped
       from std_msgs.msg import Bool
       import signal
except Exception as e:
       warnings.warn(f"ROSPY not imported!!.... Error: {e}")

class ROS_Talker:
        def __init__(self) -> None:
                rospy.init_node("Stereo_py.node")
                rospy.loginfo("It has started ")

                self.publ = rospy.Publisher("/camera/left/image_raw",Image,queue_size=10)
                self.pubr = rospy.Publisher("/camera/right/image_raw",Image,queue_size=10)
                
                self.rate = rospy.Rate(20)
                self.br = CvBridge()

                self.pause = False

                signal.signal(signal.SIGINT, self.signal_handler)

        def pub_img(self, talker):
                while(talker.play):
                        if talker.show and not self.pause:
                                talker.show = False
                                self.publ.publish(self.br.cv2_to_imgmsg(talker.img_data))
                                self.pubr.publish(self.br.cv2_to_imgmsg(talker.img2_data))



        def signal_handler(self, sig, frame):
                print("Ctrl+C pressed. Terminating...")
                cv2.destroyAllWindows()
                rospy.signal_shutdown("Ctrl+C pressed")



class Talker:
    def __init__(self,IP_addr = '169.254.163.100',use_ros=False):
        self.IP = IP_addr
        self.img_data = None
        self.img2_data = None
        self.got_img = False

        self.show = False
        self.HR = 0
        self.SpO2 = 0
        self.temp = 0
        self.depth = 0

        self.use_ros = use_ros

        self.play = True

        if self.use_ros:
               self.ros_talker = ROS_Talker()



    def show_img(self):
        '''
                Displaying camera feed
        '''
        print("Displaying")
        while(1):
            if self.show and self.showl:
                self.show = False
                self.showl = True
                cv2.imshow('left', self.img_data)
                cv2.imshow('right', self.img2_data)
                #self._out.write(self.img_data)
                #self.pub.publish(self.br.cv2_to_imgmsg(self.img_data))
            if cv2.waitKey(1) & 0xFF == ord('q'):
                cv2.destroyAllWindows()
                break

        
    def pub_img(self):
        if not self.use_ros:
              warnings.warn("ROS Library not found!")
              return
        self.ros_talker.pub_img(self)
                

    def left(self,port='5555'):
            '''
                Communication with left camera 

                input: 
                        port = Port number of the left camera

                output: 
                        None
            '''
            count = 0
            socket = init_socket(self.IP, port)
            l=[]
            while True:
                    socket.send_string('read')
                    a = time.time()
                    image = socket.recv_pyobj()['img']
                    self.img_data = cv2.imdecode(image, flags=1)
                    # cv2.imwrite("left%05d.png" % count, self.img_data)
                    # Path("left%05d.png"%count).rename("Images/left/left%05d.png"%count)
                    count += 1
                    self.showl = True
                    self.got_img = True
                #     l.append(1/(time.time()-a))
                #     fps = str(1/(time.time()-a))
                #     f = open("D435i FPS.csv", "a")
                #     f.write(fps + '\n')
                    
    
    def right(self, port='5556'):
            '''
                Communication with right camera 

                input: 
                        port = Port number of the right camera

                output: 
                        None
            '''
            count2 = 0
            socket2 = init_socket(self.IP, port)
            while True:
                    socket2.send_string('read2')
                    # a = time.time()
                    image = socket2.recv_pyobj()['img2']
                    self.img2_data = cv2.imdecode(image, flags=1)
                    # cv2.imwrite("right%05d.png" % count2, self.img2_data)
                    # Path("right%05d.png"%count2).rename("Images/right/right%05d.png"%count2)
                    count2 += 1
                    self.show = True
                    self.got_img = True


    def show_temp(self, port='5557'):
        '''
                Communication with temperature sensor

                input:
                        port = port number of temperature sensor

                output:
                        None
        '''
        socket3 = init_socket(self.IP, port)
        while True:
                socket3.send_string('read3')
                temp = socket3.recv_string()
                temp = temp.split(":")
                self.temp = int(float(temp[1]))
                # print(temp)


    def show_GPS(self, port='5559'):
        '''
                Communication with GPS

                input:
                        port = port number of GPS

                output:
                        None
        '''
        socket5 = init_socket(self.IP, port)
        while True:
                socket5.send_string('read5')
                GPS = socket5.recv_string()
                print(GPS)

    def show_depth(self, port='5560'):
        '''
                Communication with sonar

                input:
                        port = port number of sonar

                output:
                        None
        '''
        socket6 = init_socket(self.IP, port)
        while True:
                socket6.send_string('read6')
                recv = socket6.recv_string()
                recv = recv.split(":")
                self.depth = float(recv[1])
                print(float(recv[1]), "m")
                # print(sonar)

    def show_HR(self, port='5561'):
        '''
                Communication with Heart rate sensor

                input:
                        port = port number of HR sensor

                output:
                        None
        '''
        # global HR
        socket7 = init_socket(self.IP, port)
        while True:
                socket7.send_string('read7')
                data = socket7.recv_string()
                data = data.split(";")
                data[0] = data[0].split(":")
                data[1] = data[1].split(":")
                self.HR = int(float(data[0][1]))
                self.SpO2 = int(float(data[1][1]))


    def pause_slam(self):
           '''
                Pause SLAM
           '''
           if self.use_ros:
                  self.ros_talker.pause = self.ros_talker.pause == False
           else: 
                  warnings.warn("NO ROS FOUND!")

    def stop(self):
           '''
                Program stop handler
           '''
           self.play = False

def Runner(image = False, temperature = False, GPS=False, depth=False, heartrate=False):
        Talker_helper = Talker(IP_addr='169.254.211.41')
        
        threads = []

        if image:
                t1 = threading.Thread(target=Talker_helper.left)
                t2 = threading.Thread(target=Talker_helper.right)
                t3 = threading.Thread(target=Talker_helper.show_img)
                threads.append(t1)
                threads.append(t2)
                threads.append(t3)

        if temperature:
               t4 = threading.Thread(target=Talker_helper.show_temp)
               threads.append(t4)
                
        if GPS:
                t6 = threading.Thread(target=Talker_helper.show_GPS)
                threads.append(t6)

        if depth:
                t7 = threading.Thread(target=Talker_helper.show_depth)
                threads.append(t7)

        if heartrate:
                t8 = threading.Thread(target=Talker_helper.show_HR)
                threads.append(t8)

        for i in threads:
              i.start()

        return Talker_helper, threads
                        

if __name__ == "__main__":
        '''
                Setting arguments and link the threads
        '''
        parser = argparse.ArgumentParser()
        parser.add_argument("-im", "--image", action="store_true")
        parser.add_argument("-t", "--temperature", action="store_true")
        parser.add_argument("-g", "--GPS", action="store_true")
        parser.add_argument("-d", "--depth", action="store_true")
        parser.add_argument("-hr", "--heartrate", action="store_true")
        parser.add_argument("-ros", "--UseROS", action="store_true")
        args = parser.parse_args()

        # print(args)
        

        # Set use_ros to True to initialize ROS publisher
        Talker_helper = Talker(IP_addr='169.254.203.72',use_ros=args.UseROS)
        
        threads = []

        if args.image:
                t1 = threading.Thread(target=Talker_helper.left)
                t2 = threading.Thread(target=Talker_helper.right)
                t3 = threading.Thread(target=Talker_helper.show_img)
                threads.append(t1)
                threads.append(t2)
                threads.append(t3)
                if args.UseROS:
                        t9 = threading.Thread(target=Talker_helper.pub_img)
                        threads.append(t9)

        if args.temperature:
               t4 = threading.Thread(target=Talker_helper.show_temp)
               threads.append(t4)
                
        if args.GPS:
                t6 = threading.Thread(target=Talker_helper.show_GPS)
                threads.append(t6)

        if args.depth:
                t7 = threading.Thread(target=Talker_helper.show_depth)
                threads.append(t7)

        if args.heartrate:
                t8 = threading.Thread(target=Talker_helper.show_HR)
                threads.append(t8)

        for i in threads:
              i.start()

        # for i in threads:
        #       i.join()
        

        # Talker_helper = Talker(IP_addr='169.254.203.72')
        # t1 = threading.Thread(target=Talker_helper.left)
        # t2 = threading.Thread(target=Talker_helper.right)
        # t3 = threading.Thread(target=Talker_helper.show_img)
        # t4 = threading.Thread(target=Talker_helper.show_temp)
        # t6 = threading.Thread(target=Talker_helper.show_GPS)
        # t7 = threading.Thread(target=Talker_helper.show_sonar)

        # t1.start()
        # t2.start()
        # t3.start()
        # t4.start()
        # t5.start()
        # t6.start()
        # t7.start()