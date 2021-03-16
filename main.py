#Imports and setup.
import tkinter as tk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import numpy as np
import os
from scipy.signal import find_peaks
from scipy.integrate import simps
#Serial connection class


def start_application():
    global read_real_time
    read_real_time = read_real_time = HL_FSCAV_REAL_TIME()
    read_real_time.master.mainloop()


class HL_FSCAV_REAL_TIME:
    def __init__(self):
        #Definition of app window.
        self.master = tk.Tk()
        self.master.title('FSCAV Real Time')
        self.master.geometry("700x600")
        self.master.configure(bg='gray')
        #Parameters
        self.path = ''
        self.list_of_files = []
        self.first_integration_point_array = []
        self.second_integration_point_array = []
        self.charge_array = []
        self.samples_array = []
        self.cvs_array = []
        self.time_array = []
        self.first_integration_point = 0
        self.second_integration_point = 0
        self.refresh_period = 1000
        self.frequency = 500000
        self.reading_bool = False
        self.auto_bool = False
        self.timer_process = None
        self.cv_graph_index = 0
        #Window components
        self.input_frame = tk.Frame(self.master,  bg='gray')
        self.input_frame.grid(row=0, padx=10, pady=10)
        self.control_frame = tk.Frame(self.master,  bg='gray')
        self.control_frame.grid(row=1, padx=10, pady=10)
        self.graph_frame = tk.Frame(self.master,  bg='gray')
        self.graph_frame.grid(row=1, padx=10, pady=10)

        tk.Label(self.input_frame, text="Inputs", font=(None, 15), anchor="e", bg='gray').grid(row=0, columnspan=2)
        self.path_input = self.get_input_object(self.input_frame, 'Path', 'gray', [1,0,1,1,0,0], [1,1,1,1,0,0], '\ ')
        self.first_integration_point_input = self.get_input_object(self.input_frame, 'Sample 1', 'gray', [2,0,1,1,0,0], [2,1,1,1,0,0], '60')
        self.second_integration_point_input = self.get_input_object(self.input_frame, 'Sample 2', 'gray', [3,0,1,1,0,0], [3,1,1,1,0,0], '350')
        self.frequency_input = self.get_input_object(self.input_frame, 'Freq. (Hz)', 'gray', [4,0,1,1,0,0], [4,1,1,1,0,0], '500000')
        self.checking_period_input = self.get_input_object(self.input_frame, 'Period (s)', 'gray', [5,0,1,1,0,0], [5,1,1,1,0,0], '10')

        tk.Label(self.control_frame, text="Control Panel", font=(None, 15), anchor="e", bg='gray').grid(row=0, column=0, columnspan=2)

        self.start_button = self.get_button_object(self.control_frame, self.start_reading_signals, 2, 10, 'Start', [5,0,1,2,0,0])
        self.stop_button = self.get_button_object(self.control_frame, self.stop_reading_signals, 2, 10, 'Stop', [5,2,1,2,0,0])
        self.save_charge_button = self.get_button_object(self.control_frame, self.save_charge, 2, 10, 'Save Charge', [6,0,1,2,0,0])
        self.reset_files_button = self.get_button_object(self.control_frame, self.reset_files, 2, 10, 'Reset Charge', [6,2,1,2,0,0])
        self.previous_button = self.get_button_object(self.control_frame, self.previous_button_pushed, 2, 5, '<', [7,0,1,1,10,10])
        self.file_label = tk.Label(self.control_frame, text=" ", bg="gray")
        self.file_label.grid(row=7,column=1)
        self.next_button = self.get_button_object(self.control_frame, self.next_button_pushed, 2, 5, '>', [7,2,1,1,10,10])
        self.auto_variable = tk.IntVar()
        self.auto_button = tk.Checkbutton(self.control_frame, text="Auto", variable = self.auto_variable)
        self.auto_button.grid(row=7, column=3, rowspan=1, columnspan=2)

        self.list_of_files_box = tk.Listbox(self.control_frame, bg="white")
        self.list_of_files_box.grid(row=8, column=0, columnspan=5, rowspan=3)

        self.charge_figure = self.generate_figure(self.master, [4,2], 100, [0,1,1,1,10,10], self.charge_array, 'tab:blue', 'Charge (nA·s)', 'Samples', 10)
        self.cvs_figure = self.generate_figure(self.master, [4,2], 100, [1,1,1,1,10,10], self.charge_array, 'tab:blue', 'Current (nA)', 'Time (s)', 10)

        #Menu
        self.menubar = tk.Menu(self.master)
        self.filemenu = tk.Menu(self.menubar, tearoff=0)
        self.filemenu.add_command(label="Reset Application", command=self.reset_application)
        self.filemenu.add_command(label="Exit", command=self.master.destroy)
        self.menubar.add_cascade(label="File", menu=self.filemenu)
        self.master.config(menu=self.menubar)

    def get_input_object(self, macro, label_name, color, label_position, input_position, default_value):
        tk.Label(macro, text=label_name, bg=color).grid(row=label_position[0], column=label_position[1],
        rowspan=label_position[2], columnspan=label_position[3], padx=label_position[4], pady=label_position[5])
        input = tk.Entry(macro)
        input.insert(0, default_value)
        input.grid(row=input_position[0], column=input_position[1], rowspan=input_position[2],
        columnspan=input_position[3], padx=input_position[4], pady=input_position[5])
        return input

    def get_button_object(self, macro, callback_fcn, height, width, text, position):
        button = tk.Button(master = macro, command = callback_fcn, height = height, width = width, text = text)
        button.grid(row=position[0], column=position[1], rowspan=position[2], columnspan=position[3], padx=position[4], pady=position[5])
        return button

    def generate_figure(self, macro, size, dpi, position, array, color, ylabel, xlabel, fontsize):
        figure = Figure(figsize=(size[0], size[1]), dpi=dpi)
        axes = figure.add_subplot(111)
        axes.set_ylabel(ylabel, fontsize=fontsize)
        axes.set_xlabel(xlabel, fontsize=fontsize)
        axes.tick_params(axis='both', labelsize=fontsize)
        line = axes.plot(array, marker='.', color=color)
        scatter = axes.plot([],[], marker='.', color='black')
        figure.tight_layout()
        canvas = FigureCanvasTkAgg(figure, master=macro)
        plot_widget = canvas.get_tk_widget()
        plot_widget.grid(row=position[0], column=position[1], rowspan=position[2], columnspan=position[3], padx=position[4], pady=position[5])
        return figure, axes, line, scatter, canvas, plot_widget



    def start_reading_signals(self):
        if(not self.reading_bool):
            self.reading_bool = True
            self.disable_inputs()
            self.read_signals()


    def read_signals(self):
        self.get_input_parameters()
        self.read_files()
        self.calculate_charge()
        self.update_charge_graph()
        self.write_file_list()
        if(self.reading_bool): self.timer_process = self.master.after(self.refresh_period, self.read_signals)


    def stop_reading_signals(self):
        if(self.reading_bool):
            self.reading_bool = False
            self.enable_inputs()
            self.master.after_cancel(self.timer_process)


    def save_charge(self):
        f = open('charge.txt', "a")
        [f.write(self.list_of_files[i]+'\t'+str(self.charge_array[i])+'\n') for i in self.samples_array]
        f.close()

    def update_charge_graph(self):
        self.charge_figure[2][0].set_data(self.samples_array, self.charge_array)
        self.charge_figure[1].relim()
        self.charge_figure[1].autoscale_view()
        self.charge_figure[4].draw()
        self.charge_figure[4].flush_events()


    def get_input_parameters(self):
        self.path = r""+self.path_input.get()
        self.auto_bool = self.auto_variable.get()
        self.first_integration_point = int(self.first_integration_point_input.get())
        self.second_integration_point = int(self.second_integration_point_input.get())
        self.frequency = float(self.frequency_input.get())
        self.refresh_period = 1000*int(self.checking_period_input.get())


    def read_files(self):
        all_files = list(filter(lambda x: x[-4:] == '.txt', os.listdir(self.path)))
        diff_files = np.setdiff1d(all_files, self.list_of_files)
        for file in diff_files:
            matrix = open(self.path+"/"+file).read()
            matrix = np.array([item.split() for item in matrix.split('\n')[:-1]])
            matrix = matrix.astype('float64')
            self.cvs_array.append([x[2] for x in matrix])
        self.list_of_files = np.append(self.list_of_files, diff_files)



    def calculate_charge(self):
        if(self.auto_bool): self.get_auto_intervals()
        else:  self.get_manual_intervals()
        self.time_array = np.linspace(0, len(self.cvs_array[0])*(1/self.frequency), len(self.cvs_array[0]))
        self.charge_calculation()


    def get_manual_intervals(self):
        self.first_integration_point_array = [self.first_integration_point]*len(self.cvs_array)
        self.second_integration_point_array = [self.second_integration_point]*len(self.cvs_array)


    def get_auto_intervals(self):
        oxidation_length = int(len(self.cvs_array[0])/2)
        self.first_integration_point_array = []
        self.second_integration_point_array = []
        for x in self.cvs_array:
            tmp = find_peaks(np.negative(x[0:oxidation_length]))[0]
            try:
                if(tmp[0]<100): self.first_integration_point_array.append(tmp[0])
                else: self.first_integration_point_array.append(self.first_integration_point)
            except:
                self.first_integration_point_array.append(self.first_integration_point)
            try:
                self.second_integration_point_array.append(tmp[1])
            except:
                self.second_integration_point_array.append(self.second_integration_point)


    def charge_calculation(self):
        self.samples_array = range(0, len(self.first_integration_point_array))
        coeffs = [np.polyfit((self.time_array[self.first_integration_point_array[i]],self.time_array[self.second_integration_point_array[i]]),
        (self.cvs_array[i][self.first_integration_point_array[i]], self.cvs_array[i][self.second_integration_point_array[i]]), 1)
         for i in self.samples_array]
        lines = [(coeffs[i][0] * self.time_array) + coeffs[i][1] for i in self.samples_array]
        Q = [simps(self.cvs_array[i][self.first_integration_point_array[i]:self.second_integration_point_array[i]],
        self.time_array[self.first_integration_point_array[i]:self.second_integration_point_array[i]]) for i in self.samples_array]
        Qline = [simps(lines[i][self.first_integration_point_array[i]:self.second_integration_point_array[i]],
        self.time_array[self.first_integration_point_array[i]:self.second_integration_point_array[i]]) for i in self.samples_array]
        self.charge_array = np.subtract(Q, Qline)

    def reset_files(self):
        self.cvs_array = []
        self.time_array = []
        self.charge_array = []
        self.list_of_files = []
        self.samples_array = []
        self.first_integration_point_array = []
        self.second_integration_point_array = []
        self.read_signals()

    def disable_inputs(self):
        self.path_input.configure(state="disabled")
        self.first_integration_point_input.configure(state="disabled")
        self.second_integration_point_input.configure(state="disabled")
        self.frequency_input .configure(state="disabled")
        self.checking_period_input.configure(state="disabled")
        self.start_button.configure(bg = "#7bf76d")
        self.stop_button.configure(bg = "SystemButtonFace")

    def enable_inputs(self):
        self.path_input.configure(state="normal")
        self.first_integration_point_input.configure(state="normal")
        self.second_integration_point_input.configure(state="normal")
        self.frequency_input .configure(state="normal")
        self.checking_period_input.configure(state="normal")
        self.start_button.configure(bg = "SystemButtonFace")
        self.stop_button.configure(bg = "#ff4a4a")
    def write_file_list(self):
        self.list_of_files_box.delete(0, 'end')
        for entry in self.list_of_files:
            self.list_of_files_box.insert('end', entry)

    def previous_button_pushed(self):
        if (not self.samples_array or self.cv_graph_index == self.samples_array[0]): return
        elif(self.cv_graph_index>self.samples_array[-1]): self.cv_graph_index = self.samples_array[-1]
        else: self.cv_graph_index = self.cv_graph_index-1
        self.graph_cv()
        self.file_label.config(text=self.cv_graph_index)

    def next_button_pushed(self):
        if (not self.samples_array or self.cv_graph_index == self.samples_array[-1]): return
        elif(self.cv_graph_index>self.samples_array[-1]): self.cv_graph_index = self.samples_array[-1]
        else: self.cv_graph_index = self.cv_graph_index+1
        self.graph_cv()
        self.file_label.config(text=self.cv_graph_index)



    def graph_cv(self):
        self.cvs_figure[2][0].set_data(self.time_array, self.cvs_array[self.cv_graph_index])
        self.cvs_figure[3][0].set_data([self.time_array[self.first_integration_point_array[self.cv_graph_index]], self.time_array[self.second_integration_point_array[self.cv_graph_index]]],
        [self.cvs_array[self.cv_graph_index][self.first_integration_point_array[self.cv_graph_index]], self.cvs_array[self.cv_graph_index][self.second_integration_point_array[self.cv_graph_index]]])
        self.cvs_figure[1].relim()
        self.cvs_figure[1].autoscale_view()
        self.cvs_figure[4].draw()
        self.cvs_figure[4].flush_events()

    def reset_application(self):
        self.master.destroy()
        start_application()


start_application()
