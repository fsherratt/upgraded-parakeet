import cv2 as cv
import sys
import os
import glob

if len( sys.argv ) < 2:
    print( "exiting program. Need folder path" )
    sys.exit( 1 ) 

folderpath = os.path.join( os.getcwd(), sys.argv[ 1 ] )
output = 'output.avi'
print( f'Making video from folder path: {folderpath}' )
print( f'Name: {output}' )
print( f'Getting files.....' )

images = glob.glob( folderpath + "*.png" )
images.sort()

print( 'Got ' + str( len( images ) ) + ' images!' )
size = cv.imread( images[ 0 ] )
height, width, layers = size.shape

out = cv.VideoWriter( output, cv.VideoWriter_fourcc(*'XVID'), 15, ( width, height ) )

for filename in images:
    img = cv.imread( filename )
    out.write( img )

out.release()
