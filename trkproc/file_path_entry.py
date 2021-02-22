import sys,os
import tkinter
import tkinter.ttk as ttk

class FilePathEntry(tkinter.Frame):
    def __init__(self, label, dialog_ftype, path_entry_width, master=None):
        super().__init__(master)
        self.master = master
        self.dialog_ftype = dialog_ftype

        file_path_label = tkinter.Label(self.master, text=label, anchor='e', width=12)
        file_path_label.grid(row=0, column=0)
        self.entry = ttk.Entry(self.master, width=path_entry_width)
        self.entry.grid(row=0, column=1, pady=3)
        file_path_btn = ttk.Button(self.master, text='参照', command=self.__file_dialog)
        file_path_btn.grid(row=0, column=2)

    def __file_dialog(self):
        entry_content = self.entry.get()
        if entry_content == '':
            init_dir = 'C:/'
        else:
            init_dir = os.path.dirname(entry_content)
        file_path = tkinter.filedialog.askopenfilename(parent=self.master, filetypes=self.dialog_ftype, initialdir=init_dir)

        if file_path != '':
            self.entry.delete(0, tkinter.END)
            self.entry.insert(tkinter.END, file_path)

    def get(self):
        return self.entry.get()

    def delete(self, start, end):
        self.entry.delete(start, end)

    def insert(self, start, value):
        self.entry.insert(start, value)

    def overwrite(self, new_path):
        new_path = new_path.replace('\\', '/')
        self.entry.delete(0, tkinter.END)
        self.entry.insert(tkinter.END, new_path)
