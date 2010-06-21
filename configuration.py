
import db

import gconf

import gtk

default_db = "/home/user/fuelpad.db"

# fontscale
XSMALL=1
SMALL=2
MEDIUM=3
LARGE=4

fontsizes = [ 'Preconfigured' , 'XSMALL' , 'SMALL' , 'MEDIUM' , 'LARGE' ]

# DB format is hardcoded to "%Y-%m-%d"
# Possible date format strings (see strptime(3) for format descri ption) 
datefmtstr = ("%Y-%m-%d", "%d.%m.%Y", "%d/%m/%Y", "%d/%m/%y",
                    "%d-%m-%Y", "%m/%d/%Y", "%m/%d/%y")


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

# unit
SI=0
US=1
IMPERIAL=2

unitsystem = [ 'SI' , 'US' , 'IMPERIAL' ]

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

WIZARDCOLS = 1<<COL_KM | 1<<COL_TRIP | 1<<COL_FILL

#COLUMN STRUCT  : number , header , non_SI_header , formatvals(None) ,  hidden
# number , name , header , unittype , non_SI_header , format ,  showable , comparison
column_info = (
    ( 0 , "DAY" , "Date" , False , None , "%s" , True , "date" ) , # JP Format is yet to be defined and implemented
    ( 1 , "KM" , "Km" , "length" , "Miles" , "%.0f" , True , "number" ) ,
    ( 2 , "TRIP" , "Trip\n[km]" , "length" , "Trip\n[miles]" , "%.1f" , True , "number" ) ,
    ( 3 , "FILL" , "Fill\n[litre]" , "volume" , "Fill\n[gal.]" , "%.2f" , True , "number" ) ,
    ( 4 , "CONSUM" , "[litre/\n100 km]" , "consume", "[Miles/\ngallon]" , "%.1f" , True , "number" ) ,
    ( 5 , "PRICE" , "Price" , False , None , "%.2f" , True , "number" ) ,
    ( 6 , "PRICEPERTRIP" , "Price/\nkm" , "length" , "Price/\nmile" , "%.2f" , True , "number" ) ,
    ( 7 , "PRICEPERLITRE" , "Price/\nlitre" , "volume" , "Price/\ngal." , "%.2f" , True , "number" ) ,
    ( 8 , "SERVICE" , "Service" , False , None , "%.2f" , True , "number" ) ,
    ( 9 , "OIL" , "Oil" , False , None , "%.2f" , True , "number" ) ,
    ( 10 , "TIRES" , "Tires" , False , None , "%.2f" , True , "number" ) ,
    ( 11 , "CO2EMISSION" , "CO2 Emissions\n[g/km]" , "mass", "CO2 Emissions\n[lb/100 miles]" , "%.0f" , True , False ) ,
    ( 12 , "NOTES" , "Notes" , False , None , "%s" , True , "string" ) ,
    ( 13 , "ID" , "Id" , False , None , None , False , False ) ,
    ( 14 , "VISIBLE" , "Visible" , False , None , None , False , False )
    )
column_dict = {}
for item in column_info :
    column_dict[ item[1] ] = item[0]


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

        self.units = {}

        if read :
            self.read()

    def read ( self ) :

        client = gconf.client_get_default()

        self.db.currentcar = client.get_int( "/apps/fuelpad/current_car" )
        self.db.currentdriver = client.get_int( "/apps/fuelpad/current_driver" )
        self.units['main'] = client.get_int( "/apps/fuelpad/current_unit" )
        self.units['length'] = client.get_int( "/apps/fuelpad/current_lengthunit" )
        self.units['volume'] = client.get_int( "/apps/fuelpad/current_volumeunit" )
        self.units['consume'] = client.get_int( "/apps/fuelpad/current_consumeunit" )
        self.units['mass'] = client.get_int( "/apps/fuelpad/current_massunit" )

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

        self.wizardcol = client.get_int( "/apps/fuelpad/wizardpcol" )
        if self.wizardcol == 0 :
            self.wizardcol = WIZARDCOLS

        self.maintablesortcol = 0
        self.maintablesortorder = gtk.SORT_ASCENDING

        if not tmpcurrency :
            self.currency = "Pts" # localeconv()->int_curr_symbol
        else :
            self.currency = tmpcurrency

        if tmpdatabase :
            self.db.setfilename( tmpdatabase )

        # Current car and driver are zero if this is the first time
        # this program is run
        if self.db.currentcar == 0 : self.db.currentcar = 1
        if self.db.currentdriver == 0 :  self.db.currentdriver = 1
        if self.units['main'] > IMPERIAL or self.units['main'] < SI :
            self.units['main'] = SI
        if self.units['length'] > IMPERIAL or self.units['length'] < SI :
            self.units['length'] = SI
        if self.units['volume'] > IMPERIAL or self.units['volume'] < SI :
            self.units['volume'] = SI
        if self.units['consume'] > IMPERIAL or self.units['consume'] < SI :
            self.units['consume'] = SI
        if self.units['mass'] > IMPERIAL or self.units['mass'] < SI :
            self.units['mass'] = SI
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
        client.set_int( "/apps/fuelpad/current_unit" , self.units['main'] )
        client.set_int( "/apps/fuelpad/current_lengthunit" , self.units['length'] )
        client.set_int( "/apps/fuelpad/current_volumeunit" , self.units['volume'] )
        client.set_int( "/apps/fuelpad/current_consumeunit" , self.units['consume'] )
        client.set_int( "/apps/fuelpad/current_massunit" , self.units['mass'] )
        client.set_int( "/apps/fuelpad/date_format" , self.dateformat )
        client.set_string( "/apps/fuelpad/currency" , self.currency )
        client.set_string( "/apps/fuelpad/database" , self.db.result_db )
        client.set_int( "/apps/fuelpad/dispcol" , self.dispcol )
        client.set_int( "/apps/fuelpad/mainviewfontsize" , self.fontsize )
        client.set_bool( "/apps/fuelpad/maintoolbar_visible" , not self.main_toolbar_visible )
        client.set_bool( "/apps/fuelpad/secondarytoolbar_visible" , not self.secondary_toolbar_visible )

        client.set_bool( "/apps/fuelpad/reducedinput" , self.reducedinput )
        client.set_int( "/apps/fuelpad/wizardcol" , self.wizardcol )

    # To be revised
    def doubleornothing ( self , input ) :
      if not input :
        return 0.0
      return float( input )


    def isSI ( self , unittype  ) :
        return self.units[ unittype ] == SI

# Conversions are likely ported, but maybe there are missing items
    # Conversions are likely ported, but maybe there are missing items
    # Unit conversion functions

    # lcf = length conversion factor
    # vcf = volume conversion factor
    # mcf = mass conversion factor
    lcf = ( 1.0 , 1.609344 , 1.609344 )
    vcf = ( 1.0 , 3.785411784 , 4.54609 )
    mcf = ( 1.0 , 453.59237 , 453.59237 )

    def SIlength2user ( self , length ) :
        return self.doubleornothing(length) / self.lcf[self.units['length']]

    def user2SIlength ( self , length ) :
        return self.doubleornothing(length) * self.lcf[self.units['length']]

    def SIvolume2user ( self , length ) :
        return self.doubleornothing(length )/ self.vcf[self.units['volume']]

    def user2SIvolume ( self , length ) :
        return self.doubleornothing(length) * self.vcf[self.units['volume']];

    def SIconsumption2user ( self , consum ) :
        if self.isSI( 'consume' ) :
           return consum
        else :
           return self.vcf[self.units['consume']] / self.lcf[self.units['consume']] * 100.0 / consum

    def user2SIconsumption ( self , consum ) :
        raise Excception("Esto es rarito")
        return self.SIconsumption2user( consum )

    def SIppl2user ( self , ppl ) :
        return self.user2SIvolume( ppl )

    def SIemission2user ( self , emission ) :
        if self.isSI( 'mass' ) :
            return self.SImass2user(emission)*self.lcf[self.units['length']]
        else :
            return self.SImass2user(emission)*self.lcf[self.units['length']]*100

    def SImass2user ( self , mass ) :
        return mass/self.mcf[self.units['mass']]


