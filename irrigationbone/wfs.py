#!/usr/bin/python
import os
import select
import time
from wfs_config import *
from logger import logger, logger_init
from munch import *
import contextlib

debug = False

def init_data():
  data = Munch()
  data.bounces_counter = 0
  data.lastEventOnTimestamp = 0
  data.pipe_is_empty = True
  data.messured_max_bounces = 0
  data.previous_bounces_counter = 0
  #data.previous_time_diff = 0
  data.litter_counter = 0
  data.last_litter_advance = 0
  data.start_time = time.time()
  return data

@contextlib.contextmanager
def init_gpio():
  gpio_path = os.path.join( gpio_base, 'gpio' + gpio )
  with open(os.path.join(gpio_path, 'value'), 'r') as gpio_fd:
    po = select.epoll()
    po.register(gpio_fd, select.EPOLLIN | select.EPOLLET)
    yield gpio_fd,po
    po.unregister(gpio_fd)

def is_pipe_broken( events, data ):
  if not events and not debug : # if pool timed out check total waterflow timeuout
   if data.pipe_is_empty \
      and (data.eventTimestamp - data.lastEventOnTimestamp) >= WATERFLOW_TIMEOUT \
      or (data.eventTimestamp - data.lastEventOnTimestamp) >= ( 5* WATERFLOW_TIMEOUT):
     message = 'No flow sensed for {} secs , which is pass the timeout. Irrigated {} litters'.format(\
      (data.eventTimestamp - data.lastEventOnTimestamp), (data.litter_counter/5.5) )
     logger.error( message )
     raise Exception( message )

def is_pipe_empty( data ):
  if not data.pipe_is_empty :
    return False
    #timeout_expired = ( event_timestamp - data.start_time ) > PIPE_FULL_TIMEOUT
    #irrigation_started = data.litter_counter > 1
    #flow_rate_reduced = data.time_since_last_event < data.previous_time_diff
    #if irrigation_started and flow_rate_reduced or timeout_expired :
  data.messured_max_bounces = max(data.bounces_counter,data.messured_max_bounces)
  logger.debug('is_pipe_empty messured_max_bounces: {}'.format(data.messured_max_bounces))
  if data.previous_bounces_counter == 0 :
    return True
  if data.previous_bounces_counter < data.messured_max_bounces/2:
    logger.debug('Pipe is now full of water')
    data.pipe_is_empty = False
    data.litter_counter = 0
    return False

def advance_litter_counter( data ):
    if ( data.rawState == ON )\
        and ( (data.eventTimestamp - data.last_litter_advance) >= DEBOUNCE_DELAY ):
      if not is_pipe_empty( data ):
        data.litter_counter += 1
        logger.info( 'Advancing litter counter to {}'.format( data.litter_counter ) )
      data.previous_bounces_counter = data.bounces_counter
      data.bounces_counter = 0
      data.last_litter_advance = data.eventTimestamp

      #data.previous_time_diff = data.time_since_last_event
      #flow_rate = 1/data.time_since_last_event
      #logger.debug( 'Rate graph: {} : {} : {}'.format( data.eventTimestamp, data.time_since_last_event, flow_rate ) )

def check_bounces( data ):
    if ( data.rawState == ON ) : # and ( data.time_since_last_event < DEBOUNCE_DELAY ):
      data.bounces_counter += 1
      #logger.debug( 'Advancing bounce counter to {}'.format( data.bounces_counter ) )
      if data.bounces_counter >= MAX_BOUNCE_RATE :
        logger.debug('pipe_is_empty flag is: {}'.format( data.pipe_is_empty ))
        raise Exception('Got {} repeated bounces, the pipe may be broken, quiting'.format( MAX_BOUNCE_RATE ) )

def main( litres ):
  data = init_data()
  logger.info( '{} Called to water {} litres'.format( __file__ , litres ) )
  with init_gpio() as (gpio_fd,po):
    #pulse_logger = logger_init( PULSE_LOG_FILENAME )
    while ( time.time() - data.start_time ) < MAX_IRRIGATION_TIMEOUT :
      if not data.pipe_is_empty and ( data.litter_counter > ( litres * 5.5) )\
         and not debug:
        logger.info( '{} ended irrigating {} litres'.format( __file__, litres ) )
        break
      events = po.poll( WATERFLOW_TIMEOUT )
      gpio_fd.seek(0)
      data.rawState = gpio_fd.read().strip()
      data.eventTimestamp = time.time()
      data.time_since_last_event = data.eventTimestamp - data.lastEventOnTimestamp
      #pulse_logger.debug( data.rawState )

      is_pipe_broken( events, data )
      if not events :
        logger.error( 'Got an empty event when polling flow sensor' )
        continue
      advance_litter_counter( data )
      logger.debug( '\
 time: {},\
 empty: {},\
 bounces_counter: {},\
 litter_counter: {},\
 time_since_last_event: {},\
 previous_bounces_counter: {},\
 messured_max_bounces: {}\
 '.format( \
              data.eventTimestamp,\
              data.pipe_is_empty,\
              data.bounces_counter,\
              data.litter_counter,\
              data.time_since_last_event,\
              data.previous_bounces_counter,\
              data.messured_max_bounces\
              ) )
      check_bounces( data )
      if ( data.rawState == ON ) :
        data.lastEventOnTimestamp = data.eventTimestamp

  if ( time.time() - data.start_time ) >= MAX_IRRIGATION_TIMEOUT :
    raise Exception( 'Max irrigation {} secs timeout reached, irrigated {} litters'.format( \
      MAX_IRRIGATION_TIMEOUT, (data.litter_counter/5.5) ) )

if __name__ == '__main__' :
  debug = True
  main(0)
"""
This sensor: http://www.seeedstudio.com/wiki/G3/4_Water_Flow_sensor
Shows a coeff of 5.5 between pulse frequecy and flow rate.
when the flow rate is  2L/min it issues pulses at 11Hz
When the flow rate is 10L/min it issues pulses at 55Hz
sensor range is 1-60 L/min, so the frequency range is 5.5-330Hz
converting min -> sec:
range is 0.01667-1 L/sec
"""
