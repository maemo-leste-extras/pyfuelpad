
import configuration

import time

default_format = "%Y-%m-%d"

def convdate ( outformat , informat, date ) :
    if outformat :
        _outformat = configuration.datefmtstr[outformat]
    else :
        _outformat = default_format
    if informat :
        _informat = configuration.datefmtstr[informat]
    else :
        _informat = default_format
    _date = time.strptime( date , _informat )
    return time.strftime( _outformat , _date )

def date2sqlite ( format, date ) :
    return convdate( None , format , date )

def getdatestruct ( record_date ) :
    return time.strptime( record_date , default_format )

def gettimefmt ( format , record_date=None ) :
    if record_date :
        return time.strftime( configuration.datefmtstr[format] , getdatestruct( record_date ) )
    return time.strftime( configuration.datefmtstr[format] , time.localtime() )


def calc_co2_emission ( consum , fueltype ) :

    if fueltype < 0 :
        fueltype=0
    elif fueltype > 1 :
        fueltype=1

    if consum > 1e-5 :
        return get_emission_per_litre(fueltype)*consum/100.0

    return 0.0

emissionperlitre = ( 2350.0 , 2660.0 )
def get_emission_per_litre ( fueltype ) :
    return emissionperlitre[ int(fueltype) ]

def doubleornothing ( input ) :
    try :
        return float( input )
    except ValueError , ex :
        return 0.0

