#!/usr/bin/env python3

import tkinter as tk
from tkinter import ttk
import os


class Tab(tk.Frame):
    def __init__(self, notebook, update_ms=500, *args, **kwargs):
        tk.Frame.__init__(self, notebook, *args, **kwargs)
        # global tk app shortcut
        self.notebook = notebook
        self.app = notebook.master
        # frame auto-refresh delay (in ms)
        self.update_ms = update_ms
        # setup auto-refresh of notebook tab (on-visibility and every update_ms)
        self.bind('<Visibility>', lambda evt: self.tab_update())
        self._tab_update()

    def _tab_update(self):
        if self.winfo_ismapped():
            self.tab_update()
        self.master.after(self.update_ms, self._tab_update)

    def tab_update(self):
        pass


class TkApp(tk.Tk):
    def __init__(self, *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs)
        # configure main window
        self.wm_title('Analyse modbus RTU')
        # self.attributes('-fullscreen', True)
        # self.geometry('800x400')
        # build a notebook with tabs
        self.note = ttk.Notebook(self)
        self.tab1 = Tab1(self.note)
        self.tab2 = Tab2(self.note)
        self.note.add(self.tab1, text='Capture')
        self.note.add(self.tab2, text='Requêtes')
        self.note.pack(fill=tk.BOTH, expand=tk.YES)

    def do_every(self, do_cmd, every_ms=1000):
        do_cmd()
        self.after(every_ms, lambda: self.do_every(do_cmd, every_ms=every_ms))


class Tab1(Tab):
    def __init__(self, notebook, update_ms=500, *args, **kwargs):
        Tab.__init__(self, notebook, update_ms, *args, **kwargs)
        # some vars
        self.d_serial_dev = {}
        self.l_lst1_serial = []
        self.device = tk.StringVar()
        self.device.set('/dev/ttyUSB0')
        self.device.trace('w', self.update_command)
        self.baudrate = tk.StringVar()
        self.baudrate.set('9600')
        self.baudrate.trace('w', self.update_command)
        self.parity = tk.StringVar()
        self.parity.set('N')
        self.parity.trace('w', self.update_command)
        self.stop = tk.StringVar()
        self.stop.set('1')
        self.stop.trace('w', self.update_command)
        self.cmd_cap = ''
        # widget
        self.frm = tk.Frame(self)
        self.frm.pack(fill=tk.BOTH, expand=tk.YES)
        # device
        self.lbfrm1 = tk.LabelFrame(self.frm, text='Port')
        self.lbfrm1.grid(row=0, rowspan=2, column=0, sticky=tk.NSEW, padx=5, pady=5)
        self.lst1 = tk.Listbox(self.lbfrm1)
        self.lst1.pack(fill=tk.BOTH, expand=tk.YES)
        self.lst1.bind('<<ListboxSelect>>', self.on_dev_select)
        # baudrate
        self.lbfrm2 = tk.LabelFrame(self.frm, text='Baudrate')
        self.lbfrm2.grid(row=0, rowspan=2, column=1, sticky=tk.NSEW, padx=5, pady=5)
        tk.Radiobutton(self.lbfrm2, text='1200', variable=self.baudrate, value='1200').pack(anchor=tk.W)
        tk.Radiobutton(self.lbfrm2, text='2400', variable=self.baudrate, value='2400').pack(anchor=tk.W)
        tk.Radiobutton(self.lbfrm2, text='4800', variable=self.baudrate, value='4800').pack(anchor=tk.W)
        tk.Radiobutton(self.lbfrm2, text='9600', variable=self.baudrate, value='9600').pack(anchor=tk.W)
        tk.Radiobutton(self.lbfrm2, text='19200', variable=self.baudrate, value='19200').pack(anchor=tk.W)
        tk.Radiobutton(self.lbfrm2, text='38400', variable=self.baudrate, value='38400').pack(anchor=tk.W)
        tk.Radiobutton(self.lbfrm2, text='57600', variable=self.baudrate, value='57600').pack(anchor=tk.W)
        tk.Radiobutton(self.lbfrm2, text='115200', variable=self.baudrate, value='115200').pack(anchor=tk.W)
        # parity
        self.lbfrm3 = tk.LabelFrame(self.frm, text='Parité')
        self.lbfrm3.grid(row=0, column=2, sticky=tk.NSEW, padx=5, pady=5)
        tk.Radiobutton(self.lbfrm3, text='Aucune', variable=self.parity, value='N').pack(anchor=tk.W)
        tk.Radiobutton(self.lbfrm3, text='Paire', variable=self.parity, value='E').pack(anchor=tk.W)
        tk.Radiobutton(self.lbfrm3, text='Impaire', variable=self.parity, value='O').pack(anchor=tk.W)
        tk.Radiobutton(self.lbfrm3, text='Espace', variable=self.parity, value='S').pack(anchor=tk.W)
        tk.Radiobutton(self.lbfrm3, text='Marque', variable=self.parity, value='M').pack(anchor=tk.W)
        # stop bit
        self.lbfrm4 = tk.LabelFrame(self.frm, text='Bit de Stop')
        self.lbfrm4.grid(row=1, column=2, sticky=tk.NSEW, padx=5, pady=5)
        tk.Radiobutton(self.lbfrm4, text='1', variable=self.stop, value='1').pack(anchor=tk.W)
        tk.Radiobutton(self.lbfrm4, text='1.5', variable=self.stop, value='1.5').pack(anchor=tk.W)
        tk.Radiobutton(self.lbfrm4, text='2', variable=self.stop, value='2').pack(anchor=tk.W)
        # command area
        self.lbl4 = tk.Label(self.frm, text='', bg='pale green')
        self.lbl4.grid(row=3, columnspan=3, sticky=tk.NSEW)
        # start command
        self.but1 = tk.Button(self.frm, text='Lancer la capture', state='disabled',
                              command=lambda: os.system('xterm -e %s &' % self.cmd_cap))
        self.but1.grid(row=4, columnspan=3, sticky=tk.NSEW)

    def tab_update(self):
        # update serials port
        d_dev = {}
        if os.path.exists('/dev/serial/by-id'):
            for link in os.listdir('/dev/serial/by-id'):
                dev_rpath = os.readlink(os.path.join('/dev/serial/by-id', link))
                device = os.path.normpath(os.path.join('/dev/serial/by-id', dev_rpath))
                d_dev[device] = link
        # add or remove serial ?
        if self.d_serial_dev != d_dev:
            self.d_serial_dev = d_dev
            # refresh widget
            self.lst1.delete(0, tk.END)
            self.l_lst1_serial = []
            for d in self.d_serial_dev:
                # lst1 widget info cache
                self.l_lst1_serial.append({'dev': d, 'type': 'n/a'})
                i = len(self.l_lst1_serial) - 1
                # device type (RS232/485...) from link name
                if 'RS232' in self.d_serial_dev[d]:
                    self.l_lst1_serial[i]['type'] = 'RS232'
                elif 'RS485' in self.d_serial_dev[d]:
                    self.l_lst1_serial[i]['type'] = 'RS485'
                elif 'RS422' in self.d_serial_dev[d]:
                    self.l_lst1_serial[i]['type'] = 'RS422'
                # add "device (device type)" to widget
                self.lst1.insert(i, '%s (%s)' % (d, self.l_lst1_serial[i]['type']))

    def on_dev_select(self, event):
        index = self.lst1.curselection()[0]
        try:
            self.device.set(self.l_lst1_serial[index]['dev'])
        except IndexError:
            pass

    def update_command(self, *args):
        # update cmd cap
        self.cmd_cap = 'scan_modbus_serial -d %s' % self.device.get()
        # add params if not as default
        if self.baudrate.get() != '9600':
            self.cmd_cap += ' -b %s' % self.baudrate.get()
        if self.parity.get() != 'N':
            self.cmd_cap += ' -p %s' % self.parity.get()
        if self.stop.get() != '1':
            self.cmd_cap += ' -s %s' % self.stop.get()

        self.lbl4.configure(text=self.cmd_cap)
        # valid button if cmd cap ok
        if self.cmd_cap:
            self.but1.configure(state='normal')
        else:
            self.but1.configure(state='disabled')


class Tab2(Tab):
    def __init__(self, notebook, update_ms=500, *args, **kwargs):
        Tab.__init__(self, notebook, update_ms, *args, **kwargs)


if __name__ == '__main__':
    # main Tk App
    app = TkApp()
    app.mainloop()
