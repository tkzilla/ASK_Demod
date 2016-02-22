"""
Date: 9/1/2015
Tested on a 64-bit Windows 7 computer
using TekVISA 4.0.4 with Python 2.7.6, PyVISA 1.6, 
NumPy 1.8.1, and MatPlotLib 1.3.1
But really just get Anaconda: http://continuum.io/downloads
And PyVISA: https://pypi.python.org/pypi/PyVISA
Tested on RSA5126B and RSA306/SignalVu-PC
Program: ASK Demodulator
This program uses the amplitude vs time trace to calculate the
symbol table for a simple 2ASK modulated signal. User must 
adjust acquisition parameters, symbol rate, and decision threshold.
"""

import visa
import numpy as np
import matplotlib.pyplot as plt

########################################################################
#############################FUNCTIONS##################################
########################################################################
def Tek_Instrument(descriptor,timeout):
	rm = visa.ResourceManager()
	instrument = rm.open_resource(descriptor)
	instrument.timeout = timeout
	id_string = instrument.ask('*IDN?')
	print(id_string)

	return instrument

def binblock_parser(rawdata,data_type,bytes_per_pt):
	#This function parses the binary block data defined by IEE 488.2
	"""
	The raw data begins with a header that contains information that 
	is useful for transferring the waveform. We will need to read it 
	and then remove it from the actual waveform data.
	The first character in the header is a '#' character.
	The second character contains the number of digits in the number 
	of data points in the record (for example if the number of data 
	points was 100, this character would be 3).	The next number is 
	the number of data points whose length is specified by the second 
	character. A full example: If I had a 1000 point-long waveform, 
	the header would be '#41000'
	"""
	#determine the length of the header by adding 2 to the number of
	#digits in the waveform length (one for the # character and one 
	#for the character being read)
	headerlength = 2 + int(rawdata[1])
	#print(rawdata[0:10])
	bytes = int(rawdata[2:headerlength])
	numberofpoints = bytes/bytes_per_pt
	#strip out the header
	#the last data point is excluded because it is a newline character
	rawdata = rawdata[headerlength:-1]
	output = np.fromstring(rawdata, dtype = data_type)
	#output = np.array(unpack('<{0}f'.format(numberofpoints), rawdata))
	return output, numberofpoints

def hi_lo_calculator(data):
	#This function uses the histogram method to determine hi/low
	DEFAULT = 40
	hi = lo = DEFAULT
	abs_half = (np.amax(data)+np.amin(data))/2
	#print('Absolute halfway point {0}'.format(abs_half))
	hist, bins = np.histogram(data,50)
	#print(hist)
	#print(bins)
	while (hi == DEFAULT) or (lo == DEFAULT):
		index = np.argmax(hist)
		amp = bins[index]
		if amp >= abs_half:
			if hi == DEFAULT:		
				hi = amp
				#print('Hist max: {0} Argument: {1}'.format(np.amax(hist),np.argmax(hist)))
				#print('Bins max: {0} Argument: {1}'.format(bins[np.argmax(hist)],np.argmax(hist)))
			hist = np.delete(hist,index)
			bins = np.delete(bins,index)
		elif amp < abs_half:
			#print('Hist max: {0} Argument: {1}'.format(np.amax(hist),np.argmax(hist)))
			#print('Bins max: {0} Argument: {1}'.format(bins[np.argmax(hist)],np.argmax(hist)))
			hist = np.delete(hist,index)
			bins = np.delete(bins,index)
			lo = amp
	
	#print('Hi: {0} Lo: {1}'.format(hi,lo))
	return hi, lo

def firstedge_finder(data, hi, lo, thresh):
	"""
	This function finds the first rising edge of the AvT trace and
	returns the rising edge index and the decision threshold (d_point)
	"""
	d_point = (hi+lo)*(1-thresh)
	saved = data[0]

	for index in range(len(data)):
		if data[index] <= d_point:
			saved = data[index]
		#elif data[index] > d_point:
		else:
			if saved <= d_point:
				break
		#else:
		#	print('This should not happen. Something is very wrong.')
	return index, d_point

def ask_decode(data, sym_rate, samp_rate, thresh):
	"""
	This function demods the AvT trace based on symbol rate, sample rate,
	and decision threshold as a percentage of amplitude. It begins demod
	at the first rising edge of the AvT trace. It returns the symbol table 
	and info needed to annotate the resulting plot.
	"""
	sa_per_sym = samp_rate/sym_rate
	hi, lo = hi_lo_calculator(data)
	start_index, d_point = firstedge_finder(data, hi, lo, thresh)
	dec_offset = int((sa_per_sym/2))
	num_sym = int(len(data)/sa_per_sym)
	valid_sym = num_sym - int((start_index+dec_offset)/sa_per_sym)
	#print('Start index: {0}'.format(start_index))
	#print('Samples per symbol: {0}'.format(sa_per_sym))
	#print('Number of symbols: {0}'.format(num_sym))
	#print('Decision offset: {0}'.format(dec_offset))
	#print('Valid number of symbols: {0}'.format(valid_sym))
	sym_table = np.zeros(valid_sym)

	for i in range(valid_sym):
		if i == 0:
			index = start_index+dec_offset
		index = i*sa_per_sym+dec_offset+start_index
		decision = data[index]
		if decision >= d_point:
			sym_table[i] = 1
		#elif decision < d_point:
		else:
			sym_table[i] = 0
		#else:
		#	print('This should not happen. Something is very wrong.')

	annotations = [d_point, start_index, dec_offset, valid_sym, sa_per_sym]
	return sym_table, annotations

########################################################################
########################################################################
########################################################################

def main():
	"""
	########################################################################
	#configure acquisition parameters
	########################################################################
	"""
	meas_freq = 1e9
	ref_level = 5
	meas_bandwidth = 20e6
	time_scale = 40e-6
	time_offset = 0
	trig_level = -10
	sym_rate = 6e6
	thresh = 0.9
	"""
	########################################################################
	########################################################################
	########################################################################

	"""
	#establish communication with RSA
	rsa = Tek_Instrument('GPIB8::1::INSTR', 10000)

	#reset the instrument and open displays
	rsa.write('system:preset')
	rsa.write('*cls')
	rsa.write('abort')
	rsa.write('display:general:measview:new toverview')
	rsa.write('display:general:measview:new avtime')

	#configure amplitude vs time measurement
	rsa.write('spectrum:frequency:center {0}'.format(meas_freq))
	rsa.write('input:rlevel {0}'.format(ref_level))
	rsa.write('spectrum:frequency:span {0}'.format(meas_bandwidth))
	rsa.write('sense:analysis:length {0}'.format(time_scale))
	rsa.write('sense:analysis:start {0}'.format(time_offset))

	#configure power level trigger
	rsa.write('trigger:event:input:type power')
	rsa.write('trigger:event:input:level {0}'.format(trig_level))
	rsa.write('initiate:continuous off')
	rsa.write('trigger:status off')

	#start acquisition
	rsa.write('initiate:immediate')
	rsa.ask('*opc?')

	#get raw amplitude vs time data from RSA
	rsa.write('sense:avtime:maxtracepoints nev')
	rsa.write('fetch:avtime:first?')
	rawdata = rsa.read_raw()
	#print('Raw data length: {0}'.format(len(rawdata)))

	avt, avt_points = binblock_parser(rawdata, np.float32, 4)

	#get the minimum and maximum time in the measurement from the RSA
	time_max = float(rsa.ask('display:avtime:x:scale:full?'))
	time_min = float(rsa.ask('display:avtime:x:scale:offset?'))
	Fs = len(avt)/time_max
	avt_time = np.linspace(time_min,time_max, len(avt))
	#avt_time = np.arange(time_min, (time_max-1/Fs), 1/Fs)
	#print('AvT Length is: {0}'.format(len(avt)))
	#print('avt_time Length is: {0}'.format(len(avt_time)))
	#print('Calculated IQ Sample rate: {0}'.format(Fs))

	#demodulate and get symbol table
	symbol_table, annot = ask_decode(avt, sym_rate, Fs, thresh)
	print('Symbol Table:\n{0}'.format(symbol_table))

	#plot the data
	plt.plot(avt_time, avt)
	plt.axhline(y=annot[0])
	plt.axvline(x=avt_time[annot[1]])
	for i in range(annot[3]):
		plt.axvline(x=avt_time[annot[1]+annot[2]+annot[4]*i])
	plt.suptitle('Amplitude vs Time')
	plt.ylabel('Amplitude (dBm)')
	plt.xlabel('Time (s)')
	plt.xlim(time_min,time_max)
	plt.show()

	print(rsa.ask('system:error:all?'))
	rsa.close()

main()