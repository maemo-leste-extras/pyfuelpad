
import configuration , utils
import combos

import gtk
try :
    import hildon
except :
    hildon = False


def callback_tripadded ( widget , event , pui , config ) :
  newkm = float( pui.entrykm.get_text() or "0" )
  if newkm < 0.1 :
    trip = config.user2SIlength( float( pui.entrytrip.get_text() or "0" ) )
    lastkm = config.db.last_refill(newkm)
    if lastkm < 0.1 :
      lastkm = config.db.last_km()
      # BUGFIX : happens when database is brand new
      if lastkm == 0.0 :
        return False
    if widget :
      buf = "%.1f" % config.SIlength2user( lastkm + trip )
    else :
      buf = "%d" % config.SIlength2user( lastkm + trip )
    pui.entrykm.set_text( buf )
  return False

def callback_kmadded ( widget , event , pui , config ) :
  trip = float( pui.entrytrip.get_text() or "0" )
  newkm = config.user2SIlength( float( pui.entrykm.get_text() or "0" ) )
  if trip < 0.1 and newkm > 0 :
    lastkm = config.db.last_refill(newkm)
    if lastkm < 0.1 :
      lastkm = config.db.last_km()
      # BUGFIX : happens when database is brand new
      if lastkm == 0.0 :
        return False
    buf = "%.1f" % config.SIlength2user( newkm - lastkm )
    pui.entrytrip.set_text( buf )
  return False


#DIALOG_MIN_HEIGHT0 = 300
DIALOG_MIN_HEIGHT1 = 200
#DIALOG_MIN_HEIGHT2 = 150
#DIALOG_MIN_HEIGHTMAX = 400
#DIALOG_MIN_WIDTH1 = 720

# Add record dialog
ENTRYDATEMAX = 20
ENTRYKMMAX = 8
ENTRYTRIPMAX = 8
ENTRYFILLMAX = 8
ENTRYPRICEMAX = 8
ENTRYNOTESMAX = 50
ENTRYSERVICEMAX = 8
ENTRYOILMAX = 8
ENTRYTIRESMAX = 8


class KeypadAbstractButton :

        def __init__ ( self , text_label ) :
            label = gtk.Label( text_label )
            attrs = configuration.font_attrs( -2 )
            label.set_attributes( attrs )
            self.add( label )

if hildon :

    class KeypadButton ( hildon.Button , KeypadAbstractButton ) :

        def __init__ ( self , text_label ) :
            hildon.Button.__init__( self , gtk.HILDON_SIZE_THUMB_HEIGHT , hildon.BUTTON_ARRANGEMENT_VERTICAL )
            KeypadAbstractButton.__init__( self , text_label )

else :

    class KeypadButton ( gtk.Button , KeypadAbstractButton ) :

        def __init__ ( self , text_label ) :
            gtk.Button.__init__( self )
            KeypadAbstractButton.__init__( self , text_label )


class ButtonPad ( gtk.Table ) :

    # FIXME : while label is empty, backspace button must be disabled

    def __init__ ( self , decimals=False ) :

        gtk.Table.__init__( self , 4 , 4 , True )

        # Label for written values
        x , y = 0 , 0
        # FIXME : is self.label already allocated ???
        self.label = gtk.Label()
        attrs = configuration.font_attrs( -1 )
        self.label.set_attributes( attrs )
        self.attach( self.label , x , x+4 , y , y+1 )
        self.label.show()

        # Button for decimal dot
        if decimals :
            self.decimals = decimals
            x , y = 3 , 2
            button = KeypadButton( "." )
            button.connect("clicked", self.verified_write, ".")
            self.attach( button , x , x+1 , y , y+1 )
            button.show()

        # Button for 0
        x , y = 3 , 3
        button = KeypadButton( "%s" % 0 )
        button.connect("clicked", self.write, 0)
        self.attach( button , x , x+1 , y , y+1 )
        button.show()

        for i in range(9) :
            button = KeypadButton( "%s" % (i+1) )
            button.connect("clicked", self.write, i+1)
            self.attach( button , i%3 , i%3+1 , int(i/3)+1 , int(i/3)+2 )
            button.show()

        x , y = 3 , 1
        button = KeypadButton( "<-" )
        button.connect("clicked", self.backspace, None)
        self.attach( button , x , x+1 , y , y+1 )
        button.show()

    def verified_write(self, widget, data=None):
        self.write( widget , data )

    def write(self, widget, data=None):
        txt = self.label.get_text()
        self.label.set_text( "%s%s" % ( txt , data ) )

    def backspace ( self , widget , data=None ) :
        txt = self.label.get_text()
        if txt :
            self.label.set_text( txt[:-1] )

    def get_text ( self ) :
        return self.label.get_text()

    def set_text ( self , value ) :
        return self.label.set_text( value )


class FuelpadEdit ( gtk.Notebook ) :

    def __init__( self , config , add ) :
        gtk.Notebook.__init__( self )

        self.entryfill = ButtonPad( True )
        self.entrytrip = ButtonPad( True )
        self.entrykm = ButtonPad()
        self.append_page( self.entryfill , gtk.Label( "Fill" ) )
        self.append_page( self.entrytrip , gtk.Label( "Trip" ) )
        self.append_page( self.entrykm , gtk.Label( "Total KM" ) )

        # FIXME : focus actually never enters nor leave the entries
        if add :
            self.entrytrip.connect( "focus-out-event", callback_tripadded , self , config )
            self.entrykm.connect( "focus-out-event", callback_kmadded , self , config )

        # Not shown widgets
        self.entrydate = gtk.Entry()
        self.entrydate.set_text( utils.gettimefmt( config.dateformat ) )
        self.buttonnotfull = gtk.CheckButton()

        # To avoid confusion with FuelpadFullEdit
        self.entryprice = False

        # Set a handler for "switch-page" signal
        self.connect_object( "switch-page" , self.on_page_switch , config )

    def on_page_switch( self , config , page , num ) :
        print "switching",self,config,page,num
        if self.get_current_page() == 1 :
            callback_tripadded( None , None , self , config )
        elif self.get_current_page() == 2 :
            callback_kmadded( None , None , self , config )
        return True

# Ported the GTK part
class FuelpadFullEdit ( gtk.Notebook ) :

    labels = { 'EDIT_DATE':"Date",
               'EDIT_KM':"Km",
               'EDIT_MILES':"Miles",
               'EDIT_TRIP':"Trip",
               'EDIT_FILL':"Fill",
               'EDIT_NOTFULL':"Not full tank",
               'EDIT_PRICE':"Price",
               'EDIT_NOTES':"Notes",
               'EDIT_SERVICE':"Service",
               'EDIT_OIL':"Oil",
               'EDIT_TIRES':"Tires",
               'EDIT_CAR':"Car",
               'EDIT_DRIVER':"Driver"}

    def __init__( self , config , add ) :
        gtk.Notebook.__init__( self )
        self.set_tab_pos(gtk.POS_TOP)

        scrollwin = gtk.ScrolledWindow(None, None)
        scrollwin.set_size_request(-1, DIALOG_MIN_HEIGHT1)
        scrollwin.set_policy(gtk.POLICY_NEVER,
                             gtk.POLICY_AUTOMATIC)

        table = gtk.Table(4, 4, False)
        scrollwin.add_with_viewport( table )

        # First row, first entry
        label = gtk.Label( self.labels['EDIT_DATE'] ) 
        table.attach(label, 0, 1, 0, 1, 
                     gtk.EXPAND|gtk.FILL,
                     0, 0, 5)
        label.show()

        self.entrydate = gtk.Entry()
        self.entrydate.set_max_length(ENTRYDATEMAX)
        self.entrydate.set_text( utils.gettimefmt( config.dateformat ) )
#      pui.entrydate = hildon.DateEditor()
        table.attach( self.entrydate, 1, 2, 0, 1, 
                     gtk.EXPAND|gtk.FILL,
                     0, 0, 5)
        self.entrydate.show()
  
        # First row, second entry
        if config.isSI( 'length' ) :
          label = gtk.Label( self.labels['EDIT_KM'] )
        else :
          label = gtk.Label( self.labels['EDIT_MILES'] )
        table.attach(label, 2, 3, 0, 1, 
                     gtk.EXPAND|gtk.FILL,
                     0, 0, 5)
        label.show()

        self.entrykm = gtk.Entry()
        self.entrykm.set_max_length( ENTRYKMMAX )
#  if hildon :
#    if maemo5 :
#      pui.entrykm.set( "hildon-input-mode",
#		 HILDON_GTK_INPUT_MODE_NUMERIC|HILDON_GTK_INPUT_MODE_SPECIAL,
#		 None)
#    else:
#      pui.entrykm.set( "input-mode", hildon.INPUT_MODE_HINT_NUMERICSPECIAL, None)
#      pui.entrykm.set( "autocap", False, None)
        if add :
          self.entrykm.connect( "focus-out-event", callback_kmadded , self , config )

        table.attach( self.entrykm, 3, 4, 0, 1, 
                      gtk.EXPAND|gtk.FILL,
                      0, 0, 5)
        self.entrykm.show()

        # Second row, first entry
        label = gtk.Label( self.labels['EDIT_TRIP'] )
        table.attach(label, 0, 1, 1, 2,
                     gtk.EXPAND|gtk.FILL,
                     0, 0, 5)
        label.show()

        self.entrytrip = gtk.Entry()
        self.entrytrip.set_max_length( ENTRYTRIPMAX )
#  if hildon :
#    if maemo5 :
#      g_object_set(G_OBJECT(pui->entrytrip),
#              "hildon-input-mode",
#               HILDON_GTK_INPUT_MODE_NUMERIC|HILDON_GTK_INPUT_MODE_SPECIAL,
#               NULL);
#    else :
#      g_object_set(G_OBJECT(pui->entrytrip),
#               "input-mode", HILDON_INPUT_MODE_HINT_NUMERICSPECIAL, NULL);
#    g_object_set(G_OBJECT(pui->entrytrip), "autocap", FALSE, NULL);
        if add :
          self.entrytrip.connect( "focus-out-event", callback_tripadded , self , config )

        table.attach( self.entrytrip, 1, 2, 1, 2,
                   gtk.EXPAND|gtk.FILL,
                   0, 0, 5)
        self.entrytrip.show()

        # Second row, second entry
        label = gtk.Label( self.labels['EDIT_FILL'] )
        table.attach( label, 2, 3, 1, 2,
                   gtk.EXPAND|gtk.FILL,
                   0, 0, 5)
        label.show()

        self.entryfill = gtk.Entry()
        self.entryfill.set_max_length( ENTRYFILLMAX )
        table.attach( self.entryfill, 3, 4, 1, 2,
                   gtk.EXPAND|gtk.FILL,
                   0, 0, 5)
        self.entryfill.show()

        # Not full button
        self.buttonnotfull = gtk.CheckButton( label=self.labels['EDIT_NOTFULL'] )
        table.attach( self.buttonnotfull, 3, 4, 2, 3,
                   gtk.EXPAND|gtk.FILL,
                   0, 0, 5)
        self.buttonnotfull.show()

        # Third row, first entry
        label = gtk.Label( self.labels['EDIT_PRICE'] )
        table.attach( label, 0, 1, 3, 4,
                   gtk.EXPAND|gtk.FILL,
                   0, 0, 5)
        label.show()

        self.entryprice = gtk.Entry()
        self.entryprice.set_max_length( ENTRYPRICEMAX )
        table.attach( self.entryprice, 1, 2, 3, 4,
                   gtk.EXPAND|gtk.FILL,
                   0, 0, 5)
        self.entryprice.show()

        # Third row, second entry
        label = gtk.Label( self.labels['EDIT_NOTES'] )
        table.attach( label, 2, 3, 3, 4,
                   gtk.EXPAND|gtk.FILL,
                   0, 0, 5)
        label.show()

        self.entrynotes = gtk.Entry()
        self.entrynotes.set_max_length( ENTRYNOTESMAX )
        table.attach( self.entrynotes, 3, 4, 3, 4,
                   gtk.EXPAND|gtk.FILL,
                   0, 0, 5);
        self.entrynotes.show()

#        completion = gtk.EntryCompletion()
#        store = pui.view.get_model()
#        completion.set_model( store )
#        completion.set_text_column( configuration.column_dict['NOTES'] )
#        self.entrynotes.set_completion( completion )

        # Table ready - show it
        table.show()
        scrollwin.show()

        label = gtk.Label( "Fuel fill" )
        self.append_page( scrollwin, label )

        # Service etc. self
        table = gtk.Table(1, 3, False)

        # First row, first entry
        label = gtk.Label( self.labels['EDIT_SERVICE'] )
        table.attach( label, 0, 1, 0, 1,
                   gtk.EXPAND|gtk.FILL,
                   0, 0, 5)
        label.show()

        self.entryservice = gtk.Entry()
        self.entryservice.set_max_length( ENTRYSERVICEMAX )
        table.attach( self.entryservice, 1, 2, 0, 1,
                   gtk.EXPAND|gtk.FILL,
                   0, 0, 5)
        self.entryservice.show()

        # Second row, first entry
        label = gtk.Label( self.labels['EDIT_OIL'] )
        table.attach( label, 0, 1, 1, 2,
                   gtk.EXPAND|gtk.FILL,
                   0, 0, 5)
        label.show()

        self.entryoil = gtk.Entry()
        self.entryoil.set_max_length( ENTRYOILMAX )
        table.attach( self.entryoil, 1, 2, 1, 2,
                   gtk.EXPAND|gtk.FILL,
                   0, 0, 5)
        self.entryoil.show()

        # Third row, first entry
        label = gtk.Label( self.labels['EDIT_TIRES'] )
        table.attach( label, 0, 1, 2, 3,
                   gtk.EXPAND|gtk.FILL,
                   0, 0, 5)
        label.show()

        self.entrytires = gtk.Entry()
        self.entrytires.set_max_length( ENTRYTIRESMAX )
        table.attach( self.entrytires, 1, 2, 2, 3,
                   gtk.EXPAND|gtk.FILL,
                   0, 0, 5)
        self.entrytires.show()

        # Table ready - show it
        table.show()

        label = gtk.Label ( "Service/oil/tires" )
        self.append_page( table, label)

        if add :
          table = gtk.Table(2, 2, False)

          # First row, first entry 
          label = gtk.Label( self.labels['EDIT_CAR'] )
          table.attach(label, 0, 1, 0, 1, 
                 gtk.EXPAND|gtk.FILL,
                 0, 0, 5);
          label.show()

          self.carcombo = combos.FuelpadCarCombo( config )
          table.attach(self.carcombo, 1, 2, 0, 1, 
                 gtk.EXPAND|gtk.FILL,
                 0, 0, 5)
          self.carcombo.show()

          # First row, second entry
          label = gtk.Label( self.labels['EDIT_DRIVER'] )
          table.attach( label, 0, 1, 1, 2, 
                 gtk.EXPAND|gtk.FILL,
                 0, 0, 5);
          label.show()
    
          self.drivercombo = combos.FuelpadDriverCombo( config )
          table.attach( self.drivercombo, 1, 2, 1, 2, 
                  gtk.EXPAND|gtk.FILL,
                  0, 0, 5)
          self.drivercombo.show()

          table.show()

          label = gtk.Label( "Driver and car" )
          self.append_page( table , label )

