#! /usr/bin/env pythonimport sys, os, time, datetime, getopt
from cvxopt.base import matrix
from numpy import array
def parsePath(path):	# check if file exists	if os.path.isfile(path):		parse_file = file(path,'r')		data = parseFile( parse_file,path )	elif os.path.isdir(path):		for sub_path in os.listdir(path):			data = parsePath(os.path.join(path,sub_path))
	return data			def parseFile(parse_file,path):	data = list()	# parse file	for line in parse_file.readlines():
		text = line[:-4]		data.append( array( [ float(i) for i in text.split(" ") ] ) )
	return data
def getData(dataset=''):
	return parsePath(os.path.join('Santa_Fe_Competition',dataset))	 		
