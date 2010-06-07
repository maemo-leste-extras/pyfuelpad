#!/usr/bin/python

# ToDo : Implement my own add_record , and show specific button plus fulltank toggler

import configuration , ui

import gtk
try :
    import hildon
#    maemo5 = True
except :
    hildon = None
#    maemo5 = None
# hildon stands for PLAINGTK == 0
# maemo5 stands for MAEMO_VERSION_MAJOR == 5

import sys


#recfilter = configuration.recordfilter_t()
#app = configuration.AppData()
#ui = configuration.AppUIData()


#def filter_update ( filt ) :
#  rc = config.db.get_single( "SELECT min(day) FROM record WHERE carid=%d" % config.db.currentcar )
#  rc = config.db.get_single( "SELECT max(day) FROM record WHERE carid=%d" % config.db.currentcar )
#  
#def filter_init ( filt ) :
#  filt.mindate = ""
#  filt.maxdate = ""
#  filt.notes = "*"
##  filt->pattern=g_pattern_spec_new(filt->notes->str);
#  filt.column = 0
#
#  filter_update(filt)
#
#  filt._and = False
#
#def filter_clear ( filt ) :
#  # Seems to only free memory
#  filt.mindate = None
#  filt.maxdate = None
#  filt.notes = None
##  g_pattern_spec_free(filt->pattern);


def main ( argv ) :

#  /* Initialize localization. */
#  setlocale(LC_ALL, "");
#  bindtextdomain(GETTEXT_PACKAGE, LOCALEDIR);
#  bind_textdomain_codeset(GETTEXT_PACKAGE, "UTF-8");
#  textdomain(GETTEXT_PACKAGE);

    # NOTE : Why not open db within the configuration reading ?
    # ui_init + db_connect
    config = configuration.FuelpadConfig( True )
    if hildon :
        config.main_toolbar_visible = False
        config.secondary_toolbar_visible = True
    config.db.open( config )
#  filter_init(recfilter)

    ui.FuelpadWindow( config )

    # ui_main_loop
    gtk.main()

#  filter_clear(recfilter)
    # fuelpad_exit
    config.db.close()
    config.save()

if __name__ == "__main__" :
  main( sys.argv )

