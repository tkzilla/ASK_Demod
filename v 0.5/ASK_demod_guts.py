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
def VISA_search():
	rm = visa.ResourceManager()
	inst_list = rm.list_resources()
	return inst_list

def Tek_Instrument(descriptor):
	rm = visa.ResourceManager()
	try:
		instrument = rm.open_resource(descriptor)
		#instrument.timeout = 10
		id_string = instrument.ask('*IDN?')
		status_text = ('Connected to:\n{0}'.format(id_string))
		#instrument.timeout = timeout
		return instrument, status_text
	except visa.VisaIOError:
		status_text = 'Selected device not found.'
		instrument = -1
		return instrument, status_text

def binblock_parser(rawdata,data_type):
	"""
	This function parses the binary block data defined by IEE 488.2
	and requires NumPy
	rawdata is the raw binary data coming from an instrument
	data_type is a numpy data type in the format np.uint16, np.float32, etc.
	bytes_per_pt duh
	
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
	bytes_per_pt = int(str(data_type)[-4:-2])/8
	numberofpoints = bytes/bytes_per_pt
	#strip out the header
	#the last data point is excluded because it is a newline character
	rawdata = rawdata[headerlength:-1]
	output = np.fromstring(rawdata, dtype = data_type)
	return output

def hi_lo_calculator(data):
	#This function uses the histogram method to determine hi/low
	DEFAULT = 40
	hi = lo = DEFAULT
	abs_half = (np.amax(data)+np.amin(data))/2
	hist, bins = np.histogram(data,50)
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
	return hi, lo

def firstedge_finder(data, hi, lo, thresh):
	"""
	This function finds the first rising edge of the AvT trace and
	returns the rising edge index and the decision threshold (d_point)
	"""
	#d_point = (hi+lo)*(1-thresh)
	d_point = hi-thresh
	saved = data[0]

	for index in range(len(data)):
		if data[index] <= d_point:
			saved = data[index]
		else:
			if saved <= d_point:
				break

	#print('Hi: {0} Lo: {1} d_point: {2}'.format(hi,lo,d_point))
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
	sym_table = np.zeros(valid_sym)

	for i in range(valid_sym):
		if i == 0:
			index = start_index+dec_offset
		index = i*sa_per_sym+dec_offset+start_index
		decision = data[index]
		if decision >= d_point:
			sym_table[i] = 1
		else:
			sym_table[i] = 0

	#print('Symbol Table:\n{0}'.format(sym_table))

	annotations = [d_point, start_index, dec_offset, valid_sym, sa_per_sym]
	return sym_table, annotations

def inst_setup(inst, meas_freq, ref_level, meas_bw, meas_time, trig_level):
	#reset the instrument and open displays
	inst.write('system:preset')
	inst.write('*cls')
	inst.write('abort')
	inst.write('display:general:measview:new toverview')
	inst.write('display:general:measview:new avtime')
	inst.write('sense:avtime:maxtracepoints nev')

	#configure amplitude vs time measurement
	inst.write('spectrum:frequency:center {0}'.format(meas_freq))
	inst.write('input:rlevel {0}'.format(ref_level))
	inst.write('spectrum:frequency:span {0}'.format(meas_bw))
	inst.write('sense:analysis:length {0}'.format(meas_time))
	inst.write('sense:analysis:start 0')

	#configure power level trigger
	inst.write('trigger:event:input:type power')
	inst.write('trigger:event:input:level {0}'.format(trig_level))
	inst.write('initiate:continuous off')
	inst.write('trigger:status on')

	status_text = err_check(inst)
	return status_text

def get_avt(inst):
	#start acquisition
	inst.write('initiate:immediate')
	inst.ask('*opc?')

	#get raw amplitude vs time data from RSA
	inst.write('fetch:avtime:first?')
	rawdata = inst.read_raw()
	#print('Raw data length: {0}'.format(len(rawdata)))

	acq_time = np.zeros(2)
	acq_time[0] = float(inst.ask('display:avtime:x:scale:offset?'))
	acq_time[1] = float(inst.ask('display:avtime:x:scale:full?'))
	avt = binblock_parser(rawdata, np.float32)

	Fs = len(avt)/acq_time[1]
	avt_time = np.linspace(acq_time[0],acq_time[1], len(avt))

	return avt, avt_time, Fs, acq_time

def ask_plot(x, y, annotations, time_values):
	plt.plot(x, y)
	plt.axhline(y=annotations[0])
	plt.axvline(x=x[annotations[1]])
	for i in range(annotations[3]):
		plt.axvline(x=
			x[annotations[1]+annotations[2]+annotations[4]*i])
	plt.suptitle('Amplitude vs Time')
	plt.ylabel('Amplitude (dBm)')
	plt.xlabel('Time (s)')
	plt.xlim(time_values[0],time_values[1])
	plt.show()

def err_check(instrument):
	err_string = instrument.ask('system:error:all?').split(',')
	if err_string[0] != '0':
		status_text = (err_string[1])
		print(status_text)
	else:
		status_text = 0

	return status_text


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
	meas_bw = 20e6
	meas_time = 10e-6
	time_offset = 0
	trig_level = -20
	sym_rate = 6e6
	thresh = 3
	"""
	########################################################################
	########################################################################
	########################################################################
	"""
	#establish communication with RSA
	rsa, status_text = Tek_Instrument('GPIB8::1::INSTR')
	inst_setup(rsa, meas_freq, ref_level, 
		meas_bw, meas_time, trig_level)
	status_text = err_check(rsa)
	if status_text != 0:
		print status_text
	avt, avt_time, Fs, acq_time = get_avt(rsa)

	#demodulate and get symbol table
	symbol_table, annot = ask_decode(avt, sym_rate, Fs, thresh)

	#plot the data
	ask_plot(avt_time, avt, annot, acq_time)

	rsa.close()

if __name__ == '__main__':
	main()