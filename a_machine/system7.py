#! /usr/bin/env python
import sys
from math import *
from datetime import *
import numpy as np
import numpy.linalg as la
import scikits.statsmodels.api as sm
import scipy as sp

import matplotlib.pyplot as plt
import matplotlib.cm as cm


from gpu_funcs import kernel_matrix
from cvxopt import matrix, solvers
solvers.options['abstol']=1e-10
solvers.options['reltol']=1e-10
solvers.options['feastol']=1e-10

def rank(A, tol=1e-10):
  u, s, v = np.linalg.svd(A)
  return np.sum(s > tol)
  
class model:
  def __init__(self, dimension, gamma_samples=1000, gamma_quantile=100):
    self.dimension = dimension
    self.gamma_samples = gamma_samples
    self.gamma_quantile = gamma_quantile
    self.gammas = None
    self.sequences = None
    
    self.active_slices = None
    self.all_slices = None
    
  # data: [observation][dimension]
  def train(self, data, slices=[[0,[0]]]):
    #self.gammas = self.determine_gammas_from(data)
    self.gammas = [.1,]
    print "Gammas determined: %s" % str(self.gammas)
    
    # [gamma][sequence offset][dimension]
    #self.active_slices = np.mgrid[0:1,0:data.shape[1]].T.reshape(data.shape[1],2).tolist()
    # Make a single slice consisting of the 1st sequence element and all 3 dimensions
    #self.active_slices = [ [0,[0,1]], [0,[0]] ]
    self.active_slices = slices
    
    # Working with 1 sequence element for now
    sequences = data[:-1].astype('float32').reshape(data.shape[0]-1,1)
    labels = data[1:].astype('float32').reshape(data.shape[0]-1,1)
    
    l = sequences.shape[0]
    jitter = ( ( np.random.randn(l,1) / 10 ) ).astype('float32')
    jittery = ( ( np.random.randn(l,1) / 10 ) ).astype('float32')
    self.sequences = sequences + jitter
    self.labels = labels + jittery
    
    
    print "Calculating kernel matrix"
    kx = kernel_matrix(self.sequences.reshape(l,1,1), self.sequences.reshape(l,1,1), self.gammas[-1])
    ky = kernel_matrix(self.labels.reshape(l,1,1), self.labels.reshape(l,1,1), self.gammas[-1])
    sigma = 1000
    
    print "Constructing constraints"
    
    P = self.labels * self.labels.T * kx
    
    q = np.zeros((l,1))

    G_1 = self.labels.T * kx
    
    G_2 = -self.labels.T * kx
    
    h_1 = sigma + self.labels
    
    h_2 = sigma - self.labels
    
    G = np.vstack([G_1,G_2])
    h = np.vstack([h_1,h_2])
    
    A = kx
    
    b = np.ones((l,1))
        
    print "p(A[0])=%s" % A.shape[0]
    print "n(G[1],A[1])=%s or %s" % (G.shape[1], A.shape[1])
    print "rank P: %s" % rank(P)
    print "rank G: %s" % rank(G)
    print "rank A: %s" % rank(A)
    print "rand kernel: %s" % rank(kx)
    print "unique source: %s" % np.unique(self.sequences).shape[0]
    
    print "Solving"
    solution = solvers.coneqp( 
      matrix(P.astype('float')), 
      matrix(q.astype('float')), 
      matrix(G.astype('float')), 
      matrix(h.astype('float')),
      None,
      matrix(A.astype('float')),
      matrix(b.astype('float'))
    )
    
    print "Handling Solution"
    if solution['status'] == 'optimal':
      X = np.array( solution['x'] )
      #R_emp = np.array( solution['x'][-1] )
      #print solution['x']
      self.SV_mask = ( np.abs(X) < 1e-8 )
      self.beta = np.ma.compress_rows( np.ma.array( X, mask = self.SV_mask ) ).astype('float32')
      self.SVx = np.ma.compress_rows( np.ma.array( sequences, mask = np.repeat( self.SV_mask, sequences.shape[1], 1) ) ).astype('float32')
      self.SVy = np.ma.compress_rows( np.ma.array( labels.reshape(labels.shape[0],1), mask = self.SV_mask ) ).astype('float32')
      self.nSV = self.beta.shape[0]
    
      #print self.beta
      #print self.SVx.shape
      #print self.SVy.shape
      #print self.nSV
      #print self.SV_mask
      #print solution['x']
    print "--> SVM Trained: %s SV's of %s" % ( self.nSV, self.SV_mask.shape[0] ) 


  # data: [observation][dimension]      
  def predict(self, data):
    
    # [sequence][point][dimension]
    #points = self.make_sequences(data)
    points = data.astype('float32')
    
    
    #print points.shape
    #print self.sequences.shape
    
    #print points.shape
    #print self.SVx.reshape(self.nSV,1,1).shape
    
    kk = kernel_matrix( points, self.SVx.reshape(self.nSV,1,1), self.gammas[-1] )
    
    #print self.SVy.shape
    print self.beta
    
    prediction = (self.labels.T * self.beta.T * kk ).sum(1) / (self.beta.T * kk).sum(1)
    
    #print prediction.shape
    
    return prediction

  def random_sample(self, sequences, labels, samples):
    full = np.hstack([sequences, np.expand_dims(labels,1)])
    np.random.shuffle(full)
    self.sequences = full[:samples,:-1,:]
    self.labels = full[:samples,-1,self.dimension] 
    (full[:samples,:-1,:], full[:samples,-1,self.dimension] )
    
    
  def make_sequences(self, data):
    sequences = data.reshape(data.shape[0], 1, data.shape[1])
    for i in np.arange( 1, self.sequence_length):
      sequences = np.hstack([ sequences, np.roll(data, -i, 0).reshape(data.shape[0], 1, data.shape[1]) ])
    
    return np.array( sequences )[:-self.sequence_length,:,:].astype('float32')

  def make_subsets(self, X, Y):
    kk = []
    for s in self.active_slices:
      if isinstance(s[1], int):
        subset_X = X[:,s[0],s[1]].reshape(X.shape[0], s[0]+1, 1 )
        subset_Y = Y[:,s[0],s[1]].reshape(Y.shape[0], s[0]+1, 1 )
      else:
        subset_X = X[:,s[0],s[1]].reshape(X.shape[0], s[0]+1, len(s[1]))
        subset_Y = Y[:,s[0],s[1]].reshape(Y.shape[0], s[0]+1, len(s[1]))
      
      for gamma in self.gammas:
        # NOTE:  returning to test on single matrix
        kk.append( kernel_matrix(subset_X, subset_Y, gamma) )

    
    # Construct the sparse block diagonal of the kernel matrices and extend the labels to match
    # return bdiag(kk, format='csr')
    
    if len(kk) > 1:
      row = np.hstack(kk)
      
      zeros = np.zeros( (kk[0].shape[0] * (len(kk)-1), kk[0].shape[1] * (len(kk)-1)) )
      k_column = np.vstack( kk[1:] )

      base = sp.sparse.csr_matrix( np.hstack( 
          [ k_column, zeros ] 
      ) )
      KK = sp.sparse.vstack([row,base]).todense()

      return KK
    else:
      return kk[0]
    
  def determine_gammas_from(self, data):
    g_samples = data.copy()
    np.random.shuffle(g_samples)
    g_samples = g_samples[:self.gamma_samples]
    g_diff = np.abs( g_samples.reshape(g_samples.shape[0],1,g_samples.shape[1]) - g_samples.reshape(1,g_samples.shape[0],g_samples.shape[1]) )
    g_diff = g_diff.reshape(g_samples.shape[1]*g_samples.shape[0]**2)
    g_percentiles = np.arange(self.gamma_quantile / 2,100,self.gamma_quantile).astype('float')
    
    gammas = []
    for i in g_percentiles:
      gammas.append( sp.stats.stats.scoreatpercentile(g_diff, i) )   
    
    return np.array(gammas)
    
