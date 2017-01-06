"""
v 0.8
Date: 9/1/2015
Edited 7/16
Tested on a 64-bit Windows 7 computer
Python 2.7.8, NumPy 1.9.0, and MatPlotLib 1.4.0
But really just get Anaconda: http://continuum.io/downloads
Tested on RSA306B
Program: ASK Demodulator
This program uses blocks of IQ data to demodulate and create a
symbol table for a simple 2ASK signal. User must adjust 
acquisition parameters, symbol rate, and decision threshold.
"""

from ctypes import *
import os
import numpy as np
import matplotlib.pyplot as plt

os.chdir("C:\\Tektronix\\RSA_API\\lib\\x64")
rsa = cdll.LoadLibrary("RSA_API.dll")

########################################################################
#############################FUNCTIONS##################################
########################################################################
def search_connect():
	#search/connect variables
	numFound = c_int(0)
	intArray = c_int*10
	deviceIDs = intArray()
	#this is absolutely asinine, but it works
	deviceSerial = c_char_p('longer than the longest serial number')
	deviceType = c_char_p('longer than the longest device type')
	apiVersion = c_char_p('api version')

	#get API version
	rsa.DEVICE_GetAPIVersion(apiVersion)
	print('API Version {}'.format(apiVersion.value))

	#search
	ret = rsa.DEVICE_Search(byref(numFound), deviceIDs, 
		deviceSerial, deviceType)

	if ret != 0:
		print('Error in Search: ' + str(ret))
		exit()
	if numFound.value < 1:
		print('No instruments found. Exiting script.')
		exit()
	elif numFound.value == 1:
		print('One device found.')
		print('Device type: {}'.format(deviceType.value))
		print('Device serial number: {}'.format(deviceSerial.value))
		ret = rsa.DEVICE_Connect(deviceIDs[0])
		if ret != 0:
			print('Error in Connect: ' + str(ret))
			exit()
	else:
		print('2 or more instruments found. Enumerating instruments, please wait.')
		for inst in xrange(numFound.value):
			rsa.DEVICE_Connect(deviceIDs[inst])
			rsa.DEVICE_GetSerialNumber(deviceSerial)
			rsa.DEVICE_GetNomenclature(deviceType)
			print('Device {}'.format(inst))
			print('Device Type: {}'.format(deviceType.value))
			print('Device serial number: {}'.format(deviceSerial.value))
			rsa.DEVICE_Disconnect()
		#note: the API can only currently access one at a time
		selection = 1024
		while (selection > numFound.value-1) or (selection < 0):
			selection = int(input('Select device between 0 and {}\n> '.format(numFound.value-1)))
		rsa.DEVICE_Connect(deviceIDs[selection])
		
		return rsa


def hi_lo_calculator(data):
	#This function uses the histogram method to determine hi/low
	DEFAULT = 40
	hi = lo = DEFAULT
	abs_half = (np.amax(data)+np.amin(data))/2
	hist, bins = np.histogram(data,50)
	plt.hist(data, 50)
	plt.show()
	while (hi == DEFAULT) or (lo == DEFAULT):
		index = np.argmax(hist)
		amp = bins[index]
		if amp >= abs_half:
			if hi == DEFAULT:		
				hi = amp
			hist = np.delete(hist,index)
			bins = np.delete(bins,index)
		elif amp < abs_half:
			hist = np.delete(hist,index)
			bins = np.delete(bins,index)
			lo = amp	
	print('Hi: {} Lo: {}'.format(hi,lo))
	return hi, lo

def firstedge_finder(data, hi, lo, thresh):
	"""
	This function finds the first rising edge of the AvT trace and
	returns the rising edge index and the decision threshold (decPoint)
	"""
	#decPoint = (hi+lo)*.5
	decPoint = hi-thresh
	saved = data[0]

	for index in range(len(data)):
		if data[index] <= decPoint:
			saved = data[index]
		else:
			if saved <= decPoint:
				break

	#print('Hi: {0} Lo: {1} decPoint: {2}'.format(hi,lo,decPoint))
	return index, decPoint

def ask_decode(data, symRate, sampRate, thresh):
	"""
	This function demods the AvT trace based on symbol rate, sample rate,
	and decision threshold as a percentage of amplitude. It begins demod
	at the first rising edge of the AvT trace. It returns the symbol table 
	and info needed to annotate the resulting plot.
	"""
	saPerSym = sampRate/symRate
	hi, lo = hi_lo_calculator(data)
	startIndex, decPoint = firstedge_finder(data, hi, lo, thresh)
	decOffset = int((saPerSym/2))
	numSym = int(len(data)/saPerSym)
	validSym = numSym - int((startIndex+decOffset)/saPerSym)
	symTable = np.zeros(validSym)

	for i in range(validSym):
		if i == 0:
			index = startIndex+decOffset
		index = i*saPerSym+decOffset+startIndex
		decision = data[index]
		if decision >= decPoint:
			symTable[i] = 1
		else:
			symTable[i] = 0

	annotations = [decPoint, startIndex, decOffset, validSym, saPerSym]
	return symTable, annotations

def inst_setup(measFreq, refLevel, measBW, measTime, trigLevel):
	#reset the instrument and open displays
    #rsa.CONFIG_Preset()
	rsa.CONFIG_SetReferenceLevel(c_double(refLevel))
	rsa.CONFIG_SetCenterFreq(c_double(measFreq))
	rsa.IQBLK_SetIQBandwidth(c_double(measBW))
	recordLength = c_int(int(measBW*1.4*measTime))
	rsa.IQBLK_SetIQRecordLength(recordLength)
	rsa.TRIG_SetTriggerMode(c_int(1))	#1=triggered
	rsa.TRIG_SetIFPowerTriggerLevel(c_double(trigLevel))
	rsa.TRIG_SetTriggerSource(c_int(1))	#1=internal
	rsa.TRIG_SetTriggerPositionPercent(c_double(0))

	return recordLength.value


def acquire_iq(recordLength):
	#start acquisition
	timeoutMsec = c_int(200)
	ready = c_bool(False)
	rsa.DEVICE_Run()
	rsa.IQBLK_AcquireIQData()
	#check for data ready
	while ready.value == False:
		ret = rsa.IQBLK_WaitForIQDataReady(timeoutMsec, byref(ready))
	#Get IQ arrays from RSA
	iqArray =  c_float*recordLength
	iData = iqArray()
	qData = iqArray()

	actLength = c_int(0)
	rsa.IQBLK_GetIQDataDeinterleaved(byref(iData), byref(qData), byref(actLength), c_int(recordLength))
	rsa.DEVICE_Stop()

	#convert ctypes array to numpy array for ease of use
	I = np.ctypeslib.as_array(iData)
	Q = np.ctypeslib.as_array(qData)

	return I, Q
	

def get_avt(I, Q, recordLength):
	#convert IQ to amplitude vs time and return both amplitude and time arrays
	avt = 20*np.log10(((I**2 + Q**2)/100)/.001)
	iqSampleRate = c_double(0)
	rsa.IQBLK_GetIQSampleRate(byref(iqSampleRate))
	time = np.linspace(0,recordLength/iqSampleRate.value,recordLength)

	return avt, time, iqSampleRate.value


def err_check(instrument):
	err_string = instrument.ask('system:error:all?').split(',')
	if err_string[0] != '0':
		status_text = (err_string[1])
	else:
		status_text = 0

	return status_text

def ask_plot(x, y, annotations, acq_time):
	plt.plot(x, y)
	plt.axhline(y=annotations[0])
	#plt.axvline(x=x[annotations[1]])
	#for i in range(annotations[3]):
	#	plt.axvline(x=
	#		x[annotations[1]+annotations[2]+annotations[4]*i])
	plt.suptitle('Amplitude vs Time')
	plt.ylabel('Amplitude (dBm)')
	plt.xlabel('Time (s)')
	#plt.xlim(0,acq_time)
	plt.show()

########################################################################
########################################################################
########################################################################

def main():
	"""
	########################################################################
	###################configure acquisition parameters#####################
	########################################################################
	"""
	measFreq = 2.4553e9
	refLevel = 0
	measBW = 40e6
	measTime = 1e-3
	trigLevel = -10
	symRate = 100
	thresh = 3
	"""
	########################################################################
	########################################################################
	########################################################################
	"""
	#establish communication with RSA
	rsa = search_connect()
	recordLength = inst_setup(measFreq, refLevel, measBW, measTime, trigLevel)
	#status_text = err_check(rsa)
	#if status_text != 0:
	#	print status_text
	I, Q = acquire_iq(recordLength)
	avt, avtTime, Fs = get_avt(I, Q, recordLength)

	#demodulate and get symbol table
	symbol_table, annot = ask_decode(avt, symRate, Fs, thresh)

	#plot the data
	ask_plot(avtTime, avt, annot, measTime)


if __name__ == '__main__':
	main()