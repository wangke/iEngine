#! /usr/bin/env python

# Based on two papers:
# (1) Support Vector Density Estimation, and
# (2) Density Estimation using Support Vector Machines
# Both by Weston et. all, the first from '99 and the second from '98
# They seem to be reprints of the same paper

# NOTE: the technique in (1)-1.9 is described as a faster way to compute the
# same thing on large datasets - if the LP performance is bad, you might try
# implementing the other version

import sys, getopt, math, datetime, os, cmath
from random import gauss

import numpy
import scipy
import scipy.special
import scipy.stats
import cvxopt
import cvxmod
from cvxopt import *

from numpy import *

import matplotlib.pyplot as plt

_Functions = ['run']
	
class svm:
	def __init__(self,data=list(),C=1., Lambda = 1., gamma =[1./2, 1./4, 1./8, 1./16] ):
		self.data = data
		self.Fl = None
		self.SV = None
		self.betas = None
		
		self.C = C
		self.Lambda = Lambda
		self.gamma = gamma
		
		self._compute()
	
	def _K(self,X,Y,gamma):
		diff = X - Y
		N = len(X)
		return [ ( 1 / ( 1 + exp( -gi * diff ) ) ).reshape(N,N) for gi in gamma ]
		
	def Pr(self,x):
		diff = self.data - x
		return array( [ ( self.betas[i] * ( -self.gamma[i] / ( 2 + exp( self.gamma[i] * diff ) + exp( -self.gamma[i] * diff ) ) ) ).sum() for i in range(len(self.gamma)) ] ).sum()
		
	def __iadd__(self, points):
		# overloaded '+=', used for adding a vector list to the module's data
		# 
		# @param points		A LIST of observation vectors (not a single ovservation)
		self.data += points
	
	def _compute(self):
		start = datetime.datetime.now()
		#UNKNOWN: what are \alpha^*, \xi ???   check Vapnik regression
		# * used to designate negative values
		
		# Given
		# ( (x_1,F_\ell(x_1),\epsilon_1),...,(x_\ell),F_\ell(x_\ell),\epsilon_\ell) )
		# \theta(x) = indicator function; 1 if positive, 0 otherwise
		# F_\ell(x) = \frac{1}{\ell} \sum_{i=1}^{\ell} \theta(x - x_i)		NOTE: if d>1, \theta returns 0 if any dimension less than 0
		# \epsilon = \lambda \sigma_i = \lambda \sqrt{ \frac{1}{\ell} F_\ell(x_i)(1-F_\ell(x_i) ) }
		
		C = self.C
		Lambda = self.Lambda
		gamma = self.gamma
		Kcount = len( gamma )
		(N,d) = self.data.shape
		X = self.data
		
		# CMF of observations X
		Xcmf = ( (X.reshape(N,1,d) > transpose(X.reshape(N,1,d),[1,0,2])).prod(2).sum(1,dtype=float) / N ).reshape([N,1])
		
		# epsilon of observations X
		e = Lambda * sqrt( (1./N) * ( Xcmf ) * (1.-Xcmf) ).reshape([N,1])
		
		K = self._K( Xcmf.reshape(N,1,d), transpose(Xcmf.reshape(N,1,d), [1,0,2]), gamma )

		xipos = cvxmod.optvar( 'xi+', N,1)
		xipos.pos = True
		xineg = cvxmod.optvar( 'xi-', N,1)
		xineg.pos = True
			
		alphas = list()
		expr = ( C*cvxmod.sum(xipos) ) + ( C*cvxmod.sum(xineg) )
		ineq = 0
		eq = 0
		
		for i in range( Kcount ):
			alpha = cvxmod.optvar( 'alpha(%s)' % i, N,1)
			alpha.pos = True
			
			alphas.append( alpha )
			expr += ( float(1./gamma[i]) * cvxmod.sum( alpha ) )
			ineq += ( cvxopt.matrix( K[i], (N,N) ) * alpha )
			eq += cvxmod.sum( alpha )
			
		objective = cvxmod.minimize( expr )
		
		ineq1 = ineq <= cvxopt.matrix( Xcmf + e ) + xineg
		ineq2 = ineq >= cvxopt.matrix( Xcmf - e ) - xipos
		eq1 = eq == cvxopt.matrix( 1.0 )
		

		# Solve!
		p = cvxmod.problem( objective = objective, constr = [ineq1,ineq2,eq1] )
		
		start = datetime.datetime.now()
		p.solve()
		duration = datetime.datetime.now() - start
		print "optimized in %ss" % (float(duration.microseconds)/1000000)
		
		#betas = [ ma.masked_less( alpha.value, 1e-7 ) for alpha in alphas ]
		#masks = [ ma.getmask( beta ) for beta in betas ]
		#data = ma.array(X,mask=mask)
			
		self.Fl = Xcmf
		self.betas = [ ma.masked_less( alpha.value, 1e-7) for alpha in alphas ]
		
		print "SV's found: %s" % [ len( beta.compressed()) for beta in self.betas ]
		
def run():
	mod = svm( array([[gauss(0,1)] for i in range(10) ]).reshape([10,1]) )
	
	X = arange(-5.,5.,.05)
	Y_cmp = [ mod.Pr(x) for x in X ]
	
	#n, bins, patches = plt.hist(mod.data, 40, normed=1, facecolor='green', alpha=0.5)
	#bincenters = 0.5*(bins[1:]+bins[:-1])
	#plt.plot(bincenters, n, 'r', linewidth=1)
	
	#plt.plot( mod.SV, [ mod.Pr(x ) for x in  mod.SV ], 'o' )
	
	plt.plot(mod.data,mod.Fl, 'o' )
	plt.plot(X,Y_cmp, 'r--')
	#plt.show()
	
	
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
