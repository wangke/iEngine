#! /usr/bin/env python

import sys, getopt, math, datetime, os
from random import gauss

import a_machine as am

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.cm as cm

_Functions = ['run']
	
import theano.tensor as T
from theano import function

def run():
	print "Starting"
	
	xrange = [0,1]
	yrange = [0,1]
	xstep = .01
	ystep = .01
	xN = int((xrange[1]-xrange[0])/xstep)
	yN =  int((yrange[1]-yrange[0])/ystep)
	X = np.dstack(np.mgrid[xrange[0]:xrange[1]:xstep,yrange[0]:yrange[1]:ystep]).reshape([ xN *yN,2])
	x = np.arange(xrange[0],xrange[1],xstep)
	y = np.arange(yrange[0],yrange[1],ystep)
	
	print "Loading Dataset"
	# Retrieve dataset
	#data = getData('B1.dat')[:100]
	#data = list()
	#for i in range(100):
	#	data.append( array( [gauss(2.0,.1), gauss(0.0,.1) ]) )
	#for i in range(100):
	#	data.append( array( [gauss(0.0,.1), gauss(2.0,.1) ]) )
	##data = np.random.rand(10,3).astype('float32')
	
	observations = np.random.rand(1,10,1,2).astype('float32')
	#test_points = observations.reshape(1,1,10,2).astype('float32')
	test_points = X.astype('float32').reshape(1,1,xN*yN,2)
	
	pdf = am.parzen_function(observations,test_points)

	z = pdf.reshape([xN,yN]).T
	
	
	CS = plt.contour(x,y,z,10)
	plt.scatter( observations[0,:,0,0], observations[0,:,0,1] )
	
	plt.clabel(CS, inline=1, fontsize=10)
	plt.axis( [xrange[0],xrange[1],yrange[0],yrange[1]] )
	plt.show()
  
def help():
	print __doc__
	return 0
	
def process(arg='run'):
	if arg in _Functions:
		globals()[arg]()
	
class Usage(Exception):
    def __init__(self, msg):
        self.msg = msg

def main(argv=None):
	if argv is None:
		argv = sys.argv
	try:
		try:
			opts, args = getopt.getopt(sys.argv[1:], "hl:d:", ["help","list=","database="])
		except getopt.error, msg:
			raise Usage(msg)
		
		# process options
		for o, a in opts:
			if o in ("-h", "--help"):
				for f in _Functions:
					if f in args:
						apply(f,(opts,args))
						return 0
				help()
		
		# process arguments
		for arg in args:
			process(arg) # process() is defined elsewhere
			
	except Usage, err:
		print >>sys.stderr, err.msg
		print >>sys.stderr, "for help use --help"
		return 2

if __name__ == "__main__":
	sys.exit(main())
