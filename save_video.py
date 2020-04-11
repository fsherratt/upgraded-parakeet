import numpy as np
import cv2 as cv
import pika
import sys
import signal
import os
from datetime import datetime

# Setup RabbitMQ
connection = pika.BlockingConnection(
        pika.ConnectionParameters( host = 'localhost' ) )
channel = connection.channel()

channel.exchange_declare( exchange='video_feed', exchange_type='direct' )

result = channel.queue_declare( queue='', exclusive=True )
queue_name = result.method.queue

channel.queue_bind( exchange="video_feed", queue=queue_name, routing_key="raw_feed" )


# video writing is harder. We have to define a fourCC method.
#fourcc = cv.VideoWriter_fourcc( *'XVID')
#out = cv.VideoWriter( 'output.avi', fourcc, 0, (640, 480 ) )
# out = None

d = datetime.now()
folder = os.path.join( os.getcwd(), d.strftime( "%Y.%m.%d_%H:%M:%S" ) )
os.mkdir( folder )
print( f'[x] Saving to folder: {folder}' )
counter = 0

def int_handler( signal, frame ):
    print( "Bye!!" )
    #out.release()
    sys.exit( 0 )

def saveVideo( ch, method, properties, body ):
    print( f"[x] got frame!" )
    global counter 
#     global out
    # Display
    # Decode our image string to a numpy array
    data = np.fromstring( body, np.uint8 )
    # render the image using the decode
    img = cv.imdecode( data, cv.IMREAD_GRAYSCALE )
    #write the frame
#     if out is None:
#         size = img.shape
#         fourcc = cv.VideoWriter_fourcc( *'XVID')
#         out = cv.VideoWriter( 'output.avi', fourcc, 30, (size[ 0 ], size[ 1 ] ) )

    # This is having problems, articles make it sound likeit could be a framerate issue. Maybe we could write to a file and deal with it later? We could even proecss it on the fly? Will have to investigate how to do this though.
    # out.write( img )
    name = os.path.join( folder, '{:06d}'.format(counter) + '_img.png' )
    print( f'[x] Saving to {name}' )
    cv.imwrite( name, img )
    counter = counter + 1

# Setup graceful closedown
signal.signal( signal.SIGINT, int_handler ) 


channel.basic_consume(
        queue=queue_name, on_message_callback=saveVideo, auto_ack=True )

channel.start_consuming()
