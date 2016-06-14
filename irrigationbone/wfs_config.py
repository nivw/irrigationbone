gpio_base = '/sys/class/gpio'
gpio = '48' #P9_15
ON = "1"
OFF = "0"
# sensor is between 1L/min to 60L/min
# 5.5 pulses are 1 litre, 
# assume 1L/1min flow constantly its 60sec /5.5 pulse = 10.9 sec
# if 60L/1min flow constatly its 60sec / 60*5.5 pulses = 181.8 msec
DEBOUNCE_DELAY = 1/5.5  #sec
BOUNCE_COUNT_THRESHOLD = 1
WATERFLOW_TIMEOUT = 60 #no water flow for a minute
PULSE_LOG_FILENAME = "pulse"
MAX_BOUNCE_RATE = 1000 # was 7.7 is messures
PIPE_FULL_TIMEOUT = 120 # in 60 secs the pipe will be full
MAX_IRRIGATION_TIMEOUT = 60*60 # 60 min is the max irrigation time
DEBUG = True
