import logging
import os.path
import pyautogui
import time
from collections import deque
from pynput.keyboard import Key, HotKey
from pynput.keyboard import Listener as Key_Listener
from pynput.keyboard import Controller as Key_Controller
from pynput.mouse import Button
from pynput.mouse import Listener as Mouse_Listener
from pynput.mouse import Controller as Mouse_Controller

log_folder = "automation_logs"
log_dir = os.path.join(os.path.dirname(__file__), log_folder)
if not os.path.exists(log_dir):
    os.makedirs(log_dir)


def start_recording(save_name, stop_recording_key=Key.esc, compress_held_keys=True, raw_file=False, save_raw_file=False, replace_existing=False):

    class util:
        def __init__(self):
            """records time in seconds"""
            self.start_time = time.perf_counter()
            self.prev_time = self.start_time
            self.elapsed_time = self.start_time
            self.timer = self.start_time

        def process_current_time_stamps(self):
            current_time = time.perf_counter()
            self.timer = current_time - self.start_time
            self.elapsed_time = current_time - self.prev_time
            self.prev_time = current_time

        def get_timer(self):
            return self.timer

        def get_elapsed_time(self):
            return self.elapsed_time

        def restart_timer(self):
            self.start_time = time.perf_counter()
            self.prev_time = self.start_time
            self.elapsed_time = self.start_time
            self.timer = self.start_time

    def log_key(key):
        # test for the stop_recording key
        try:
            if key.char == stop_recording_key:
                m_listener.stop()
                k_listener.stop()
                return
        except AttributeError:
            if key == stop_recording_key:
                m_listener.stop()
                k_listener.stop()
                return
        # log key
        timer.process_current_time_stamps()
        try:
            logger.info("+{0} {1} {2}".format(key.char, timer.get_timer(), timer.get_elapsed_time()))
        except AttributeError:
            logger.info("+{0} {1} {2}".format(key, timer.get_timer(), timer.get_elapsed_time()))

    def log_unkey(key):
        timer.process_current_time_stamps()
        try:
            logger.info("-{0} {1} {2}".format(key.char, timer.get_timer(), timer.get_elapsed_time()))
        except AttributeError:
            logger.info("-{0} {1} {2}".format(key, timer.get_timer(), timer.get_elapsed_time()))

    def log_click(x, y, button, pressed):
        timer.process_current_time_stamps()
        if pressed:
            logger.info("1{0} {1},{2} {3} {4}".format(button, x, y, timer.get_timer(), timer.get_elapsed_time()))
        else:
            logger.info(("0{0} {1},{2} {3} {4}".format(button, x, y, timer.get_timer(), timer.get_elapsed_time())))

    def log_scroll(x, y, dx, dy):
        timer.process_current_time_stamps()
        if dy < 0:
            logger.info("_ {0},{1} {2} {3}".format(x, y, timer.get_timer(), timer.get_elapsed_time()))
        else:
            logger.info("^ {0},{1} {2} {3}".format(x, y, timer.get_timer(), timer.get_elapsed_time()))
        if dx < 0:
            logger.info("< {0},{1} {2} {3}".format(x, y, timer.get_timer(), timer.get_elapsed_time()))
        else:
            logger.info("> {0},{1} {2} {3}".format(x, y, timer.get_timer(), timer.get_elapsed_time()))

    # prepare file name
    save_name = os.path.splitext(save_name)[0]
    file_name = os.path.join(log_folder, save_name + ".log")
    if not replace_existing:
        file_name = account_for_duplicate_filenames(file_name)
    if is_duplicate(file_name):
        file_name = file_name[:-8] + "_RAW" + file_name[-8:]
    else:
        file_name = file_name[:-4] + "_RAW" + file_name[-4:]

    # start recording
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)

    recording_format = logging.Formatter("%(message)s")
    handler = logging.FileHandler(filename=file_name)
    handler.setFormatter(recording_format)
    logger.addHandler(handler)

    with (Key_Listener(on_press=log_key, on_release=log_unkey) as k_listener,
          Mouse_Listener(on_click=log_click, on_scroll=log_scroll) as m_listener):
        timer = util()
        k_listener.join()
        m_listener.join()
    logger.removeHandler(handler)
    handler.close()

    if not raw_file:
        log_post_processing(file_name, save_raw_file, compress_held_keys)


def log_post_processing(log, save_raw_file, compress_held_keys=True):
    # get log as strings
    with open(log, "r") as f:
        lines_orig = f.readlines()

    # strip "_RAW" from file name
    if is_duplicate(log):
        file_name = log[:-12] + log[-8:]
    else:
        file_name = log[:-8] + ".log"

    # overwrite RAW file if True
    if not save_raw_file:
        os.rename(log, file_name)

    # start post-processing
    with open(file_name, "w") as f:
        held_keys = []
        prev_time = 0.0
        for line in lines_orig:
            data = list(line.split(" "))
            if compress_held_keys:
                # account for held keys
                if data[0][0] == "+":
                    key = data[0][1:]
                    if key in held_keys:
                        # if key is already pressed, do not write to logger
                        continue
                    held_keys.append(key)
                if data[0][0] == "-":
                    key = data[0][1:]
                    for i, held_key in enumerate(held_keys):
                        if key == held_key:
                            # if key is being released, update held_keys
                            held_keys.pop(i)
                            break
                # calculate elapsed time
                current_time = float(data[-2])
                data[-1] = str(current_time - prev_time)
                prev_time = current_time
            data.pop(-2)
            f.write(" ".join(data) + "\n")


def run_automator(log, repeat_num=1, time_precision=10, stop_key=Key.esc):
    class IntVar:
        def __init__(self, value: int = None): self.value = value
        def set(self, value: int): self.value = value
        def get(self): return self.value
        def increment(self, increment=1): self.value += increment

    def stop_automation(key):
        try:
            if key == stop_key:
                key_listener.stop()
                script_copy.clear()
                run_num.set(repeat_num)
        except AttributeError:
            if key == stop_key:
                key_listener.stop()
                script_copy.clear()
                run_num.value = repeat_num

    # convert log file to strings
    script = log_to_string(log, time_precision=time_precision)

    keyboard = Key_Controller()
    mouse = Mouse_Controller()
    key_listener = Key_Listener(on_press=stop_automation)
    key_listener.start()

    # execute script
    run_num = IntVar(0)
    while run_num.value < repeat_num:
        script_copy = script.copy()
        while len(script_copy) > 0:
            exec(script_copy.popleft())
        run_num.increment()
    script.clear()


def log_to_string(log, time_precision=2):
    # add file extension if missing
    file_ext = os.path.splitext(log)[1]
    if not file_ext:
        log += ".log"
    log = os.path.join(log_folder, log)

    with open(log) as f:
        script_q = deque()
        f = f.readlines()
        for line in f:
            data = list(line.split(" "))
            script_line = "time.sleep({0})".format(round(float(data[len(data) - 1]), time_precision))
            script_q.append(script_line)
            if len(data) > 2:
                xy = data[1].split(",")
                script_line = "pyautogui.moveTo({0}, {1}, _pause=False)".format(xy[0], xy[1])
                script_q.append(script_line)
            if data[0][0] == "+" and len(data[0]) == 2:
                script_line = "keyboard.press('{0}')".format(data[0][1:])
            elif data[0][0] == "+":
                script_line = "keyboard.press({0})".format(data[0][1:])
            elif data[0][0] == "-" and len(data[0]) == 2:
                script_line = "keyboard.release('{0}')".format(data[0][1:])
            elif data[0][0] == "-":
                script_line = "keyboard.release({0})".format(data[0][1:])
            elif data[0][0] == "1":
                script_line = "mouse.click({0})".format(data[0][1:])
            elif data[0][0] == "0":
                script_line = "mouse.release({0})".format(data[0][1:])
            elif data[0][0] == "^":
                script_line = "mouse.scroll(0, -1)"
            elif data[0][0] == "_":
                script_line = "mouse.scroll(0, 1)"
            elif data[0][0] == "<":
                script_line = "mouse.scroll(-1, 0)"
            elif data[0][0] == ">":
                script_line = "mouse.scroll(1, 0)"
            script_q.append(script_line)
        return script_q


def get_recording(log):
    return log_to_string(log)


def account_for_duplicate_filenames(file_name):
    # add file extension if missing
    file_ext = os.path.splitext(file_name)[1]
    if not file_ext:
        file_name += ".log"

    # return if file_name does not exist
    if not os.path.exists(file_name):
        return file_name
    else:
        # append for duplicates
        path_temp = os.path.splitext(file_name)[0]
        i = 1
        while True:
            filename = "{0}_({1}).log".format(path_temp, str(i))
            if not os.path.exists(filename):
                return filename
            i += 1


def is_duplicate(file_name):
    file_name = os.path.splitext(file_name)[0]
    if file_name[-2].isnumeric():
        return True
    else:
        return False


def get_automation_logs(include_raws=False):
    dir_list = os.listdir(log_dir)
    log_list = [os.path.splitext(log)[0] for log in dir_list]
    if not include_raws:
        i = 0
        while i < len(log_list):
            log = log_list[i]
            if log[-4:] == "_RAW":
                log_list.pop(i)
                continue
            elif is_duplicate(log):
                if log[-8:-4] == "_RAW":
                    log_list.pop(i)
                    continue
            i += 1
    return log_list


def delete_log(file, also_delete_raw=True):
    file = os.path.splitext(file)[0] + ".log"
    os.remove(os.path.join(log_dir, file))
    if also_delete_raw:
        file_raw_path = os.path.join(log_dir, file[:-4] + "_RAW" + file[-4:])
        if os.path.exists(file_raw_path):
            os.remove(file_raw_path)


def rename_log(file, new_name, also_rename_raw=True):
    file = os.path.splitext(file)[0] + ".log"
    new_name = os.path.splitext(new_name)[0]
    if not new_name:
        new_name = "New_log"
    new_name += ".log"
    os.rename(os.path.join(log_dir, file), os.path.join(log_dir, new_name))
    if also_rename_raw:
        file_raw_path = os.path.join(log_dir, file[:-4] + "_RAW" + file[-4:])
        if os.path.exists(file_raw_path):
            os.rename(file_raw_path, os.path.join(log_dir, new_name[:-4] + "_RAW" + new_name[-4:]))
