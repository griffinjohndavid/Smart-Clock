# Smart-Clock
A smart clock powered by the Raspberry Pi. Displays current time, weather, and a random Bible verse throughout the day.

## Installation and Updating
### Code
If you have [git](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git) installed, clone the repository.

```
git clone git@github.com:jgriffin3/Smart-Clock.git
```

**Alternatively, you can download a zip file containing the project (green button on the [repository page](https://github.com/jgriffin3/Smart-Clock))**

Navigate to the folder for the repository

```
cd /path/to/Smart-Clock
```

### Install your dependencies
Make sure you have [pip](https://pip.pypa.io/en/stable/installing/) installed before doing this. The requirements file will ensure that the following are installed:
* requests
* feedparser
* Pillow

```
sudo pip3 install -r requirements.txt
```

### Add your API token
You will need to get an API token from [DarkSky](https://darksky.net/dev) to get weather to work. Simple create a free account and replace `weather_api_token` with the token you get from DarkSky.

## Running
To run the application run the following command in this folder

```
python smartclock.py
```
