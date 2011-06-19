#! /usr/bin/env python

import sys, getopt, math, datetime, os
sys.path.append('../')
from random import gauss

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import scikits.statsmodels.api as sm
import scipy as sp

_Functions = ['run', 'test_system3', 'test_parzen', 'test_divergence']
	
import theano.tensor as T
from theano import function

def run():
  print "Initializing"
  
  train_size = 1000
  sequence_length = 1
  gamma_quantile = 25
  test_size = 200

  import a_machine.system4 as system
  
  print "Importing & Normalizing Data"
  
  from santa_fe import getData
  data = getData('B1.dat')
  test = getData('B2.dat')
  median = np.median(data, axis=0)
  std = np.std(data, axis=0)

  # normalizing to median 0, std deviation 1
  normed_data = ( data - median ) / std
  
  
  print "Initializing Models"
  
  model = system.model(dimension=0, gamma_samples=1000, gamma_quantile=gamma_quantile, sequence_length=sequence_length) 
  model.train( normed_data, train_size )   
  
  print "Generating Predictions"
  
  # [test_point][dimension]
  test = test[:test_size+sequence_length,:]
  #test = data[:test_size+sequence_length,:]
  normed_test = (test - median) / std
  predictions = model.predict(normed_test)
  
  # denormalize
  #predictions = ( std[0] * predictions ) + median[0]

  errors = np.abs( normed_test[sequence_length : predictions.shape[0]+sequence_length, 0] - predictions )
  
  print "Results!  Loss/point: %s (in normed space)" % ( errors.sum(0) / test_size )
  
  x = np.arange( predictions.shape[0] )
  
  plt.plot(x,normed_test[sequence_length : predictions.shape[0]+sequence_length, 0], 'k', alpha=.4)
  #for i in range(predictions.shape[1]):
  #  for j in range(predictions.shape[2]):
  #    plt.plot(x,predictions[:,i,j])

  plt.plot(x,predictions)
  
  plt.show()

  return
  
def test_system3():
  print "Initializing"
  
  train_size = 500
  sequence_length = 2
  gamma_quantile = 50
  test_size = 500

  import a_machine.system3 as system
  
  print "Importing & Normalizing Data"
  
  from santa_fe import getData
  data = getData('B1.dat')
  test = getData('B2.dat')
  median = np.median(data, axis=0)
  std = np.std(data, axis=0)

  # normalizing to median 0, std deviation 1
  data = ( data - median ) / std
  
  
  print "Initializing Models"
  
  model = system.model(gamma_samples=1000, gamma_quantile=gamma_quantile, sequence_length=sequence_length) 
  model.train( data, train_size )   
  
  print "Generating Predictions"
  
  # [test_point][dimension]
  #normed_test = (test[:test_size,:] - median) / std
  normed_test = data[:test_size]
  predictions, risks = model.predict(normed_test)
  hybrid = ( predictions * risks ).sum(1) / risks.sum(1)
  
  # denormalize
  predictions = ( std.reshape(1,1,3) * predictions ) + median.reshape(1,1,3)
  hybrid = ( std.reshape(1,3) * hybrid ) + median.reshape(1,3)
  
  print "Results!"
  
  errors = np.abs( np.expand_dims( test[sequence_length : test_size], 1) - predictions )
  hybrid_error = np.abs( test[sequence_length : test_size] - hybrid )
  print hybrid.shape
  print hybrid_error.shape
  
  print ( hybrid_error.sum(0) / test_size )
  print ( errors.sum(0) / test_size )
  print std.astype('int')
  
  x = np.arange(test_size-sequence_length)
  
  for i in range(data.shape[1]):
    fig = plt.subplot(data.shape[1],1,i+1)
    
    fig.plot(x, test[sequence_length : test_size,i], 'k--')
    for j in range(predictions.shape[1]):
      fig.plot(x, predictions[:,j,i] )

    fig.plot(x, hybrid[:,i], 'r', lw=2)
  plt.show()

  
def test_divergence():
  print "Starting"
  
  import cs_divergence, parzen_probability
  
  print "compiled for GPU"
  
  xrange = [0,1]
  xstep = .01
  xN = int((xrange[1]-xrange[0])/xstep)
  x=np.arange(xrange[0],xrange[1],xstep).astype('float32')
  gamma = .1
  distN = 20
  baseN = 20
  
  # 5 distributions containing 5 1-d points
  distributions = np.array( [
    np.random.normal(.2, .05, distN), 
    np.random.normal(.4, .05, distN), 
    np.random.normal(.6, .05, distN),  
    np.random.normal(.8, .05, distN)
  ] ).reshape(4,distN,1).astype('float32')
  # distribution with 5 1-d points
  base = np.random.normal(.8, .05, baseN).reshape(baseN,1).astype('float32')
  
  divergences = cs_divergence.from_many(distributions, base, gamma=gamma)
  
  for i in range(4):
    ax = plt.subplot(2,2,i+1, title="Divergence: %s" % divergences[i])
    
    ax.plot(x, parzen_probability.from_many( distributions[i].reshape(1,distN,1), x.reshape(xN,1), gamma=gamma ).reshape(xN), 'b' )
    ax.plot(x, parzen_probability.from_many( base.reshape(1,baseN,1), x.reshape(xN,1), gamma=gamma ).reshape(xN), 'g--' )
    ax.axis([0,1,0,None])
  
  plt.show()
  
  
def test_parzen():
	print "Starting"
	
	import parzen_probability
	
	print "compiled for GPU"
	
	parzen_probability.graph(np.random.rand(10,2).astype('float32'), .1, 100, 100)
  
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
