import sys, time, configparser, logging, threading
import Instabot
import tkinter as tk
from datetime import datetime
from queue import Queue
from threading import Thread, RLock
from tkinter import ttk



class StdoutRedirector(object):
    """sys.stdout redirect to tkinter text widget.\n
        Pass in the text widget object.\n
        Declare inside the tkinter run method."""
    def __init__(self, widget):
        self.box = widget

    def write(self, string):
        self.box['state'] = 'normal'
        self.box.insert('end', string)
        self.box.see('1.0')
        self.box['state'] = 'disabled'

    def flush(self):
        pass


class GUI(object):
    """GUI Thread """
    def __init__(self):
        self.main_window = None

    def run(self):
        self.main_window = MainWindow(self)
        self.main_window.run()


class Window(object):
    """Set Shared Window Variables"""
    def __init__(self, title, font):
        self.root = tk.Tk()
        self.root.title(title)
        self.font = font
        self.lock = RLock()


    def update(self):
        """GUI Update Action\n
            Update and Sleep for 1 Second"""
        with self.lock:
            self.root.update()
            time.sleep(1)
        return True


class MainWindow(Window):
    """Main Window"""
    def __init__(self, gui):
        super().__init__('Python Instagram Bot',('Comic Sans MS', 10, 'bold'))
        
        self.output_box = None
        self.submit_button = None

        #Variables for Dynamic GUI
        self.posts = tk.StringVar(value=0)
        self.follows = tk.StringVar(value=0)

        #Build Main Window
        self.build_window()

    def build_window(self):
        """Build Main Window, Widgets and Event Bindings"""
        self.root.geometry('850x730+1000+200')
        self.root.minsize(850, 730)

        #Main Frame
        self.main_frame = tk.Frame(self.root)
        self.main_frame.grid(row=0, column=0)

        #User Input Label Frame
        self.user_lbframe = ttk.LabelFrame(self.main_frame, text="Command and Control:")
        self.user_lbframe.grid(row=0, column=0, padx=5, pady=5)
        
        ttk.Label(self.user_lbframe, text="Posts Liked: ").grid(row=1, column=0, sticky="W")
        self.liked_posts = ttk.Entry(self.user_lbframe, width=7, state='readonly', textvariable=self.posts)
        self.liked_posts.grid(row=1, column=0, padx=0, pady=5, sticky="E")

        ttk.Label(self.user_lbframe, text="New Followings: ").grid(row=2, column=0, sticky="W")
        self.followings = ttk.Entry(self.user_lbframe, width=7, state='readonly', textvariable=self.follows)
        self.followings.grid(row=2, column=0, padx=0, pady=5, sticky="E")

        #Start Button
        self.submit_button = ttk.Button(self.user_lbframe, text="Start InstaBot", command =self.start)
        self.submit_button.grid(row=3, column=0, pady=5, sticky='E')

        #Stop Button
        self.stop_button = ttk.Button(self.user_lbframe, text="Stop InstaBot", command =self.stop)
        self.stop_button.grid(row=3, column=0, pady=5, sticky='W')

        #Progress Bar
        self.progress_bar = ttk.Progressbar(self.user_lbframe, orient='horizontal', length=150, mode='indeterminate')
        self.progress_bar.grid(row=4, column=0, padx=25, pady=5)
        
        
        #Output Label Frame
        self.output_lbframe = ttk.LabelFrame(self.main_frame, text='Output Box')
        self.output_lbframe.grid(row=2, column=0, padx=25, pady=5)

        #Output Box
        self.output_box = tk.Text(self.output_lbframe, font=self.font, width=95, height=30, wrap='word', state='disabled')
        self.output_box.grid(row=1, column=0, padx=5, pady=5)
        self.output_scroll = ttk.Scrollbar(self.output_lbframe, orient='vertical', command=self.output_box.yview)
        self.output_scroll.grid(row=1, column=1, sticky='ns')


    def run(self):
        """Main Class Function"""
        
        sys.stdout = StdoutRedirector(self.output_box)
        self.root.mainloop()


    def start(self):
        """Start Button Callback"""
        #GUI Function
        self.submit_button['state'] = 'DISABLED'
        #Thread Progress Bar and Start
        self.thread = Thread(daemon=True, target=self.progress_bar.start())
        self.thread.start()
        print(f'[{datetime.now().time()}] Starting InstaBot....')
        self.root.update()
        

        #Define Function Variables
        insta_bot = Instabot.InstagramBot()
        
        #Hashtag Spider (LONG PROCESS)
        try:
            insta_bot.login()
            if insta_bot.logged_in == False:
                insta_bot.quit()
                self.pause()
            else:
                print('Logged in')
                self.root.update()
                que = insta_bot.queue()
            while que != False:
                print('Starting Spider for {}'.format(que))
                insta_bot.spider_scrawl(que)
                data = insta_bot.update()
                self.posts.set(str(data[0]))
                self.follows.set(str(data[1]))
                print(f' Acquired data from Spider- Pictures Liked: {data[0]} / New Following: {data[1]})
                self.root.update()
                time.sleep(1)
                insta_bot.queue()
            print('Finished Tag Spider')
        except TimeoutError as e:
            print('Search Tag Spider Error, Check XML Paths')
            print(e)
        except Exception as e:
            print('GUI Call Error')
            print(e)
        finally:
            self.output_box
            self.root.update()
            self.pause()


    def pause(self):
        """When the Start Button Loop is finished\n Call This Function"""
        self.progress_bar.stop()
        self.submit_button['state'] = 'NORMAL'
        self.output_box.see('end')
        print('InstaBot Paused')
        self.root.update()


    def stop(self):
        """Terminate Instabot"""
        with self.lock:
            print(str(threading.active_count()))
            print(str(threading.current_thread()))
            print(threading.enumerate())
            print(threading.main_thread())
            self.progress_bar.stop
            print('[{}] InstaBot Stopped')
            self.root.update()
            time.sleep(3)
            self.root.destroy()


def main():
    '''Start the GUI'''
    app = GUI()
    app.run()


if __name__ == '__main__': main()
