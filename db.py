
import configuration


import sqlite3


create_full_db = """
	    CREATE TABLE driver (
	    id INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE,
	    fullname TEXT,
	    nickname TEXT);
	    CREATE TABLE car (
	    id INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE,
	    mark TEXT,
	    model TEXT,
	    year NUMBER,
	    register TEXT,
	    notes TEXT,
	    fueltype INTEGER);
	    CREATE TABLE record(
	    id INTEGER PRIMARY KEY AUTOINCREMENT,
	    carid INTEGER,
	    driverid INTEGER,
	    day TIMESTAMP,
	    km REAL,
	    trip REAL,
	    fill REAL,
	    consum REAL,
	    price REAL,
	    priceperlitre REAL,
	    service REAL,
	    oil REAL,
	    tires REAL,
	    insurance REAL,
	    other REAL,
	    notes TEXT);
	    CREATE TABLE alarmtype (
	    id INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE,
	    carid INTEGER,
	    shortdesc TEXT,
	    distance NUMBER,
	    interval INTEGER,
	    longdesc TEXT);
	    CREATE TABLE alarmevent (
	    id INTEGER PRIMARY KEY AUTOINCREMENT,
	    alarmid INTEGER,
	    carid INTEGER,
	    driverid INTEGER,
	    recordid INTEGER,
	    day TIMESTAMP,
	    km REAL);
	    INSERT INTO driver(fullname,nickname)
	    VALUES('Default Driver','Default');
	    INSERT INTO car(mark,model,year,register,notes)
	    VALUES('Default','Model',2007,'ABC-123','');
"""

create_db = """
	    CREATE TABLE driver (
	    id INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE,
	    fullname TEXT,
	    nickname TEXT);
	    CREATE TABLE car (
	    id INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE,
	    mark TEXT,
	    model TEXT,
	    year NUMBER,
	    register TEXT,
	    notes TEXT);
	    CREATE TABLE record(
	    id INTEGER PRIMARY KEY AUTOINCREMENT,
	    carid INTEGER,
	    driverid INTEGER,
	    day TIMESTAMP,
	    km REAL,
	    trip REAL,
	    fill REAL,
	    consum REAL,
	    price REAL,
	    priceperlitre REAL,
	    service REAL,
	    oil REAL,
	    tires REAL,
	    insurance REAL,
	    other REAL,
	    notes TEXT);
"""

default_insert = """
	    INSERT INTO driver(fullname,nickname) VALUES ('Default Driver','Default');
	    INSERT INTO car(mark,model,year,register,notes) VALUES('Default','Model',2007,'ABC-123','');
"""

create_alarms =  """
		 CREATE TABLE alarmtype (
		 id INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE,
		 carid INTEGER,
		 shortdesc TEXT,
		 distance NUMBER,
		 interval INTEGER,
		 longdesc TEXT);
		 CREATE TABLE alarmevent (
		 id INTEGER PRIMARY KEY AUTOINCREMENT,
		 alarmid INTEGER,
		 carid INTEGER,
		 driverid INTEGER,
		 recordid INTEGER,
		 day TIMESTAMP,
		 km REAL);
"""

create_gpsinfo = """ALTER TABLE record ADD COLUMN gpstime TIMESTAMP;
                    ALTER TABLE record ADD COLUMN lat REAL;
                    ALTER TABLE record ADD COLUMN lon REAL;"""


import location , gobject

delay_for_fix = 120

class timed_locator :

    def __init__ ( self , rowid , database ) :
        self.rowid , self.db = rowid , database
        self.control = location.GPSDControl.get_default()
        self.device = None
        self.update_handler , self.timeout_handler = None , None
        self.fix = None
        self.time = None
        self.lat , self.lon = None , None
        self.do_start()

    def do_start ( self ) :
        if not self.device :
            self.device = location.GPSDevice()
        if not self.update_handler :
            self.update_handler = self.device.connect_object("changed", self.do_update , None )
            self.timeout_handler = gobject.timeout_add( delay_for_fix * 1000 , self.do_stop )
            self.control.start()

    def do_stop ( self ) :
        if self.update_handler :
            self.device.disconnect( self.update_handler )
            self.update_handler = None
        if self.time :
            query = "UPDATE RECORD set gpstime=%s WHERE id=%d" % ( self.time , self.rowid )
            self.db.execute( query )
            if self.lat and self.lon :
                query = "UPDATE RECORD set lat=%s , lon=%s WHERE id=%d" % ( self.lat , self.lon , self.rowid )
                self.db.execute( query )
            self.db.commit()
        self.device.stop()
        self.control.stop()
        if self.timeout_handler :
            gobject.source_remove( self.timeout_handler )
            self.timeout_handler = None

    def do_update ( self , data=None ) :

        if self.device :
            flags = self.device.fix[1]
            if self.device.status == location.GPS_DEVICE_STATUS_FIX :
                if flags & location.GPS_DEVICE_TIME_SET :
                    self.time = self.device.fix[2]
                if flags & location.GPS_DEVICE_LATLONG_SET :
                    self.lat , self.lon = self.device.fix[4:6]
                if flags & ( location.GPS_DEVICE_TIME_SET | location.GPS_DEVICE_LATLONG_SET ) :
                    # FIXME : do we need to remove the timeout function previously added ??
                    self.do_stop()


class database :

    def __init__ ( self , dbname=None ) :
        self.result_db = dbname
        self.db = None
        self.currentcar = None
        self.currentdriver = None
        self.locator = None

    def get_current ( self , key ) :
        if key.lower() == "car" :
            return self.currentcar
        if key.lower() == "driver" :
            return self.currentdriver
        raise Exception( "Unknown current value for '%s'" % key )

    def last_refill ( self , newkm ) :
        return self.get_float( "SELECT km FROM record WHERE carid=%d AND trip>0 AND km<%f ORDER BY km DESC LIMIT 1" % ( self.currentcar , newkm ) )

    def last_km ( self ) :
        return self.get_float( "SELECT max(km) FROM record WHERE carid=%d" % self.currentcar )

    def carid ( self , index ) :
        return self.get_float( "SELECT id FROM car LIMIT 1 OFFSET %d" % index )

    def driverid ( self , index ) :
        return self.get_float( "SELECT id FROM driver LIMIT 1 OFFSET %d" % index )

    def fueltype ( self ) :
        return self.get_float( "SELECT fueltype FROM car WHERE id=%d" % self.currentcar )

    def get_float ( self, query ) :
        result = self.get_single( query )
        if result :
            return float( result )
        return 0.0

    def get_single ( self, query ) :
        if self.is_open() :
            rc = self.db.execute( query )
            result = rc.fetchone()
            if result :
                return result[0]
        return None

    def setfilename ( self , dbname ) :
        self.result_db = dbname

    def open ( self , config ) :

        if self.db :
            self.close()

        self.db = sqlite3.connect( self.result_db )

        rc = self.db.execute( "SELECT * FROM sqlite_master" )
        tables = map( lambda x : "%s-%s" % ( x[0] , x[1] ) , rc.fetchall() )

        if not tables :
            # NOTE : we can replace create_full_db with just create_db + default_insert, avoiding return and leaving table updating to subsequent code
            self.db.executescript( create_full_db )
            return

        if "table-alarmtype" not in tables :
            self.db.executescript( create_alarms )

        rc = self.db.execute( "PRAGMA table_info(car)" )
        if "fueltype" not in map( lambda x : x[1] , rc.fetchall() ) :
            rc = self.db.execute( "ALTER TABLE car ADD COLUMN fueltype INTEGER" )

        rc = self.db.execute( "PRAGMA table_info(record)" )
        if "gpstime" not in map( lambda x : x[1] , rc.fetchall() ) :
            rc = self.db.executescript( create_gpsinfo )

        # We don't make any verification on curret car & driver values from configuration
        # self.currentcar = maxid = self.get_float( "SELECT max(id) FROM car" )
        # self.currentdriver = maxid = self.get_float( "SELECT max(id) FROM driver" )

        # And lots of sqlite3_prepare_v2 statements ...

    def close ( self ) :
        self.db.close()
        self.db = None

    def is_open ( self ) :
        if not self.db :
            return False 
        return True 

    def get_rows ( self , query ) :
        rc = self.db.execute( query )
        return rc.fetchall()

    def add_record (self, date, km, trip, fill, consum, price, service, oil, tires, notes) :
  
        # NOTE : move to main functions and to arglist
        priceperlitre = -1
        if fill > 0 :
            priceperlitre = price / fill

        if self.is_open() :

            columns = ( "carid" , "driverid" , "day" , "km" , "trip" , "fill" , "consum" , "price" , "priceperlitre" , "service" , "oil" , "tires" , "notes" )
            values = "%s , %s , '%s' , %s , %s , %s , %s , %s , %s , %s , %s , %s , '%s'" % ( self.currentcar, self.currentdriver, date, km, trip, fill, consum, price, priceperlitre, service, oil, tires, notes )
            query = "INSERT INTO record ( %s ) VALUES  ( %s )" % ( ",".join(columns) , values )
            rc = self.db.execute( query )
            if rc.rowcount :
                self.locator = timed_locator( rc.lastrowid , self.db )
                self.db.commit()
                return rc.lastrowid

        return False

    # Fill view is apparently ported
    def create_fillview ( self ) :
        query = "CREATE TEMP VIEW fillview AS SELECT * FROM record WHERE carid=%d ORDER BY km LIMIT -1 OFFSET 1" % self.currentcar
        return self.db.execute( query )

    def drop_fillview ( self ) :
        return self.db.execute( "DROP VIEW fillview" )

    # Summarizer functions completelly ported
    def totalkm ( self , timespan ) :
    
      if self.is_open() :
    
        querystr = "SELECT %s FROM record WHERE carid=%d %s"
    
        if timespan in ( configuration.OVERALL, configuration.SPANEND ) :
          sqlquery = querystr % ( "MAX(km)-MIN(km)" , self.currentcar , "" )
        elif timespan == configuration.LASTMONTH :
          sqlquery = querystr % ( "SUM(trip)" , self.currentcar , "AND day BETWEEN DATE('now','-1 month') AND DATE('now')" )
        elif timespan == configuration.LASTYEAR :
          sqlquery = querystr % ( "SUM(trip)" , self.currentcar , "AND day BETWEEN DATE('now','-1 year') AND DATE('now')" )
        else :
          sqlquery = querystr % ( "MAX(km)-MIN(km)" , self.currentcar , "" )
    
        rc = self.db.execute( sqlquery )
        res = rc.fetchone()
        if res[0] :
          return float( res[0] )
    
      return 0.0
    
    def totalfillkm ( self , timespan ) :
    
      if self.is_open() :
    
        if self.create_fillview() :
    
          querystr = "SELECT sum(trip) FROM fillview WHERE carid=%d AND fill>0 %s"
    
          if timespan in ( configuration.OVERALL, configuration.SPANEND ) :
            sqlquery = querystr % ( self.currentcar , "" )
          elif timespan == configuration.LASTMONTH :
            sqlquery = querystr % ( self.currentcar , "AND day BETWEEN DATE('now','-1 month') AND DATE('now')" )
          elif timespan == configuration.LASTYEAR :
            sqlquery = querystr % ( self.currentcar , "AND day BETWEEN DATE('now','-1 year') AND DATE('now')" )
          else :
            sqlquery = querystr % ( self.currentcar , "" )
    
          rc = self.db.execute( sqlquery )
          self.drop_fillview();
    
          res = rc.fetchone()
          if res[0] :
            return float( res[0] )
    
      return 0.0
    
    def totalcost ( self ) :
    
      if self.is_open() :
    
        # BUG : We are accounting for all the -1 values !!!
        sqlquery = "SELECT sum(price)+sum(service)+sum(oil)+sum(tires) FROM record WHERE carid=%d" % self.currentcar
    
        rc = self.db.execute( sqlquery )
        res = rc.fetchone()
        if res[0] :
          return float( res[0] )
    
      return 0.0
    
    def totalfill ( self , timespan ) :
    
      if self.is_open() :
    
        if self.create_fillview() :
    
          querystr = "SELECT SUM(fill) FROM fillview WHERE carid=%d %s"
    
          if timespan in ( configuration.OVERALL , configuration.SPANEND ) :
            sqlquery = querystr % ( self.currentcar , "" )
          elif timespan == configuration.LASTMONTH :
            sqlquery = querystr % ( self.currentcar , "AND day BETWEEN DATE('now','-1 month') AND DATE('now')" )
          elif timespan == configuration.LASTYEAR :
            sqlquery = querystr % ( self.currentcar , "AND day BETWEEN DATE('now','-1 year') AND DATE('now')" )
          else :
            sqlquery = querystr % ( self.currentcar , "" )
    
        rc = self.db.execute( sqlquery )
        self.drop_fillview();
    
        res = rc.fetchone()
        if res[0] :
          return float( res[0] )
    
      return 0.0

    def find_prev_full ( self , km ) :
       if self.is_open() :
           query = "SELECT km,trip,fill,consum,id FROM record WHERE carid=%d AND km<%d AND fill>0 ORDER BY km DESC" % ( self.currentcar , km )
           rc = self.db.execute( query )
           result = rc.fetchone()
           if result :
               consum = float( result[3] )
               if not consum*consum > 1e-6 : # Full fill not found
                   return float( result[2] ) , float( result[1] )

       return 0.0 , 0.0

