#! /usr/bin/env python

import sys
import glob
import os
import string
import time
import shutil
import subprocess
import StringIO

class lfoi_datafile:
    def __init__(self, index, name):
        self.index = index
        self.name  = name
        
    def __cmp__( self, other ):
        if( self.index < other.index ):
            return -1
        elif( self.index == other.index ):
            return 0
        else:
            return 1

class lfoi_elastix_registrator:
    def __init__( self, datadir ):

        self.datadir = datadir
                
        self.tstart = time.time()

        self.paramFileName = os.path.abspath('./elastix_parameters.txt')
        
        if not os.path.isfile( self.paramFileName ):
            print "ERROR: Missing parameter file: %s" % ( self.paramFileName )
            sys.exit(-1)

        self.outputDirPrefix = "elastix_out"
        self.outstandingProcesses = {}
        self.MAX_OUTSTANDING_PROCESSES = 20
                
    def run_on_tif(self):        
        print "Running run_on_tif()"
        
        # Create the over higher level dir 
        bname = os.path.basename( self.datadir )        
        cur_dir = os.getcwd()        
                       
        regdirname = cur_dir + '/' + bname + '_regdir'

        if os.path.isdir( regdirname ):
            shutil.rmtree( regdirname )

        os.mkdir( regdirname )
        print "made dir: ", regdirname

        sorted_files = []
        files = glob.glob(self.datadir + '/*_*.tif')
        for filepath in iter(files):
            filename = os.path.basename( filepath )
            
            # print 'filename', filename
            underscore_split = string.split( filename, '_' )
            
            # print 'underscore_split: ', underscore_split
            fileidx   = int( string.split( underscore_split[ -1 ], '.' )[0] )

            sorted_files.append( lfoi_datafile( fileidx, filepath ) )
    
        sorted_files.sort()
                
        fixedImagePath = sorted_files[ 0 ].name
            
        frameIncrement = 1
        frameIdx = 1
        frameMax = len(sorted_files)

        while frameIdx < frameMax:
            
            if len(self.outstandingProcesses) < self.MAX_OUTSTANDING_PROCESSES:
                
                movingImagePath = sorted_files[ frameIdx ].name
                                
                outputDir = os.path.abspath( regdirname + "/" + self.outputDirPrefix + "." + str( frameIdx ) )

                if os.path.isdir( outputDir ):
                    shutil.rmtree( outputDir )
                    
                os.mkdir( outputDir )
                    
                cmd = 'elastix -f %s -m %s -out %s -p %s > run.%d.log 2>&1' \
                    % ( fixedImagePath, movingImagePath, outputDir, self.paramFileName, frameIdx-1 )
                
                print "cmd: %s" % ( cmd )

                p = subprocess.Popen( cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE )
                self.outstandingProcesses[ p ] = cmd
                
                frameIdx += frameIncrement
            else:
                # too many outstanding processes, need to wait
                p = self.outstandingProcesses.keys()[ 0 ]
                p.wait()
                del self.outstandingProcesses[ p ]
                
                # Clean out all the processes which are done
                todelete = []
                for p in iter(self.outstandingProcesses.keys()):
                    p.poll()
                    if p.returncode != None:
                        todelete.append( p )
                        
                for p in iter(todelete):
                    del self.outstandingProcesses[ p ]
                        

        # Wait for all the processes to complete
        for p in iter(self.outstandingProcesses.keys()):
            p.wait()

        # Move the files up one dir
        for filepath in iter( glob.glob( regdirname + '/' + self.outputDirPrefix + '.*/*.raw' ) ):
            file_dirname = os.path.dirname( filepath )
    
            file_dirname = os.path.basename( file_dirname )
                
            fileIdx = string.split( file_dirname, '.')[ 1 ]
            
            destpath = regdirname + "/data_" + str( fileIdx ) + ".raw"
            
            print destpath
            
            os.renames( filepath, destpath )

        return True

def usage():
    print "%s: <datadir>" % ( sys.argv[ 0 ] )

if len(sys.argv) < 2:
    usage()
    sys.exit(-1)

datadir = os.path.abspath( sys.argv[ 1 ] )

registrator = lfoi_elastix_registrator( datadir )

if len(glob.glob( datadir + "/*.tif" )) != 0:
    registrator.run_on_tif()
else:
    print "ERROR: Datadir type not recognized"
