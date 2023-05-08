import configparser


config = configparser.ConfigParser()

try:
    config.read("conf/config.ini")
    print("reading config")
except:
    print("Reading conf/config.ini error")
