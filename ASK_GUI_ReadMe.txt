#readme.txt

ASK_Demodulator

Tested on windows 7 64-bit and Windows 8 64-bit
with SignalVu-PC 3.6.0239 and TekVISA 4.0.4 with RSA306
http://www.tek.com/model/rsa306-software-4
http://www.tek.com/oscilloscope/tds7054-software-2

Requirements:
Win7 64-bit or Win8 64-bit
SignalVu-PC v 3.6.0239/TekVISA4.0.4/RSA306

To use this demodulator, simply download and run it, no installation required.

Instructions:
1. Launch SignalVu-PC and ensure the RSA306 is connected
2. Launch ASK_GUI.exe
3. Select GPIB8::1::INSTR in the instrument connection window and click
	the Connect button
4. Either use SignalVu-PC to set up your acquisition or use the Instrument
	Setup fields/button provided in the GUI.
	Note: if you use SignalVu-PC to set up, make sure that the 
		Amplitude vs Time display is active
5. In the GUI click the Acquire button
6. In the GUI enter the desired values in the Symbol Rate and Demod Threshold
	fields and click Demodulate
7. The symbol table will show up on the right side of the GUI
8. You can export the symbol table as a text file if you like 
	(by default it is saved in the directory you launched ASK_GUI.exe from)

Notes: 
1. Demod Threshold is the number of dB down from the peak power in the
Amplitude vs Time display that the demodulator uses as it's high/low decision point.
2. You can use this demodulator with recalled .tiq files, just make sure the 
Amplitude vs Time window is active and contains valid data. Use steps 6-8.