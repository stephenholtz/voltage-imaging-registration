#! /usr/bin/env python

import sys
import glob
import os
import string
import time
import shutil
import subprocess
import StringIO

class lfoi_path_metadata:
    def __init__(self, index, name, regname):
        self.index   = index
        self.name    = name
        self.regname = regname
        
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

        # Figure out the input directory structure 
        # and save the results in python structures
        sorted_scan_dirs = []
        scan_dirs = glob.glob(self.datadir + '/scan*')
        for scan_dir in iter(scan_dirs):
            # print scan_dir
            scan_dir_basename = os.path.basename( scan_dir )            
            idx_split = string.split( scan_dir_basename, 'scan' )
            
            # print idx_split
            scanId   = int( idx_split[ 1 ] )

            scan_regdir_name = regdirname + '/scan_reg_' + str( scanId )

            sorted_scan_dirs.append( lfoi_path_metadata( scanId, scan_dir, scan_regdir_name ) )

            # create scan_reg directory to be filled during registration
            if os.path.isdir( scan_regdir_name ):
                shutil.rmtree( scan_regdir_name )

            os.mkdir( scan_regdir_name )
            
        sorted_scan_dirs.sort()
                
        depth_files_per_scan_dir = []
        depth_num = -1
        for scan_dir in iter(sorted_scan_dirs):
            # print scan_dir.name
            files_in_scan_dir = glob.glob(scan_dir.name + '/*_*.tif')

            sorted_depth_files = []
            for filepath in iter(files_in_scan_dir):
                filename = os.path.basename( filepath )

                # print 'filename', filename
                underscore_split = string.split( filename, '_' )
            
                # print 'underscore_split: ', underscore_split
                fileidx   = int( string.split( underscore_split[ -1 ], '.' )[ 0 ] )

                sorted_depth_files.append( lfoi_path_metadata( fileidx, filepath, 'none' ) )
    
                sorted_depth_files.sort()

            depth_files_per_scan_dir.append( sorted_depth_files )
            depth_num = len( sorted_depth_files )
 
        # Register the scans, depth by depth
        depthIdx = 0
        elastixIdx = 0
        DEPTH_LIMIT = depth_num
        SCAN_LIMIT = len(depth_files_per_scan_dir)

        while depthIdx < DEPTH_LIMIT:
            
            scanIdx = 1
            fixedImagePath = depth_files_per_scan_dir[ 0 ][ depthIdx ].name
            while scanIdx < SCAN_LIMIT:
                
                ###
                if len(self.outstandingProcesses) < self.MAX_OUTSTANDING_PROCESSES:
                    movingImagePath = depth_files_per_scan_dir[ scanIdx ][ depthIdx ].name
                    depth_idx       = depth_files_per_scan_dir[ scanIdx ][ depthIdx ].index
                                
                    outputDir = os.path.abspath( regdirname + "/" + self.outputDirPrefix + ".depth_" + str( depth_idx ) + ".mov_scan_" + str(scanIdx+1) )

                    if os.path.isdir( outputDir ):
                        shutil.rmtree( outputDir )
                    
                    os.mkdir( outputDir )
                    
                    cmd = 'elastix -f %s -m %s -out %s -p %s > run.%d.log 2>&1' \
                        % ( fixedImagePath, movingImagePath, outputDir, self.paramFileName, elastixIdx )

                    elastixIdx = elastixIdx + 1
                
                    print "cmd: %s" % ( cmd )

                    p = subprocess.Popen( cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE )
                    self.outstandingProcesses[ p ] = cmd                
                
                    scanIdx = scanIdx + 1
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
            # format of output dir: elastix_out.depth_<>.mov_scan_<>
            for filepath in iter( glob.glob( regdirname + '/' + self.outputDirPrefix + '.*/*.tif' ) ):
                file_dirname_full = os.path.dirname( filepath )
                file_dirname = os.path.basename( file_dirname_full )

                split_by_dot = string.split(file_dirname, '.')

                depthIdx_in_str = int(string.split( split_by_dot[1], '_')[-1])

                scanIdx_in_str = int(string.split( split_by_dot[2], '_')[-1])

                destpath = sorted_scan_dirs[ scanIdx_in_str-1 ].regname + "/depth_reg_" + str( depthIdx_in_str ) + ".tif"
            
                print destpath
            
                # Copy the file to the proper scan reg dir
                os.renames( filepath, destpath )

                # Remove the elastix metadata
                shutil.rmtree( file_dirname_full )


            # take out the elastix output in run.*.log
            runlogdirs = glob.glob('run.*.log')
            for runlogdir in iter( runlogdirs ):
                os.remove( runlogdir )
            
            depthIdx = depthIdx + 1

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
