import logging
import os
import secrets
from PIL import Image
from flask import url_for, current_app
from flask_login import current_user
from flask_mail import Message
from app import mail
import cv2


# Create a function that handle profile picture
def save_picture(form_picture):
    '''This function add random hex byte & extension to a file a save to a location '''
    # create a random hex of 8 bytes
    random_hex = secrets.token_hex(8)
    # slice the file name and file extension of the picture update
    _, file_ext = os.path.splitext(form_picture.filename)
    # combine the random hex with the file extension in order set the name of the new uploaded file
    uploaded_PicName = random_hex + file_ext 
    # extract and define the path where to save the file
    picture_path = os.path.join(current_app.root_path, 'static/userpics/', uploaded_PicName)
    # Resizing the  picture before saving
    img_sizer = (125, 125)
    new_img = Image.open(form_picture)
    new_img.thumbnail(img_sizer)
    # Saving the picture
    new_img.save(picture_path)
    return uploaded_PicName



def capture_image(camera_index=0):
    ''' 
        Capture an image from the specified webcam on click
        args: 
            camera_index: Index of the webcam to use (default: 0)
    '''
    # Initialize video capture object 
    cap = cv2.VideoCapture(camera_index)

    # check if camera opened succesfully 
    if not cap.isOpened():
        print("Failed to open camera")
        return
    
    # Create a window to display the webcam feed
    cv2.namedWindow("Webcam Feed", cv2.WINDOW_NORMAL)

    # Track the click event 
    clicked = False
    def click_event(event, x, y, flags, param):
        nonlocal clicked
        # set clicked flag to True only on left mouse button event 
        if event == cv2.EVENT_LBUTTONDOWN:
            clicked = True
    #set mouse click callback function 
    cv2.setMouseCallback("Webcam Feed", click_event)
    while True:
        # Capture frame-by-frame
        ret, frame = cap.read()
        #check if the frame is read correctly
        if not ret:
            print("Fail to capture an image")
            break
        # Display the webcam feed
        cv2.imshow("Webcam Feed", frame)
        # Capture image on click 
        if clicked:
            # Get current timestamp for filemane 
            #timestamp = str(int(round(time.time() + 1000)))
            # Save captured image
            #cv2.imwrite(f"webcam_image_{timestamp}.jpg", frame)
            cv2.imwrite(f"app/static/userpics/takeapics/{current_user.username}.jpg", frame)  
            print("Image captured successfully!")
            # Reset clicked flag
            clicked = False
        # Exit on 'q' key press
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    # Release capture object
    cap.release()
    cv2.destroyAllWindows()
    return ''
