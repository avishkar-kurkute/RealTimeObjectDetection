# usage: python yolo_video.py --model "./yolov6n.onnx" --source 0

import cv2
import numpy as np
import argparse
import pyttsx3 as sp
import threading


import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageTk



INPUT_WIDTH = 640
INPUT_HEIGHT = 640
SCORE_THRESHOLD = 0.5
NMS_THRESHOLD = 0.45
CONFIDENCE_THRESHOLD = 0.2

# Text parameters.
FONT_FACE = cv2.FONT_HERSHEY_SIMPLEX
FONT_SCALE = 0.7
THICKNESS = 1

# Colors.
BLACK  = (0,0,0)
BLUE   = (255,178,50)
YELLOW = (0,255,255)





# Voice Module

prev_output = None
# Create a lock object
lock = threading.Lock()

engine = sp.init('sapi5')
voices = engine.getProperty('voices')
# print(voices[0].id)
engine.setProperty('voice', voices[0].id)

def speak(audio):
    with lock:
        engine.say(audio)
        engine.runAndWait()




def draw_label(im, label, x, y):
    """Draw text onto image at location."""

    # Get text size.
    text_size = cv2.getTextSize(label, FONT_FACE, FONT_SCALE, THICKNESS)
    dim, baseline = text_size[0], text_size[1]
    # Use text size to create a BLACK rectangle.
    cv2.rectangle(im, (x,y), (x + dim[0], y + dim[1] + baseline), (0,0,0), cv2.FILLED)
    # Display text inside the rectangle.
    cv2.putText(im, label, (x, y + dim[1]), FONT_FACE, FONT_SCALE, YELLOW, THICKNESS, cv2.LINE_AA)

def pre_process(input_image, net):
      # Create a 4D blob from a frame.
      blob = cv2.dnn.blobFromImage(input_image, 1/255,  (INPUT_WIDTH, INPUT_HEIGHT), [0,0,0], 1, crop=False)

      # Sets the input to the network.
      net.setInput(blob)

      # Run the forward pass to get output of the output layers.
      outputs = net.forward(net.getUnconnectedOutLayersNames())
      return outputs

def post_process(input_image, outputs):
        global prev_output
        # Lists to hold respective values while unwrapping.
        class_ids = []
        confidences = []
        boxes = []
        # Rows.
        rows = outputs[0].shape[1]
        image_height, image_width = input_image.shape[:2]
        # Resizing factor.
        x_factor = image_width / INPUT_WIDTH
        y_factor =  image_height / INPUT_HEIGHT
        # Iterate through detections.
        for r in range(rows):
            row = outputs[0][0][r]
            confidence = row[4]
            # Discard bad detections and continue.
            if confidence >= CONFIDENCE_THRESHOLD:
                    classes_scores = row[5:]
                    # Get the index of max class score.
                    class_id = np.argmax(classes_scores)
                    #  Continue if the class score is above threshold.
                    if (classes_scores[class_id] > SCORE_THRESHOLD):
                        confidences.append(confidence)
                        class_ids.append(class_id)
                        cx, cy, w, h = row[0], row[1], row[2], row[3]
                        left = int((cx - w/2) * x_factor)
                        top = int((cy - h/2) * y_factor)
                        width = int(w * x_factor)
                        height = int(h * y_factor)
                        box = np.array([left, top, width, height])
                        boxes.append(box)

        # Perform non maximum suppression to eliminate redundant, overlapping boxes with lower confidences.
        indices = cv2.dnn.NMSBoxes(boxes, confidences, CONFIDENCE_THRESHOLD, NMS_THRESHOLD)
        for i in indices:
                box = boxes[i]
                left = box[0]
                top = box[1]
                width = box[2]
                height = box[3]
                # Draw bounding box.
                cv2.rectangle(input_image, (left, top), (left + width, top + height), BLUE, 3*THICKNESS)
                # Class label.
                label = "{}:{:.2f}".format(classes[class_ids[i]], confidences[i])
                voice_label = "{}".format(classes[class_ids[i]])
                # t2 = threading.Thread(target=draw_label,args=(input_image, label, left, top))
                if(prev_output != voice_label):
                    prev_output = voice_label
                    print(f"{voice_label} Detected")
                    # speak(f"{voice_label} Detected")
                    t1 = threading.Thread(target=speak,args=(f"{prev_output} Detected",))
                    t1.start()
                
                # print(label)
                # Draw label.
                draw_label(input_image, label, left, top)
                # t1.start()
                # t2.start()
                

                # if(i%20==0):
                #     print(f"{voice_label} Detected")
                #     speak(f"{voice_label} Detected")
                
        
        return input_image


def video():
    while True :

        # get frame from the video
        ret, frame = cap.read()
        net = cv2.dnn.readNet(modelWeights)
        # Process image.
        detections = pre_process(frame, net)
        img = post_process(frame.copy(), detections)
        
        """
        Put efficiency information. The function getPerfProfile returns the overall time for inference(t)
        and the timings for each of the layers(in layersTimes).
        """
        t, _ = net.getPerfProfile()
        label = 'Inference time: %.2f ms' % (t * 1000.0 /  cv2.getTickFrequency())
        # print(label)
        cv2.putText(img, label, (20, 40), FONT_FACE, FONT_SCALE,  (0, 0, 255), THICKNESS, cv2.LINE_AA)
        cv2.imshow('Output', img)

        if cv2.waitKey(30) & 0xFF == ord('q'):
            break



class ObjectDetectionApp:
    def __init__(self, master):
        self.master = master
        self.master.title("Object Detection")
        
        self.image_label = tk.Label(self.master)
        self.image_label.pack()
        
        self.detect_button = tk.Button(self.master, text="Detect Objects", command=self.detect_objects)
        self.detect_button.pack()
        
        # self.select_image_button = tk.Button(self.master, text="Select Image", command=self.select_image)
        # self.select_image_button.pack()
        
    def select_image(self):
        file_path = filedialog.askopenfilename()
        if file_path:
            self.display_image(file_path)
        
    def display_image(self, file_path):
        image = Image.open(file_path)
        image = image.resize((400, 300), Image.ANTIALIAS)
        photo = ImageTk.PhotoImage(image)
        self.image_label.config(image=photo)
        self.image_label.image = photo
        
    def detect_objects(self):
        # Perform object detection on the selected image
        video()
        # Placeholder for actual object detection code


def main():
    root = tk.Tk()
    app = ObjectDetectionApp(root)
    root.mainloop()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--model', default='yolov6n.onnx', help="Input your onnx model.")
    parser.add_argument('--source', default=0, type=int, help="video source - 0,1,2 ...")
    parser.add_argument('--classesFile', default='coco.names', help="Path to your classesFile.")
    args = parser.parse_args()

    modelWeights, video_source, classesFile = args.model, args.source, args.classesFile
    video_source = int(input("Enter 0 for Webcam Or 1 For IPCam: "))
    
    #IP camera Module
    if video_source != 0:
        try:
            ip_address = input("Enter Ip Address: ")
            url = f"https://{ip_address}/video"
            cap = cv2.VideoCapture(url)
        except Exception as e:
             print(f"Unable to connect with ipcam\nError:{e}")
            
    else:
        cap = cv2.VideoCapture(video_source)
         
    classes = None
    with open(classesFile, 'rt') as f:
        classes = f.read().rstrip('\n').split('\n')

    video()
    # main()
