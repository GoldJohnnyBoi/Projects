#Library Dependencies
import numpy as np
import cv2
import time
from PIL import Image
import os.path
import pyrealsense2 as rs
from RealsenseTools import realsense_camera,Vector2D,Vector3D,map2DTo3D
#from RaspPiCode import *   #uncomment when on pi

#Global Drawer declarations
LOUVER_DRAWER_ONE = "0001"
LOUVER_DRAWER_TWO = "0010"
LOUVER_DRAWER_THREE = "0011"
CAB_CNTR_P_DRAWER_ONE = "0101"
CAB_CNTR_P_DRAWER_TWO = "0110"
CAB_CNTR_P_DRAWER_THREE = "0111"
TNK_CNTR_P_DRAWER_ONE = "1001"
TNK_CNTR_P_DRAWER_TWO = "1010"
TNK_CNTR_P_DRAWER_THREE = "1011"


#Threshold Values
bad = 0.02 
thresh = 30
max_v = 255
MAX_ATTEMPTS = 5
cam = None #Needs to be defined so the Camera Initialization works

images = [] #Needs to be defined up here instead of the loop or it will continously clear the array instead of keeping it


def difference_mask_score(imaget,imagec,thresh,max_v, median_kernel):   #Creates difference score for comparison
    #Gets the difference and provides a mask for all values above the threshold
    diff = cv2.absdiff(imaget,imagec)

    ret,mask = cv2.threshold(diff,thresh,max_v,cv2.THRESH_BINARY) #Returns two values, need both variables

    erosion_size = median_kernel
    
    element = cv2.getStructuringElement(cv2.MORPH_RECT,(2*erosion_size+1,2*erosion_size+1),(erosion_size,erosion_size)) 

    mask_eroded = cv2.erode(mask,element)
    
    cv2.imshow("mask",mask_eroded)
      
    dif_pixel_count = cv2.countNonZero(mask_eroded) #Counts how many pixels have changed
    total_pixel_count = len(mask_eroded)*len(mask_eroded[0]) #Total amount of pixels 

    score = dif_pixel_count/total_pixel_count 

    return score

def mouseCallBack(event,x,y,flags,param):  #For setting up rectangles
    #Displays Coordinates When Left Button Is Pressed
    if event == cv2.EVENT_LBUTTONDOWN: #checks mouse left button down condition
        print("Coordinates of pixel: X: ",x,"Y: ",y)

def initialize_camera_LOGI(index):    #Initializes The Logitech Webcam
    global cam
    cam = cv2.VideoCapture()
    cam.open(index,cv2.CAP_ANY)
    time.sleep(0.100)
    cam.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
    time.sleep(0.100)
    cam.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
    time.sleep(0.100)
    cam.set(cv2.CAP_PROP_FPS,30)    

    time.sleep(0.100)
    if not cam.isOpened():
        raise Exception("Cannot Open Camera")

def initialize_camera(): #Turns on camera for Intel RealSense
    global cam
    attempt = 0
    print("Attempting to connect to camera ...")
    while cam == None and attempt<MAX_ATTEMPTS:
        try:
            cam = realsense_camera()
            time.sleep(0.1)
        except:
            attempt +=1
    if cam == None:
        raise Exception("Failed to Connect to Camera")
    print("Starting Camera...")
    cam.start()
    cam.align_config(1) #align to color frame

    print("SUCCESS")


def read_camera_frame():  #Reads a frame from the camera for LOGITECH
    for i in range(5):    #Pi delays by 5 frames, this counteracts that and keeps the frames updated. Can comment out for testing on windows computers.
        ret,frame = cam.read()
        i=i+1
    if not ret:
        raise Exception("Did not recieve frame from camera.")
    return frame


def align_image(image,pts1,pts2,frame_size):  #Actually warps image
    matrix = cv2.getPerspectiveTransform(pts1, pts2)
    result = cv2.warpPerspective(image, matrix, frame_size) 
    return result


def kill_camera():    #Closes the connection to the camera
    if cam.isOpened():
        cam.release()


def initialize_viewer_window():    #Initalizes the Live Feed
    global window_header
    window_header = "Live Feed (press q to quit, press n for next, p for previous)"
    cv2.namedWindow(window_header, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(window_header,1000,600)
    cv2.setMouseCallback(window_header,mouseCallBack)


def show_live_feed():
    #shows the live feed
    global index
    cframe = frames[index]
    if isinstance(cframe,np.ndarray):
        curframe=cframe
    cv2.imshow(window_header,curframe)

    key = cv2.waitKey(1)
    if key ==ord('q'):
        print("Ending Stream")
        raise Exception("Exiting...")
    elif key == ord('n'):
        if index+1>=len(frame_names):
            index=0
        else:
            index+=1
        print(f"Switching to {frame_names[index]}")
    elif key == ord('p'):
        if index-1<0:
            index=len(frame_names)-1
        else:
            index-=1
        print(f"Switching to {frame_names[index]}")
    elif key == ord('s'):
        cv2.imwrite("capture.png",cframe)
        print(f"Frame Captured")


def Warp_Perspective(image):  #Sets up the warping
    corners_of_drawer_2 = np.float32([[253,220],[1665,220],[127,931],[1788,931]])   #check if camera moves corners are locator pins in drawer
    origin = [220,220]                                                              #top left pin in drawer
    new_corners = np.float32([[0+origin[0],0+origin[1]],[1537+origin[0],0+origin[1]],[0+origin[0],722+origin[1]],[1537+origin[0],722+origin[1]]])
    a_frame = align_image(image,corners_of_drawer_2,new_corners,(1920,1080))
    return a_frame

def Crop_Image(a_frame, y_bounds, x_bounds):    #Crops
    c_frame = a_frame[y_bounds[0]:y_bounds[1],x_bounds[0]:x_bounds[1]]
    return c_frame



# configure_GPIO()   # Configures the Pi GPIO # uncomment when on Pi
index = 0  # index of what image it's on

initialize_viewer_window()  # Include for live feed
initialize_camera()  # comment out for Pi RS
#initialize_camera_LOGI(1)  #0 for webcam, 1 for logi
# initialize_camera(0)   # uncomment for Pi 
prev_mode = "0002"
# set_output(4,0)

# mode = check_inputs()      # reads octocoupler breakout # uncomment on Pi
mode = LOUVER_DRAWER_ONE  # comment out if you need inputs
print(f"Current Mode: {mode}")
if prev_mode != mode:
# If the mode switched
    if mode == LOUVER_DRAWER_ONE:

        # median for salt pepper noise
        median_kernel = 9

        # crop boundaries
        x_bounds = [0, 690]
        y_bounds = [0, 510]

        # Rectangle Coordinates
        BoxTL_1 = [50,30]
        BoxBR_1 = [70,50]
        BoxTL_2 = [200,250]
        BoxBR_2 = [300,350]
        BoxTL_3 = [6,50]
        BoxBR_3 = [20,55]
        BoxTL_4 = [400,450]
        BoxBR_4 = [600,650]

    elif mode == CAB_CNTR_P_DRAWER_ONE:
        
        # median for salt pepper noise
        median_kernel = 9

        # crop boundaries
        x_bounds = [0, 690]
        y_bounds = [0, 510]

        #Rectangle Coordinates
        BoxTL_1 = []
        BoxBR_1 = []
        BoxTL_2 = []
        BoxBR_2 = []
        BoxTL_3 = []
        BoxBR_3 = []
        BoxTL_4 = []
        BoxBR_4 = []
    
    elif mode == TNK_CNTR_P_DRAWER_ONE:

        # median for salt pepper noise
        median_kernel = 9

        # crop boundaries
        x_bounds = [0, 690]
        y_bounds = [0, 510]

        #Rectangle Coordinates
        BoxTL_1 = []
        BoxBR_1 = []
        BoxTL_2 = []
        BoxBR_2 = []
        BoxTL_3 = []
        BoxBR_3 = []
        BoxTL_4 = []
        BoxBR_4 = []


    elif mode == LOUVER_DRAWER_TWO:

        # median for salt pepper noise
        median_kernel = 9

        # crop boundaries
        x_bounds = [218, 1764]
        y_bounds = [230, 953]

        #Rectangle Coordinates
        BoxTL_1 = []
        BoxBR_1 = []
        BoxTL_2 = []
        BoxBR_2 = []
        BoxTL_3 = []
        BoxBR_3 = []
        BoxTL_4 = []
        BoxBR_4 = []
        BoxTL_5 = []
        BoxBR_5 = []
        

    elif mode == CAB_CNTR_P_DRAWER_TWO:

        # median for salt pepper noise
        median_kernel = 9

        # crop boundaries
        x_bounds = [218, 1764]
        y_bounds = [230, 953]

        #Rectangle Coordinates
        BoxTL_1 = []
        BoxBR_1 = []
        BoxTL_2 = []
        BoxBR_2 = []
        BoxTL_3 = []
        BoxBR_3 = []
        BoxTL_4 = []
        BoxBR_4 = []
        BoxTL_5 = []
        BoxBR_5 = []

    elif mode == TNK_CNTR_P_DRAWER_TWO:

         # median for salt pepper noise
        median_kernel = 9

        # crop boundaries
        x_bounds = [218, 1764]
        y_bounds = [230, 953]

        #Rectangle Coordinates
        BoxTL_1 = []
        BoxBR_1 = []
        BoxTL_2 = []
        BoxBR_2 = []
        BoxTL_3 = []
        BoxBR_3 = []
        BoxTL_4 = []
        BoxBR_4 = []
        BoxTL_5 = []
        BoxBR_5 = []


    elif mode == LOUVER_DRAWER_THREE:

        # median for salt pepper noise
        median_kernel = 9

        # crop boundaries
        x_bounds = [360, 1637]
        y_bounds = [365, 972]

        #Rectangle Coordinates
        BoxTL_1 = []
        BoxBR_1 = []
        BoxTL_2 = []
        BoxBR_2 = []
        BoxTL_3 = []
        BoxBR_3 = []
        BoxTL_4 = []
        BoxBR_4 = []
        BoxTL_5 = []
        BoxBR_5 = []
        BoxTL_6 = []
        BoxBR_6 = []
    
    elif mode == CAB_CNTR_P_DRAWER_THREE:

        # median for salt pepper noise
        median_kernel = 9

        # crop boundaries
        x_bounds = [360, 1637]
        y_bounds = [365, 972]

        #Rectangle Coordinates
        BoxTL_1 = []
        BoxBR_1 = []
        BoxTL_2 = []
        BoxBR_2 = []
        BoxTL_3 = []
        BoxBR_3 = []
        BoxTL_4 = []
        BoxBR_4 = []
        BoxTL_5 = []
        BoxBR_5 = []
        BoxTL_6 = []
        BoxBR_6 = []
    
    elif mode == TNK_CNTR_P_DRAWER_THREE:

        # median for salt pepper noise
        median_kernel = 9

        # crop boundaries
        x_bounds = [360, 1637]
        y_bounds = [365, 972]

        #Rectangle Coordinates
        BoxTL_1 = []
        BoxBR_1 = []
        BoxTL_2 = []
        BoxBR_2 = []
        BoxTL_3 = []
        BoxBR_3 = []
        BoxTL_4 = []
        BoxBR_4 = []
        BoxTL_5 = []
        BoxBR_5 = []
        BoxTL_6 = []
        BoxBR_6 = []



while True:
    try:

        cv2.waitKey(0)  #Press a button in order to capture frame
        #For some unknown reason the Pi will be 5 captures delayed before displaying the correct frame. Current solution is to use a for loop.

        #image = read_camera_frame() #Logitech camera initialization    

        raw_image = cam.get_alignedframes() #How to read frames using Intel RealSense Cam
        image = raw_image[0].copy() #This is important so that the frames can actually be read and transferred for Intel RealSense
    
        image_gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) #Gray Scales to reduce the affect dirt and glare have on the photo
        

        image_warp = Warp_Perspective(image_gray) #Removes any uneccesary background and creates a better image to compare one to another
        

        image_crop = Crop_Image(image_warp, y_bounds, x_bounds) #Cropping image to make the comparison easier
        

        image_blur = cv2.medianBlur(image_crop, median_kernel) #Reduces the effects dirt and glare may have on the comparison
        
        # Put Rectangles Here
        if mode == LOUVER_DRAWER_ONE or LOUVER_DRAWER_TWO or LOUVER_DRAWER_THREE: #4 Boxes, 4 Diff rects, repeated for each drawer type.
            cv2.rectangle(image_blur, (BoxTL_1) ,(BoxBR_1) , (0,0,0), -1)
            cv2.rectangle(image_blur, (BoxTL_2) ,(BoxBR_2) , (0,0,0), -1)
            cv2.rectangle(image_blur, (BoxTL_3) ,(BoxBR_3) , (0,0,0), -1)
            cv2.rectangle(image_blur, (BoxTL_4) ,(BoxBR_4) , (0,0,0), -1)
        
        elif mode == CAB_CNTR_P_DRAWER_ONE or CAB_CNTR_P_DRAWER_TWO or CAB_CNTR_P_DRAWER_THREE:
            cv2.rectangle(image_blur, (BoxTL_1) ,(BoxBR_1) , (0,0,0), -1)
            cv2.rectangle(image_blur, (BoxTL_2) ,(BoxBR_2) , (0,0,0), -1)
            cv2.rectangle(image_blur, (BoxTL_3) ,(BoxBR_3) , (0,0,0), -1)
            cv2.rectangle(image_blur, (BoxTL_4) ,(BoxBR_4) , (0,0,0), -1)
            cv2.rectangle(image_blur, (BoxTL_5) ,(BoxBR_5) , (0,0,0), -1)

        elif mode == TNK_CNTR_P_DRAWER_ONE or TNK_CNTR_P_DRAWER_TWO or TNK_CNTR_P_DRAWER_THREE:
            cv2.rectangle(image_blur, (BoxTL_1) ,(BoxBR_1) , (0,0,0), -1)
            cv2.rectangle(image_blur, (BoxTL_2) ,(BoxBR_2) , (0,0,0), -1)
            cv2.rectangle(image_blur, (BoxTL_3) ,(BoxBR_3) , (0,0,0), -1)
            cv2.rectangle(image_blur, (BoxTL_4) ,(BoxBR_4) , (0,0,0), -1)
            cv2.rectangle(image_blur, (BoxTL_5) ,(BoxBR_5) , (0,0,0), -1)
            cv2.rectangle(image_blur, (BoxTL_6) ,(BoxBR_6) , (0,0,0), -1)

        
        images.append(image_blur) #Need one append so that the array updates

        window_frame = "Frame"
        cv2.imshow(window_frame, images[0])
        cv2.setMouseCallback(window_frame,mouseCallBack)

        if len(images) == 1:
            print ("pass // Taking new comparison photo // Resetting...")   #If there is only one image in the array, it will pass
            pass
        elif len(images) == 2:
            score = difference_mask_score(images[0], images[1], thresh, max_v, median_kernel)       #If there are two images, it will take those two images and compare them, the latest to the oldest.
            print(score)                                                                            #The Difference Mask will return a score and using that score and relative thresholds it will determine
            if score < bad:  #Measures percent diff, if below a certain percent it will be good.    #if the process should continue or if there is a problem. 
                images.pop(0) #Pops first item in array list, moving the second one to the first
                print ("It's good, pop!")
            else:
                images = [] #Resets Array
                print("Potential Problem Detected // Operator Intervention Required")

    except Exception as e:
        print(e)


