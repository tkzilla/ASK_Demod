"""
v 0.8
ASK_GUI.py
This is the graphical user interface for ASK_demod_guts.py
Tested on a Windows 7 64-bit and Windows 8 64-bit computer
It requires the installation of both SignalVu-PC and TekVISA 4.0.4
and will not run at all without TekVISA installed.
TODO:
Fix symbol table output ellipsis
ADD MANCHESTER FUNCTIONALITY, YOU GOT THE GUI FRAMEWORK DONE!
"""

from Tkinter import *
from ASK_demod_guts import *

class GUI(Frame):
	"""GUI with 8 text fields, 3 buttons, and a table"""

	def __init__(self, master=0):
		Frame.__init__(self,master)
		self.grid()
		self.createWidgets()

	def createWidgets(self):
		#Creating widgets in the GUI
		self.button_width = 18
		self.status_text = 'Ready'
		active_row = 0

		#Row 0: Instrument listbox label, symbol table label
		self.inst_list_label = Label(self, text='Instrument List')
		self.inst_list_label.grid(column=0, row=active_row)
		self.inst_connect_button = Button(self, text='Connect', 
			command=self.inst_connect, width=self.button_width)
		self.inst_connect_button.grid(column=1, row=active_row)
		self.symtablabel = Label(self, text='Symbol Table')
		self.symtablabel.grid(column=2, row=active_row)
		active_row += 1
		
		#Row 1: Instrument listbox, symbol table
		self.inst_list_contents = StringVar()
		self.inst_list = Listbox(self, listvariable=self.inst_list_contents,
			width=48)
		self.inst_list_contents.set(' '.join(VISA_search()))
		self.inst_list.grid(column=0, row=active_row, columnspan=2)
		self.st_scrollbar = Scrollbar(self, orient=VERTICAL)
		self.symtable = Canvas(self, width=300, height=400, 
			borderwidth=4, relief=SUNKEN, 
			scrollregion=(0,0,300,1000))
		self.symbol_table_text = self.symtable.create_text(10, 10, anchor=NW,
			text='Symbols will appear here after\nsuccessful demodulation.')
		self.symtable.config(yscrollcommand=self.st_scrollbar.set)
		self.st_scrollbar.config(command=self.symtable.yview)
		self.symtable.grid(column=2, row=active_row, rowspan=10)
		self.st_scrollbar.grid(column=3, row=active_row, sticky=N+S,
			rowspan=10)
		active_row += 1

		#Row 2: Settings label and Settings button
		self.settingslabel = Label(self, text='Instrument/Demod Settings')
		self.settingslabel.grid(column=0, row=active_row)
		self.inst_setup_button = Button(self, text='Instrument Setup',
			command = self.gui_instrument_setup, width=self.button_width)
		self.inst_setup_button.grid(column=1, row=active_row)
		active_row += 1

		#Row 3: Center frequency label and entry
		self.cflabel = Label(self, text = 'Center Frequency (Hz)')
		self.cflabel.grid(column=0, row=active_row, sticky=E)
		self.cf_e_text = StringVar()
		self.cf_e = Entry(self, textvariable=self.cf_e_text)
		self.cf_e.grid(column=1, row=active_row)
		self.cf_e_text.set('1e9')
		active_row += 1

		#Row 4: Span label and entry
		self.spanlabel = Label(self, text = 'Span (Hz)')
		self.spanlabel.grid(column=0, row=active_row, sticky=E)
		self.span_e_text = StringVar()
		self.span_e = Entry(self, textvariable=self.span_e_text)
		self.span_e.grid(column=1, row=active_row)
		self.span_e_text.set('20e6')
		active_row += 1

		#Row 5: Ref level label and entry
		self.reflevellabel = Label(self, text = 'Reference Level (dBm)')
		self.reflevellabel.grid(column=0, row=active_row, sticky=E)
		self.reflevel_e_text = StringVar()
		self.reflevel_e = Entry(self, textvariable=self.reflevel_e_text)
		self.reflevel_e.grid(column=1, row=active_row)
		self.reflevel_e_text.set('0')
		active_row += 1

		#Row 6: Meas length label and entry
		self.meas_lengthlabel = Label(self, text = 'Measurement Length (sec)')
		self.meas_lengthlabel.grid(column=0,row=active_row, sticky=E)
		self.meas_length_e_text = StringVar()
		self.meas_length_e = Entry(self, textvariable=self.meas_length_e_text)
		self.meas_length_e.grid(column=1, row=active_row)
		self.meas_length_e_text.set('200e-6')
		active_row += 1

		#Row 7: Trigger Level label and entry
		self.trig_lvllabel = Label(self, text = 'Trigger Level (dBm)')
		self.trig_lvllabel.grid(column=0, row=active_row, sticky=E)
		self.trig_lvl_e_text = StringVar()
		self.trig_lvl_e = Entry(self, textvariable=self.trig_lvl_e_text)
		self.trig_lvl_e.grid(column=1, row=active_row)
		self.trig_lvl_e_text.set('-0')
		active_row += 1

		#Row 8: Acquire and Replay buttons
		self.acquire_button = Button(self, text='Acquire', 
			command=self.gui_acquire, width=self.button_width)
		self.acquire_button.grid(column=0, row=active_row)
		self.replay_button = Button(self, text='Replay', 
			command=self.gui_replay, width=self.button_width)
		self.replay_button.grid(column=1, row=active_row)
		active_row += 1

		#Row 9: Symbol rate label and entry
		self.symratelabel = Label(self, text = 'Symbole Rate (Sym/sec)')
		self.symratelabel.grid(column=0, row=active_row, sticky=E)
		self.symrate_e_text = StringVar()
		self.symrate_e = Entry(self, textvariable=self.symrate_e_text)
		self.symrate_e.grid(column=1, row=active_row)
		self.symrate_e_text.set('250e3')
		active_row += 1

		#Row 10: Demodulation Threshold label and entry
		self.threshlabel = Label(self, text = 'Demod Thresh (dB from peak)')
		self.threshlabel.grid(column=0, row=active_row, sticky=E)
		self.thresh_e_text = StringVar()
		self.thresh_e = Entry(self, textvariable=self.thresh_e_text)
		self.thresh_e.grid(column=1, row=active_row)
		self.thresh_e_text.set('3')
		active_row += 1

		#Row 11: Status message, Manchester radio buttons, demodulate button
		self.manch_var = IntVar()
		self.manch_checkbox = Checkbutton(self, text='Manchester', 
			variable=self.manch_var, onvalue=1, offvalue=0)
		self.manch_checkbox.grid(column=0, row=active_row)
		self.demod_button = Button(self, text='Demodulate',
			command = self.gui_full_demod, width=self.button_width)
		self.demod_button.grid(column=1, row=active_row)
		self.status_label = Label(self, text=self.status_text)
		self.status_label.grid(column=2, row=active_row, rowspan=2)
		active_row += 1

		#Row 12: Export and quit buttons
		self.export_button = Button(self, text='Export Symbol Table',
			command = self.export, width=self.button_width)
		self.export_button.grid(column=0, row=active_row)
		self.quitButton = Button(self, text='Quit',
			command = self.quit, width=self.button_width)
		self.quitButton.grid(column=1, row=active_row)
		active_row += 1

		#Row 13: Graph Button and Eye Diagram Button
		self.graph_button = Button(self, text='Demod Plot', 
			command = self.gui_ask_plot, width=self.button_width)
		self.graph_button.grid(column=0, row=active_row)
		# self.eye_diagram_button = Button(self, text='Eye Diagram',
			# command = self.gui_eye_diagram, width=self.button_width)
		active_row += 1


	def inst_connect(self):
		self.status_text = 'Attemtping to connect...'
		self.status_update()
		descriptor = self.inst_list.get(ACTIVE)
		self.inst, self.status_text = Tek_Instrument(descriptor)
		self.status_update()

	def gui_instrument_setup(self):
		try:
			cf = float(self.cf_e.get())
			span = float(self.span_e.get())
			reflevel = float(self.reflevel_e.get())
			meas_length = float(self.meas_length_e.get())
			trig_lvl = float(self.trig_lvl_e.get())
			self.status_text = inst_setup(self.inst, 
				cf, reflevel, span, meas_length, trig_lvl)
			if self.status_text != 0:
				self.status_update()
			else:
				self.status_text = 'Acquisition settings configured.'
		except ValueError:
			self.status_text = 'Enter a valid number in each field.'
		except AttributeError:
			self.status_text = 'Please connect to an instrument.'
		except visa.VisaIOError:
			self.status_text = 'Timeout expired before operation completed.'
		self.status_update()

	def gui_acquire(self):
		try:
			acquire(self.inst)
			self.avt, self.Fs, self.plot_time, self.status_text = get_avt(self.inst)
			if self.status_text != 0:
				self.status_update()
			else:
				self.status_text = 'Data acquired, ready to demodulate.'
		except ValueError:
			self.status_text = 'Please enter valid numbers in all fields.'
		except AttributeError:
			self.status_text = 'Please connect to an instrument.'
		except visa.VisaIOError:
			self.status_text = 'Timeout expired before operation completed.'
		self.status_update()

	def gui_replay(self):
		try:
			self.avt, self.Fs, self.plot_time, self.status_text = get_avt(self.inst)
			if self.status_text != 0:
					self.status_update()
			else:
				self.status_text = 'Data updated, ready to demodulate.'
		except ValueError:
			self.status_text = 'Please enter valid numbers in all fields.'
		except AttributeError:
			self.status_text = 'Please connect to an instrument.'
		except visa.VisaIOError:
			self.status_text = 'Timeout expired before operation completed.'
		self.status_update()

	def gui_full_demod(self):
		try:
			sym_rate = float(self.symrate_e.get())
			if self.manch_var.get() == 1:
				sym_rate = sym_rate*2
			if (sym_rate > 200e6) or (sym_rate < 0):
				raise Warning
			thresh = float(self.thresh_e.get())
			symbol_table, self.annot = ask_decode(self.avt, sym_rate, self.Fs, thresh)
			self.status_text ='Demodulation complete.'
			if self.manch_var.get() == 1:
				symbol_table = manchester_ask_decode(symbol_table)
				self.status_text = 'Manchester demod complete.'

			self.st_contents = np.array_str(symbol_table, max_line_width=64)
			self.symtable.itemconfig(self.symbol_table_text, 
				text=self.st_contents)
		except ValueError:
			self.status_text = 'Please enter valid numbers in all fields.'
		except AttributeError:
			self.status_text = 'Please acquire data before demodulating.'
		except Warning:
			self.status_text = 'Symbol rate out of range.'
		except IndexError:
			self.status_text = 'Pattern alignment or data rate error,\nplease reacquire data or adjust data rate.'
		self.status_update()

	def export(self):
		filename = 'ASK_symbol_table.txt'
		output = open(filename, 'w')
		output.write(self.st_contents)
		output.close
		self.status_text = 'Symbol table exported to {0}'.format(filename)
		self.status_update()	

	def gui_ask_plot(self):
		axis = AskAxis()
		try:
			axis.y = self.avt
			axis.annot = self.annot
			axis.time = self.plot_time
			axis.calcx()
			ask_plot(axis)
			self.status_text = 'Demodulation decision points/thresholds plotted.'
		except AttributeError:
			self.status_text = 'Please acquire and demodulate before plotting.'
		self.status_update()

	#def gui_eye_diagram(self):
		

	def status_update(self):
		self.status_label.configure(text=self.status_text)


app = GUI()

app.master.title('ASK Demodulator v 0.7')

app.mainloop()