import sys, os
import logbook

def logger_init( module = __name__ ):
  log_name =  '.'.join( (module, 'log' ) )
  filename=os.path.join( '/home', 'debian', log_name)
  logger = logbook.Logger( module )
  format_string = '{record.time:%Y-%m-%d %H:%M:%S.%f} {record.level_name} {record.message}'
  file_handler = logbook.RotatingFileHandler( filename, mode= 'a', \
                                              format_string=format_string, max_size=5000000000, \
                                              backup_count=1 , filter=lambda r, h: r.channel == module)
  file_handler.push_application()
  return logger

f=sys.argv[0].split('/')[-1]
logger = logger_init( f )
