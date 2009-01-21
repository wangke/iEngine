#! /usr/bin/env python

import sys, getopt, math, datetime, os
from math import sqrt, sin
from random import gauss

from svm import *

from numpy import *
from pylab import *

from cvxopt.base import *
from cvxopt.blas import dot 
from cvxopt.solvers import qp

from cvxopt import solvers
solvers.options['show_progress'] = False

from santa_fe import getData
from components import inference_module

_Functions = ['run']
	
def run():
	print "Starting"
	
	print "Loading Dataset"
	# Retrieve dataset
	data = getData('B1.dat')[:100]
	#data = list()
	#for i in range(60):
	#	data.append( array( [gauss(2.0,.1), gauss(0.0,.1) ]) )
	#for i in range(60):
	#	data.append( array( [gauss(0.0,.1), gauss(2.0,.1) ]) )

	param = svm_parameter(svm_type=ONE_CLASS, kernel_type = RBF)
	prob = svm_problem( range(100), data)
	m= svm_model(prob,param)
	m.save('output.svm')
	
	mod = module('output.svm')
	
	mod.get_SV()
	mod.get_BSV()
	

def help():
	print __doc__
	return 0
	
def process(arg='run'):
	if arg in _Functions:
		globals()[arg]()
	
		
				for f in _Functions:
					if f in args:
						apply(f,(opts,args))
						return 0
		
			
	except Usage, err: