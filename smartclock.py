# Imports
from tkinter import *
import time
import threading
import locale
import requests
import traceback
import json
from contextlib import contextmanager
from PIL import Image, ImageTk
import re #regex

# Globals
LOCALE_LOCK = threading.Lock()
ui_locale = '' # 'en_US' for English (Default: '') - For help: https://stackoverflow.com/a/3191729
time_format = 12 # 12 or 24 (MUST BE A NUMBER)
date_format = "%b %d, %Y" # Format for strftime() (Default: "%b %d, %Y") - For help: http://strftime.org/
xlarge_text_size = 70
large_text_size = 32
medium_text_size = 18
small_text_size = 12
weather_api_token = 'ce4a1fcd2f9c208b7823b933e764cc3a' # create account at https://darksky.net/dev/
weather_lang = 'en' # see https://darksky.net/dev/docs/forecast for full list of language parameters values
weather_unit = 'us' # see https://darksky.net/dev/docs/forecast for full list of unit parameters values
latitude = "35.2468" # Set this if IP location lookup does not work for you (must be a string)
longitude = "-91.7337" # Set this if IP location lookup does not work for you (must be a string)

# Weather Icons
icon_lookup = {
    'clear-day': "assets/Sun.png",  # clear sky day
    'wind': "assets/Wind.png",   #wind
    'cloudy': "assets/Cloud.png",  # cloudy day
    'partly-cloudy-day': "assets/PartlySunny.png",  # partly cloudy day
    'rain': "assets/Rain.png",  # rain day
    'snow': "assets/Snow.png",  # snow day
    'snow-thin': "assets/Snow.png",  # sleet day
    'fog': "assets/Haze.png",  # fog day
    'clear-night': "assets/Moon.png",  # clear sky night
    'partly-cloudy-night': "assets/PartlyMoon.png",  # scattered clouds night
    'thunderstorm': "assets/Storm.png",  # thunderstorm
    'tornado': "assests/Tornado.png",    # tornado
    'hail': "assests/Hail.png"  # hail
}


@contextmanager
def setlocale(name): #thread proof function to work with locale
    with LOCALE_LOCK:
        saved = locale.setlocale(locale.LC_ALL)
        try:
            yield locale.setlocale(locale.LC_ALL, name)
        finally:
            locale.setlocale(locale.LC_ALL, saved)

def changeTimeFormat(event):
    if globals()['time_format'] == 12:
        globals()['time_format'] = 24
    elif globals()['time_format'] == 24:
        globals()['time_format'] = 12


# Clock Class adapted from Smart-Mirror (https://github.com/HackerHouseYT/Smart-Mirror)
class Clock(Frame):
    def __init__(self, parent, *args, **kwargs):
        Frame.__init__(self, parent, bg='black')

        # initialize time label
        self.time1 = ''
        self.timeLbl = Label(self, font=('Helvetica', large_text_size), fg="white", bg="black")
        self.timeLbl.pack(side=TOP, anchor=E)
        self.timeLbl.bind("<Button-1>", changeTimeFormat)

        # initialize day of week
        # self.day_of_week1 = ''
        self.dayOWLbl = Label(self, font=('Helvetica', small_text_size), fg="white", bg="black")
        self.dayOWLbl.pack(side=TOP, anchor=E)

        # initialize date label
        self.date1 = ''
        self.fulldate = ''
        self.dateLbl = Label(self, text=self.date1, font=('Helvetica', small_text_size), fg="white", bg="black")
        self.dateLbl.pack(side=TOP, anchor=E)
        self.tick()

    def tick(self):
        with setlocale(ui_locale):
            if time_format == 12:
                time2 = time.strftime('X%I:%M %p').replace('X0','X').replace('X','') #hour in 12h format
            else:
                time2 = time.strftime('X%H:%M').replace('X0','X').replace('X','') #hour in 24h format

            day_of_week2 = time.strftime('%A')
            date2 = time.strftime(date_format)
            fulldate2 = day_of_week2 + ", " + date2

            # if time string has changed, update it
            if time2 != self.time1:
                self.time1 = time2
                self.timeLbl.config(text=time2)
            if fulldate2 != self.fulldate:
                self.fulldate = fulldate2
                self.dayOWLbl.config(text=fulldate2)

            # calls itself every 200 milliseconds
            # to update the time display as needed
            # could use >200 ms, but display gets jerky
            self.timeLbl.after(200, self.tick)


# Weather Class adapted from Smart-Mirror (https://github.com/HackerHouseYT/Smart-Mirror)
class Weather(Frame):
    def __init__(self, parent, *args, **kwargs):
        Frame.__init__(self, parent, bg='black')
        self.temperature = ''
        self.forecast = ''
        self.location = ''
        self.currently = ''
        self.icon = ''
        self.degreeFrm = Frame(self, bg="black")
        self.degreeFrm.pack(side=TOP, anchor=W)
        self.temperatureLbl = Label(self.degreeFrm, font=('Helvetica', large_text_size), fg="white", bg="black")
        self.temperatureLbl.pack(side=LEFT, anchor=N)
        self.temperatureLbl.bind("<Button-1>", self.changeWeatherFormat)
        self.iconLbl = Label(self.degreeFrm, bg="black")
        self.iconLbl.pack(side=LEFT, anchor=N, padx=20)
        self.currentlyLbl = Label(self, font=('Helvetica', medium_text_size), fg="white", bg="black")
        self.currentlyLbl.pack(side=TOP, anchor=W)
        self.forecastLbl = Label(self, font=('Helvetica', small_text_size), fg="white", bg="black",wraplength=375,justify="left")
        self.forecastLbl.pack(side=TOP, anchor=W)
        self.locationLbl = Label(self, font=('Helvetica', small_text_size), fg="white", bg="black")
        self.locationLbl.pack(side=TOP, anchor=W)
        self.get_weather()

    def get_ip(self):
        try:
            ip_url = "http://jsonip.com/"
            req = requests.get(ip_url)
            ip_json = json.loads(req.text)
            return ip_json['ip']
        except Exception as e:
            traceback.print_exc()
            return "Error: %s. Cannot get ip." % e

    def changeWeatherFormat(self, event2):
        if globals()['weather_unit'] == 'us':
            globals()['weather_unit'] = 'si'
        elif globals()['weather_unit'] == 'si':
            globals()['weather_unit'] = 'us'

        self.get_weather()

    def get_weather(self):
        try:
            if latitude is None and longitude is None:
                # get location
                location_req_url = "http://freegeoip.net/json/%s" % self.get_ip()
                r = requests.get(location_req_url)
                location_obj = json.loads(r.text)
                lat = location_obj['latitude']
                lon = location_obj['longitude']
                location2 = "%s, %s" % (location_obj['city'], location_obj['region_code'])

                # get weather
                weather_req_url = "https://api.darksky.net/forecast/%s/%s,%s?lang=%s&units=%s" % (weather_api_token, lat,lon,weather_lang,weather_unit)
            else:
                location2 = ""
                
                # get weather
                weather_req_url = "https://api.darksky.net/forecast/%s/%s,%s?lang=%s&units=%s" % (weather_api_token, latitude, longitude, weather_lang, weather_unit)

            r = requests.get(weather_req_url)
            weather_obj = json.loads(r.text)

            degree_sign= u'\N{DEGREE SIGN}'
            temperature2 = "%s%s" % (str(int(weather_obj['currently']['temperature'])), degree_sign)
            currently2 = weather_obj['currently']['summary']
            forecast2 = weather_obj["hourly"]["summary"]

            icon_id = weather_obj['currently']['icon']
            icon2 = None
            if icon_id in icon_lookup:
                icon2 = icon_lookup[icon_id]
            if icon2 is not None:
                if self.icon != icon2:
                    self.icon = icon2
                    image = Image.open(icon2)
                    image = image.resize((50, 50), Image.ANTIALIAS)
                    image = image.convert('RGB')
                    photo = ImageTk.PhotoImage(image)
                    self.iconLbl.config(image=photo)
                    self.iconLbl.image = photo
            else:
                # remove image
                self.iconLbl.config(image='')

            if self.currently != currently2:
                self.currently = currently2
                self.currentlyLbl.config(text=currently2)
                
            if self.forecast != forecast2:
                self.forecast = forecast2
                self.forecastLbl.config(text=forecast2)

            if self.temperature != temperature2:
                self.temperature = temperature2
                self.temperatureLbl.config(text=temperature2)

            if self.location != location2:
                if location2 == ", ":
                    self.location = "Cannot Pinpoint Location"
                    self.locationLbl.config(text="Cannot Pinpoint Location")
                else:
                    self.location = location2
                    self.locationLbl.config(text=location2)

        except Exception as e:
            traceback.print_exc()
            print("Error: %s. Cannot get weather." % e)

        self.after(600000, self.get_weather)

    @staticmethod
    def convert_kelvin_to_fahrenheit(kelvin_temp):
        return 1.8 * (kelvin_temp - 273) + 32


# RandomVerse Class fetches a random verse every 30 minutes
class RandomVerse(Frame):
    def __init__(self, parent, *args, **kwargs):
        Frame.__init__(self, parent, bg='black')
        self.book = ''
        self.chapter = ''
        self.verse = ''
        self.verseText = ''
        self.verseRef = ''
        self.verseFrm = Frame(self, bg="black")
        self.verseFrm.pack(side=TOP, anchor=W)
        self.verseTxt = Label(self.verseFrm, font=('Helvetica', small_text_size), fg="white", bg="black",wraplength=375,justify="left")
        self.verseTxt.pack(side=LEFT, anchor=N)
        self.verseLbl = Label(self, font=('Helvetica ' + str(small_text_size) + ' italic'), fg="white", bg="black")
        self.verseLbl.pack(side=TOP, anchor=W)
        self.get_verse()

    def get_verse(self):
        try:
            # get verse
            verse_req_url = "http://labs.bible.org/api/?passage=random&type=json"
            r = requests.get(verse_req_url)
            verse_obj = json.loads(r.text)
            book2 = verse_obj[0]['bookname']
            chapter2 = verse_obj[0]['chapter']
            verse2 = verse_obj[0]["verse"]
            verseText2 = "\"" + re.sub("<[^>]*>", "", verse_obj[0]["text"]) + "\"";
            ref = "— %s %s:%s" % (book2, chapter2, verse2)

            if self.verseRef != ref:
                self.verseRef = ref
                self.verseLbl.config(text=ref)

            if self.verseText != verseText2:
               self.verseText = verseText2
               self.verseTxt.config(text=verseText2)

        except Exception as e:
            traceback.print_exc()
            print("Error: %s. Cannot get verse." % e)

        self.after(1800000, self.get_verse)


# FullscreenWindow Class adapted from Smart-Mirror (https://github.com/HackerHouseYT/Smart-Mirror)
class FullscreenWindow:
    def __init__(self):
        self.tk = Tk()
        self.tk.configure(background='black', cursor='none')
        self.topFrame = Frame(self.tk, background = 'black')
        self.bottomFrame = Frame(self.tk, background = 'black')
        self.topFrame.pack(side = TOP, fill=BOTH, expand = YES)
        self.bottomFrame.pack(side = BOTTOM, fill=BOTH, expand = YES)
        self.state = False
        self.tk.bind("<Return>", self.toggle_fullscreen)
        self.tk.bind("<Escape>", self.end_fullscreen)

        # CLOCK
        self.clock = Clock(self.topFrame)
        self.clock.pack(side=RIGHT, anchor=N, padx=60, pady=60)

        # WEATHER
        self.weather = Weather(self.topFrame)
        self.weather.pack(side=LEFT, anchor=N, padx=60, pady=60)

        # VERSE
        self.verse = RandomVerse(self.bottomFrame)
        self.verse.pack(side=LEFT, anchor=S, padx=60, pady=60)

    def toggle_fullscreen(self, event=None):
        self.state = not self.state  # Just toggling the boolean
        self.tk.attributes("-fullscreen", self.state)
        return "break"

    def end_fullscreen(self, event=None):
        self.state = False
        self.tk.attributes("-fullscreen", False)
        return "break"

if __name__ == '__main__':
    w = FullscreenWindow()
    w.tk.mainloop()
    
