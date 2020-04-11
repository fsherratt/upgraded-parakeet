import numpy as np
import cv2 as cv
import pika
import sys


# Setup RabbitMQ
connection = pika.BlockingConnection(
        pika.ConnectionParameters( host = 'localhost' ) )
channel = connection.channel()

channel.exchange_declare( exchange='video_feed', exchange_type='direct' )

# Cap comes as a list. 0 is the first camera. Can select a second by passing -1.
# How do we identify this?
# If we want to play a video file, we pass that in as a parameter (dep injection??)
cap = cv.VideoCapture( 0 )

if not cap.isOpened():
    print( "Cannot open camera")
    exit()
while True:
    #Capture frame by frame
    ret, frame = cap.read()

    print( "Read frame!" )

    # if frame is read correctly, ret is true
    if not ret:
        print( "Cannot recieve frame (stream end?). Exiting..." )
        break

    message = cv.imencode('.jpg', frame )[1].tostring()

    channel.basic_publish(
            exchange='video_feed',
            routing_key='raw_feed',
            body=message )

    print( "Sent frame!" )
    if cv.waitKey( 1 ) == ord('q'):
        break


# When we are done, release the capture
cap.release()
out.release()
cv.destroyAllWindows()
