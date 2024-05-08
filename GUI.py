import automator
import tkinter_tools as tkTools


class Root(tkTools.MainWindow):
    def __init__(self, title="Screen capture tools", window_size=(360, 360), min_size=(360, 360), max_size=(720, 760)):
        super().__init__(title=title,
                         window_size=window_size,
                         min_size=min_size,
                         max_size=max_size
                         )
        self.frame = None
        self.grid()
        self.widgets()
        self.HomeFrame = HomeFrame(self)
        self.HomeFrame.grid()
        self.mainloop()

    def grid(self):
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

    def widgets(self):
        self.frame = tkTools.Frame(self)
        self.frame.grid_configure(row=0, column=0, sticky="NSEW")
        self.frame.rowconfigure(0, weight=1)
        self.frame.columnconfigure(0, weight=1)


# home frame
class HomeFrame(tkTools.Frame):
    def __init__(self, root):
        super().__init__(root.frame)
        self.root = root
        self.log_list = automator.get_automation_logs()
        self.grid_configure(row=0, column=0, sticky="NSEW")
        self.grid_setup()
        self.widgets()

    def grid_setup(self):
        self.grid_rowconfigure(0, weight=1, minsize=100)
        self.grid_rowconfigure(1, minsize=36)
        self.grid_rowconfigure(2, weight=1, minsize=40)
        self.grid_rowconfigure(3, weight=1)
        self.grid_rowconfigure(4, weight=1, minsize=40)
        self.grid_columnconfigure(0, weight=1, minsize=40)
        self.grid_columnconfigure(1, weight=1, minsize=100)
        self.grid_columnconfigure(2, weight=1, minsize=100)
        self.grid_columnconfigure(3, weight=1, minsize=40)
        self.grid_remove()

    def widgets(self):
        def set_log_dropdown_value():
            self.log_list = automator.get_automation_logs()
            log_dropdown.configure(values=self.log_list)
            if not self.log_list:
                log_dropdown.delete(first=0, last="end")
                log_dropdown.configure(foreground="gray")
                log_dropdown.insert(0, "No logs found")
                no_logs_label.grid_configure(row=2, column=1, columnspan=2, sticky="NW")
            else:
                no_logs_label.grid_remove()
                log_dropdown.configure(foreground="black")
                log_dropdown.current(0)

        def run_automator():
            if not self.log_list:
                log_output_textbox.output("There are no logs to automate.")
                log_output_textbox.see("end")
                return
            record_button.configure(state="disabled")
            log_output_textbox.output('Starting "' + log_dropdown.get() + '"...'),
            log_output_textbox.see("end"),
            automator.run_automator(log_dropdown.get() + ".log"),
            log_output_textbox.output('Finished running "' + log_dropdown.get() + '"\n')
            record_button.configure(state="normal")

        def run_recorder():
            name = "test"
            automate_button.configure(state="disabled")
            log_output_textbox.output("Recording started.")
            log_output_textbox.see("end"),
            automator.start_recording(name),
            log_output_textbox.output("Recording stopped.")
            log_output_textbox.see("end"),
            log_output_textbox.output('Recording saved as "' + name + '"\n')
            log_output_textbox.see("end"),
            set_log_dropdown_value()
            automate_button.configure(state="normal")

        def open_log_deletion_window():
            if not self.log_list:
                log_output_textbox.output("There are no logs to delete.")
                log_output_textbox.see("end")
                return
            log_deletion_window = tkTools.SubWindow(self, title="Log deletion", window_size=(360, 180), min_size=(360, 180))
            log_deletion_window.grid_rowconfigure(0, weight=1)
            log_deletion_window.grid_rowconfigure(1, minsize=72)
            log_deletion_window.grid_rowconfigure(2, weight=4)
            log_deletion_window.grid_columnconfigure(0, weight=1)
            log_deletion_window.grid_columnconfigure(1, minsize=20)
            log_deletion_window.grid_columnconfigure(2, weight=1)
            log_deletion_text = "Are you sure you want to delete:"
            log_deletion_label = tkTools.Label(log_deletion_window, display_text=log_deletion_text)
            log_deletion_label.grid_configure(row=0, column=0, columnspan=3, sticky="S")
            log_label = tkTools.Label(log_deletion_window, display_text=log_dropdown.get(), font="Consolas", backdrop="ridge")
            log_label.configure(padding=4)
            log_label.grid_configure(row=1, column=0, columnspan=3)
            log_deletion_confirm_button = tkTools.Button(log_deletion_window, display_text="Delete",
                                                         function_when_clicked=lambda: [
                                                             delete_log(log_dropdown.get()),
                                                             log_deletion_window.destroy(),
                                                             log_deletion_window.update()
                                                         ])
            log_deletion_confirm_button.grid_configure(row=2, column=0, sticky="NE")
            log_deletion_cancel_button = tkTools.Button(log_deletion_window, display_text="Cancel",
                                                        function_when_clicked=lambda: [
                                                            log_deletion_window.destroy(),
                                                            log_deletion_window.update()
                                                        ])
            log_deletion_cancel_button.grid_configure(row=2, column=2, sticky="NW")

        def delete_log(log):
            automator.delete_log(log)
            log_output_textbox.output("Deleted: " + log)
            set_log_dropdown_value()

        # first initialize the log-fetching widgets so that they can be referenced with other buttons
        welcome_msg = ("Hi!\n"
                       "This tool can be used to automate mouse clicks and key presses.\n"
                       "To do so, start by clicking the button on the top right. Once clicked, the program will begin "
                       "to record your mouse clicks and key presses. You can click the ESC key to stop the recording.\n"
                       "To replay a recording, click the button on the top left.\n\n")
        log_dropdown = tkTools.Combobox(self, values=self.log_list, font=("Consolas", 10))
        no_logs_label = tkTools.Label(self, display_text="No logs found", text_color="red", text_alignment="left")
        set_log_dropdown_value()
        log_dropdown.grid_configure(row=1, column=1, columnspan=2, sticky="NEW")
        log_deletion_button = tkTools.Button(self, display_text="delete", function_when_clicked=open_log_deletion_window)
        log_deletion_button.grid_configure(row=2, column=2, sticky="E")
        log_output_textbox = tkTools.Text(self, wrap_on="word", state="disabled", text=welcome_msg)
        log_output_textbox.grid_configure(row=3, column=1, columnspan=2, sticky="NSEW")
        log_dropdown.bind("<FocusIn>", lambda e: set_log_dropdown_value())

        # more widgets
        automate_button = tkTools.Button(self, display_text="Play", function_when_clicked=run_automator)
        automate_button.grid_configure(row=0, column=1, sticky="W")
        record_button = tkTools.Button(self, display_text="Rec.", function_when_clicked=run_recorder)
        record_button.grid_configure(row=0, column=2, sticky="E")
        settings_button = tkTools.Button(self, display_text="Settings")
        settings_button.grid_configure(row=4, column=2, sticky="SE")


Root()
