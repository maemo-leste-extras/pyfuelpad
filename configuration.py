
import db

import os
import gconf

default_db = os.path.join( os.environ['HOME'] , "fuelpad.db" )

# fontscale
XSMALL=1
SMALL=2
MEDIUM=3
LARGE=4

fontsizes = [ 'Preconfigured' , 'XSMALL' , 'SMALL' , 'MEDIUM' , 'LARGE' ]

import pango
fontscalefactors = ( pango.SCALE_MEDIUM , pango.SCALE_X_SMALL , pango.SCALE_SMALL , pango.SCALE_MEDIUM , pango.SCALE_LARGE , pango.SCALE_XX_LARGE )

# text size : create/modify pango attributes
def font_attrs ( fontsize , widget=None ) :
    attr = pango.AttrScale( fontscalefactors[fontsize] , 0 , -1 )
    if widget :
        attrs = widget.get_attributes()
        attrs.insert(attr)
    else :
        attrs = pango.AttrList()
        attrs.change(attr)
    return attrs


# DB format is hardcoded to "%Y-%m-%d"
# Possible date format strings (see strptime(3) for format descri ption) 
datefmtstr = ("%Y-%m-%d", "%d.%m.%Y", "%d/%m/%Y", "%d/%m/%y",
                    "%d-%m-%Y", "%m/%d/%Y", "%m/%d/%y")


# unit
unitsystem = [ 'SI' , 'US' , 'IMPERIAL' ]
unitrange = range( len(unitsystem) )

unitnames = {}
unitnames['length'] = [ "Km" , "Mile" , "Mile" ]
unitnames['volume'] = [ "Litre" , "Gallon" , "Litre" ]
unitnames['consume'] = [ "Litre/\n100 Km" , "MPG" , "Litre/Mile" ]
unitnames['mass'] = [ "CO2 Emissions\n[g/km]" , "CO2 Emissions\n[lb/100 miles]" , "CO2 Emissions\n[lb/miles]" ]

# dbtimespan
OVERALL=0
LASTYEAR=1
LASTMONTH=2
SPANEND=3

# enum
COL_DAY=0
COL_KM=1
COL_TRIP=2
COL_FILL=3
COL_CONSUM=4
COL_PRICE=5
COL_PRICEPERTRIP=6
COL_PRICEPERLITRE=7
COL_SERVICE=8
COL_OIL=9
COL_TIRES=10
# COL_INSURANCE
# COL_OTHER
COL_CO2EMISSION=11
COL_NOTES=12
COL_ID=13
COL_VISIBLE=14
NUM_COLS=15

DISPCOLDEFAULT = 1<<COL_NOTES | 1<<COL_PRICEPERTRIP | 1<<COL_PRICE | 1<<COL_CONSUM | 1<<COL_FILL | 1<<COL_TRIP | 1<<COL_KM | 1<<COL_DAY

# COLUMN ITEM : number , header/unittype , ( format , header format ) ,  showable , comparison
column_info = (
    ( 0 , "DAY" , "Date" , None , "%s" , True , "date" ) ,
    ( 1 , "KM" , "length" , None , "%.0f" , True , "number" ) ,
    ( 2 , "TRIP" , "length" , "Trip\n[%s]" , "%.1f" , True , "number" ) ,
    ( 3 , "FILL" , "volume" , "Fill\n[%s]" , "%.2f" , True , "number" ) ,
    ( 4 , "CONSUM" , "consume" , "consume: %s" , "%.1f" , True , "number" ) ,
    ( 5 , "PRICE" , "Price" , None , "%.2f" , True , "number" ) ,
    ( 6 , "PRICEPERTRIP" , "length" , "Price/\n%s" , "%.2f" , True , "number" ) ,
    ( 7 , "PRICEPERLITRE" , "volume" , "Price/\n%s" , "%.2f" , True , "number" ) ,
    ( 8 , "SERVICE" , "Service" , None , "%.2f" , True , "number" ) ,
    ( 9 , "OIL" , "Oil" , None , "%.2f" , True , "number" ) ,
    ( 10 , "TIRES" , "Tires" , None , "%.2f" , True , "number" ) ,
    ( 11 , "CO2EMISSION" , "mass" , None , "%.0f" , True , False ) ,
    ( 12 , "NOTES" , "Notes" , None , "%s" , True , "string" ) ,
    ( 13 , "ID" , "Id" , None , None , False , False ) ,
    ( 14 , "VISIBLE" , "Visible" , None , None , False , False )
    )
column_dict = {}
for item in column_info :
    column_dict[ item[1] ] = item[0]


class WizardItems ( list ) :

    def __init__( self , wizardcols=0 ) :

        list.__init__( self , ( "Fill" , "Price" , "Trip", "Total" ) )
        self.__keys = ( COL_FILL , COL_PRICE , COL_TRIP , COL_KM )
        self.wizardcol = wizardcols or ( 1<<COL_KM | 1<<COL_TRIP | 1<<COL_FILL )

    def set( self , i ) :
        self.wizardcol += 1 << self.__keys[i]

    def unset( self , i ) :
        self.wizardcol -= 1 << self.__keys[i]

    def is_on ( self , i ) :
        return self.wizardcol & ( 1 << self.__keys[i] )

class FuelpadConfig :

    def __init__ ( self , read=False ) :

        # global variables from fuelpad.c
        self.debug_level = None
        self.db = db.database( default_db )
        self.result_db = None

        self.reducedinput = True

        self.changed = False

        # global variables from ui.c
        self.fontsize = MEDIUM
        self.stbstattime = OVERALL

        self.units = unitsystem.index('SI')

        if read :
            self.read()

    def read ( self ) :

        client = gconf.client_get_default()

        self.db.currentcar = client.get_int( "/apps/fuelpad/current_car" )
        self.db.currentdriver = client.get_int( "/apps/fuelpad/current_driver" )
        self.units = client.get_int( "/apps/fuelpad/current_unit" )

        self.dateformat = client.get_int( "/apps/fuelpad/date_format" )
        tmpcurrency = client.get_string( "/apps/fuelpad/currency" )
        tmpdatabase = client.get_string( "/apps/fuelpad/database" )
        self.dispcol = client.get_int( "/apps/fuelpad/dispcol" )
        self.fontsize = client.get_int( "/apps/fuelpad/mainviewfontsize" )
        self.main_toolbar_visible = not client.get_bool( "/apps/fuelpad/maintoolbar_visible" )
        self.secondary_toolbar_visible = not client.get_bool( "/apps/fuelpad/secondarytoolbar_visible" )

        value = client.get_without_default( "/apps/fuelpad/reducedinput" )
        if value is not None :
            self.reducedinput = value.get_bool()

        self.wizarditems = WizardItems( client.get_int( "/apps/fuelpad/wizardcol" ) )

        self.use_gps = client.get_bool( "/apps/fuelpad/gps" )
        self.gps_timeout = client.get_int( "/apps/fuelpad/gps_timeout" )

        self.maintablesortcol = 0
        self.maintablesortorder = 0

        if not tmpcurrency :
            self.currency = "Eur" # localeconv()->int_curr_symbol
        else :
            self.currency = tmpcurrency

        if tmpdatabase :
            self.db.setfilename( tmpdatabase )

        # Current car and driver are zero if this is the first time
        # this program is run
        if self.db.currentcar == 0 : self.db.currentcar = 1
        if self.db.currentdriver == 0 :  self.db.currentdriver = 1
        if self.units not in unitrange :
            self.units = unitsystem.index('SI')
        if self.dateformat < 0 or self.dateformat > len(datefmtstr) :
            self.dateformat = 0

        # Reset shown columns to default value
        if self.dispcol == 0 :
            self.dispcol = DISPCOLDEFAULT

        # Reset fontsize to MEDIUM
        if self.fontsize < XSMALL or self.fontsize > LARGE :
            self.fontsize = MEDIUM

    def save ( self ) :

        client = gconf.client_get_default()

        client.set_int( "/apps/fuelpad/current_car" , self.db.currentcar )
        client.set_int( "/apps/fuelpad/current_driver" , self.db.currentdriver )
        client.set_int( "/apps/fuelpad/current_unit" , self.units )
        client.set_int( "/apps/fuelpad/date_format" , self.dateformat )
        client.set_string( "/apps/fuelpad/currency" , self.currency )
        client.set_string( "/apps/fuelpad/database" , self.db.result_db )
        client.set_int( "/apps/fuelpad/dispcol" , self.dispcol )
        client.set_int( "/apps/fuelpad/mainviewfontsize" , self.fontsize )
        client.set_bool( "/apps/fuelpad/maintoolbar_visible" , not self.main_toolbar_visible )
        client.set_bool( "/apps/fuelpad/secondarytoolbar_visible" , not self.secondary_toolbar_visible )

        client.set_bool( "/apps/fuelpad/reducedinput" , self.reducedinput )
        client.set_int( "/apps/fuelpad/wizardcol" , self.wizarditems.wizardcol )

        client.set_bool( "/apps/fuelpad/gps" , self.use_gps )
        client.set_int( "/apps/fuelpad/gps_timeout" , self.gps_timeout )


    def unit_label ( self , unittype ) :
        if unitnames.has_key( unittype ) :
            return unitnames[ unittype ][ self.units ]
        else :
            return unittype

    # Unit conversion functions
    # Conversions are likely ported, but maybe there are missing items

    # lcf = length conversion factor
    # vcf = volume conversion factor
    # mcf = mass conversion factor
    lcf = ( 1.0 , 1.609344 , 1.609344 )
    vcf = ( 1.0 , 3.785411784 , 4.54609 )
    mcf = ( 1.0 , 453.59237 , 453.59237 )

    def SIlength2user ( self , length ) :
        return length / self.lcf[self.units]

    def user2SIlength ( self , length ) :
        return length * self.lcf[self.units]

    def SIvolume2user ( self , length ) :
        return length / self.vcf[self.units]

    def user2SIvolume ( self , length ) :
        return length * self.vcf[self.units];

    def SIconsumption2user ( self , consum ) :
        if consum == 0 or self.units == unitsystem.index('SI') :
           return consum
        else :
           return self.vcf[self.units] / self.lcf[self.units] * 100 / consum

    def SIppl2user ( self , ppl ) :
        return self.user2SIvolume( ppl )

    def SIemission2user ( self , emission ) :
        if self.units == unitsystem.index('SI') :
            return self.SImass2user(emission)*self.lcf[self.units]
        else :
            return self.SImass2user(emission)*self.lcf[self.units]*100

    def SImass2user ( self , mass ) :
        return mass/self.mcf[self.units]


