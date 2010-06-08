
import configuration , utils
import combos

import gtk
try :
    import hildon
except :
    hildon = False


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


def callback_tripadded ( widget , event , editwin , config ) :
    newkm = float( editwin.entrykm.get_text() or "0" )
    if newkm < 0.1 :
        trip = config.user2SIlength( float( editwin.entrytrip.get_text() or "0" ) )
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
        editwin.entrykm.set_text( buf )
    return False

def callback_kmadded ( widget , event , editwin , config ) :
    trip = float( editwin.entrytrip.get_text() or "0" )
    newkm = config.user2SIlength( float( editwin.entrykm.get_text() or "0" ) )
    if trip < 0.1 and newkm > 0 :
        lastkm = config.db.last_refill(newkm)
        if lastkm < 0.1 :
            lastkm = config.db.last_km()
            # BUGFIX : happens when database is brand new
            if lastkm == 0.0 :
                return False
        buf = "%.1f" % config.SIlength2user( newkm - lastkm )
        editwin.entrytrip.set_text( buf )
    return False


class FuelpadEdit ( gtk.Notebook ) :

    def __init__( self , config , add ) :
        gtk.Notebook.__init__( self )

        self.entryfill = ButtonPad( True )
        self.entrytrip = ButtonPad( True )
        self.entrykm = ButtonPad()
        self.append_page( self.entryfill , gtk.Label( "Fill" ) )
        self.append_page( self.entrytrip , gtk.Label( "Trip" ) )
        self.append_page( self.entrykm , gtk.Label( "Total KM" ) )

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

class FuelpadAbstractFullEdit :

    labels = { 'EDIT_DATE':( "Date", 20 ) ,
               'EDIT_KM':( "Km", 8 ) ,
               'EDIT_MILES':( "Miles", 8 ) ,
               'EDIT_TRIP':( "Trip", 8 ) ,
               'EDIT_FILL':( "Fill", 8 ) ,
               'EDIT_NOTFULL':( "Not full tank", None ) ,
               'EDIT_PRICE':( "Price", 8 ) ,
               'EDIT_NOTES':( "Notes", 50 ) ,
               'EDIT_SERVICE':( "Service", 8 ) ,
               'EDIT_OIL':( "Oil", 8 ) ,
               'EDIT_TIRES':( "Tires", 8 ) ,
               'EDIT_CAR':( "Car", None ) ,
               'EDIT_DRIVER':( "Driver", None )
               }

    #DIALOG_MIN_HEIGHT0 = 300
    DIALOG_MIN_HEIGHT1 = 200
    #DIALOG_MIN_HEIGHT2 = 150
    DIALOG_MIN_HEIGHTMAX = 400
    #DIALOG_MIN_WIDTH1 = 720

    def add_label ( self , table , id , item , row , column=0 ) :
        label = gtk.Label( self.labels[id][0] )
        table.attach(label, column, column+1, row, row+1,
                     gtk.EXPAND|gtk.FILL,
                     0, 0, 5)
        label.show()
        table.attach(item, column+1, column+2, row, row+1,
                     gtk.EXPAND|gtk.FILL,
                     0, 0, 5)
        item.show()

if hildon :

    class FuelpadFullEdit ( hildon.PannableArea , FuelpadAbstractFullEdit ) :

        def __init__( self , config , add ) :
            hildon.PannableArea.__init__( self )
            self.set_size_request( -1 , self.DIALOG_MIN_HEIGHTMAX )

            if add :
                table = gtk.Table(12, 2, False)
            else :
                table = gtk.Table(10, 2, False)

            row = 0

            if add :

                self.carcombo = combos.FuelpadCarCombo( config )
                self.add_button( table , self.carcombo , row )
                row += 1

                self.drivercombo = combos.FuelpadDriverCombo( config )
                self.add_button( table , self.drivercombo , row )
                row += 1

            # First row, first entry
            self.entrydate = hildon.DateButton( gtk.HILDON_SIZE_FINGER_HEIGHT , hildon.BUTTON_ARRANGEMENT_VERTICAL )
            self.add_button( table , self.entrydate , row )
            row += 1

            # First row, second entry
            if config.isSI( 'length' ) :
              self.entrykm = self.add_item( table , 'EDIT_KM' , row )
            else :
              self.entrykm = self.add_item( table , 'EDIT_MILES' , row )
            row += 1

            if add :
              self.entrykm.connect( "focus-out-event", callback_kmadded , self , config )

            # Second row, first entry
            self.entrytrip = self.add_item( table , 'EDIT_TRIP' , row )
            row += 1

            if add :
              self.entrytrip.connect( "focus-out-event", callback_tripadded , self , config )

            # Second row, second entry
            self.entryfill = self.add_item( table , 'EDIT_FILL' , row )
            row += 1

            # Not full button
            self.buttonnotfull = hildon.CheckButton( gtk.HILDON_SIZE_FINGER_HEIGHT )
            self.buttonnotfull.set_label( self.labels['EDIT_NOTFULL'][0] )
            table.attach( self.buttonnotfull, 1, 2, row, row+1,
                       gtk.EXPAND|gtk.FILL,
                       0, 0, 5)
            self.buttonnotfull.show()
            row += 1

            # Third row, first entry
            self.entryprice = self.add_item( table , 'EDIT_PRICE' , row )
            row += 1

            # Third row, second entry
            self.entrynotes = self.add_item( table , 'EDIT_NOTES' , row )
            row += 1

    #        completion = gtk.EntryCompletion()
    #        store = pui.view.get_model()
    #        completion.set_model( store )
    #        completion.set_text_column( configuration.column_dict['NOTES'] )
    #        self.entrynotes.set_completion( completion )

            # First row, first entry
            self.entryservice = self.add_item( table , 'EDIT_SERVICE' , row )
            row += 1

            # Second row, first entry
            self.entryoil = self.add_item( table , 'EDIT_OIL' , row )
            row += 1

            # Third row, first entry
            self.entrytires = self.add_item( table , 'EDIT_TIRES' , row )
            row += 1

            self.add_with_viewport( table )

        def add_item ( self , table , id , row , column=0 ) :
            item = hildon.Entry( gtk.HILDON_SIZE_FINGER_HEIGHT )
            item.set_max_length( self.labels[id][1] )
            item.set_input_mode( gtk.HILDON_GTK_INPUT_MODE_NUMERIC|gtk.HILDON_GTK_INPUT_MODE_SPECIAL )
        #    item.set_property( "autocap", False)
            self.add_label( table , id , item ,row , column )
            return item

        def add_button ( self , table , item , row ) :
            table.attach(item, 0, 2, row, row+1,
                         gtk.EXPAND|gtk.FILL,
                         0, 0, 5)
            item.show()
else :

    class FuelpadFullEdit ( gtk.Notebook , FuelpadAbstractFullEdit ) :

        def __init__( self , config , add ) :
            gtk.Notebook.__init__( self )
            self.set_tab_pos(gtk.POS_TOP)

            scrollwin = gtk.ScrolledWindow(None, None)
            scrollwin.set_size_request(-1, self.DIALOG_MIN_HEIGHT1)
            scrollwin.set_policy(gtk.POLICY_NEVER,
                                 gtk.POLICY_AUTOMATIC)

            table = gtk.Table(4, 4, False)
            scrollwin.add_with_viewport( table )

            # First row, first entry
            self.entrydate = self.add_item( table , 'EDIT_DATE' , 0 )
            self.entrydate.set_text( utils.gettimefmt( config.dateformat ) )

            # First row, second entry
            if config.isSI( 'length' ) :
              self.entrykm = self.add_item( table , 'EDIT_KM' , 0 , 2 )
            else :
              self.entrykm = self.add_item( table , 'EDIT_MILES' , 0 , 2 )

            if add :
              self.entrykm.connect( "focus-out-event", callback_kmadded , self , config )

            # Second row, first entry
            self.entrytrip = self.add_item( table , 'EDIT_TRIP' , 1 )

            if add :
              self.entrytrip.connect( "focus-out-event", callback_tripadded , self , config )

            # Second row, second entry
            self.entryfill = self.add_item( table , 'EDIT_FILL' , 2 )

            # Not full button
            self.buttonnotfull = gtk.CheckButton( label=self.labels['EDIT_NOTFULL'][0] )
            table.attach( self.buttonnotfull, 3, 4, 2, 3,
                       gtk.EXPAND|gtk.FILL,
                       0, 0, 5)
            self.buttonnotfull.show()

            # Third row, first entry
            self.entryprice = self.add_item( table , 'EDIT_PRICE' , 3 )

            # Third row, second entry
            self.entrynotes = self.add_item( table , 'EDIT_NOTES' , 2 )

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
            self.entryservice = self.add_item( table , 'EDIT_SERVICE' , 0 )

            # Second row, first entry
            self.entryoil = self.add_item( table , 'EDIT_OIL' , 1 )

            # Third row, first entry
            self.entrytires = self.add_item( table , 'EDIT_TIRES' , 2)

            # Table ready - show it
            table.show()

            label = gtk.Label ( "Service/oil/tires" )
            self.append_page( table, label)

            if add :
              table = gtk.Table(2, 2, False)

              # First row, first entry 
              self.carcombo = combos.FuelpadCarCombo( config )
              self.add_label( table , 'EDIT_CAR' , self.carcombo , 0 )

              # First row, second entry
              self.drivercombo = combos.FuelpadDriverCombo( config )
              self.add_label( table , 'EDIT_DRIVER' , self.drivercombo , 1 )

              table.show()

              label = gtk.Label( "Driver and car" )
              self.append_page( table , label )

        def add_item ( self , table , id , row , column=0 ) :
            item = gtk.Entry()
            item.set_max_length( self.labels[id][1] )
            self.add_label( table , id , item ,row , column )
            return item

