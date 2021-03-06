
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

    class Entry ( hildon.Entry ) :

        def __init__ ( self ) :
            hildon.Entry.__init__( self , gtk.HILDON_SIZE_FINGER_HEIGHT )

    class KeypadButton ( hildon.Button , KeypadAbstractButton ) :

        def __init__ ( self , text_label ) :
            hildon.Button.__init__( self , gtk.HILDON_SIZE_THUMB_HEIGHT , hildon.BUTTON_ARRANGEMENT_VERTICAL )
            KeypadAbstractButton.__init__( self , text_label )

    class CheckButton ( hildon.CheckButton ) :

        def __init__ ( self , label=None ) :
            hildon.CheckButton.__init__( self , gtk.HILDON_SIZE_FINGER_HEIGHT )
            if label :
                self.set_label( label )

    class DateEntry ( hildon.DateButton ) :

        def __init__ ( self , config , date=None ) :
            hildon.DateButton.__init__( self , gtk.HILDON_SIZE_FINGER_HEIGHT , hildon.BUTTON_ARRANGEMENT_VERTICAL )
            if date :
                datestruct = utils.getdatestruct( date )
                self.set_date( datestruct[0] , datestruct[1]-1 , datestruct[2] )

        def get_datestring ( self ) :
            year , month , day = self.get_date()
            return "%d-%02d-%02d" % ( year , month+1 , day )

else :

    Entry = gtk.Entry

    class KeypadButton ( gtk.Button , KeypadAbstractButton ) :

        def __init__ ( self , text_label ) :
            gtk.Button.__init__( self )
            KeypadAbstractButton.__init__( self , text_label )

    class CheckButton ( gtk.CheckButton ) :

        def __init__ ( self , label=None ) :
            gtk.CheckButton.__init__( self )
            if label :
                self.set_label( label )

    class DateEntry ( gtk.Entry ) :

        def __init__ ( self , config , date=None ) :
            gtk.Entry.__init__( self )
            self.set_text( utils.gettimefmt( config.dateformat , date ) )

        def get_datestring ( self ) :
            return self.get_text()


class FloatEntry ( Entry ) :

    def get_text ( self ) :
        return utils.doubleornothing( Entry.get_text( self ) )


class ButtonPad ( gtk.Table ) :

    # FIXME : while label is empty, backspace button must be disabled

    def __init__ ( self , title , decimals=False ) :

        gtk.Table.__init__( self , 4 , 4 , True )

        def label ( ) :
            item = gtk.Label()
            attrs = configuration.font_attrs( -1 )
            item.set_attributes( attrs )
            return item

        self.title = label()
        self.units = label()
        self.label = label()

        hbox = gtk.HBox()
        hbox.pack_start( self.title , expand=False, fill=False )
        hbox.pack_end( self.units , expand=False, fill=False )
        hbox.pack_end( self.label , expand=True, fill=True )
        self.attach( hbox , 0 , 4 , 0 , 1 )

        # Button for decimal dot
        if decimals :
            self.decimals = decimals
            button = KeypadButton( "." )
            button.connect("clicked", self.verified_write, ".")
            self.attach( button , 3 , 4 , 2 , 3 )

        # Button for 0
        button = KeypadButton( "%s" % 0 )
        button.connect("clicked", self.write, 0)
        self.attach( button , 3 , 4 , 3 , 4 )

        for i in range(9) :
            button = KeypadButton( "%s" % (i+1) )
            button.connect("clicked", self.write, i+1)
            self.attach( button , i%3 , i%3+1 , int(i/3)+1 , int(i/3)+2 )

        button = KeypadButton( "<-" )
        button.connect("clicked", self.backspace, None)
        self.attach( button , 3 , 4 , 1 , 2 )

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
        return utils.doubleornothing( self.label.get_text() )

    def set_text ( self , value ) :
        return self.label.set_text( value )


def tripadded ( widget , event , editwin , config ) :
    newkm = editwin.entrykm.get_text()
    if newkm < 0.1 :
        trip = editwin.entrytrip.get_text()
        lastkm = config.SIlength2user( config.db.last_km() )
        # BUGFIX : happens when database is brand new
        if lastkm == 0.0 :
            return False
        if widget :
            buf = "%.1f" % ( lastkm + trip )
        else :
            buf = "%d" % ( lastkm + trip )
        editwin.entrykm.set_text( buf )
    return False

def kmadded ( widget , event , editwin , config ) :
    trip = editwin.entrytrip.get_text()
    newkm = editwin.entrykm.get_text()
    if trip < 0.1 :
        lastkm = config.SIlength2user( config.db.last_km() )
	if lastkm == newkm :
            return False
    #    lastkm = config.SIlength2user( config.db.last_refill(newkm) )
        buf = "%.1f" % ( newkm - lastkm )
        editwin.entrytrip.set_text( buf )
    return False


class FuelpadEdit ( gtk.Notebook ) :

    def __init__( self , config , add ) :
        gtk.Notebook.__init__( self )
        self.set_size_request(450,260)

        self.entryprice = ButtonPad( "Price" , True )
        self.entryfill = ButtonPad( "Fill" , True )
        self.entrytrip = ButtonPad( "Trip" ,  True )
        self.entrykm = ButtonPad( "Total" )

        page = {}
        page["Price"] = self.entryprice
        page["Fill"] = self.entryfill
        page["Trip"] = self.entrytrip
        page["Total"] = self.entrykm
        for i in range( len(config.wizarditems) ) :
            if config.wizarditems.is_on( i ) :
                self.append_page( page[ config.wizarditems[i] ] , gtk.Label( config.wizarditems[i] ) )
                page[ config.wizarditems[i] ].title.set_text( config.wizarditems[i] )
            else :
                page[ config.wizarditems[i] ] = False
        if page["Price"] :
            page[ "Price" ].units.set_text( config.currency )
        if page["Fill"] :
            page[ "Fill" ].units.set_text( config.unit_label( 'volume' ) )
        if page["Trip"] :
            page[ "Trip" ].units.set_text( config.unit_label( 'length' ) )
        if page["Total"] :
            page[ "Total" ].units.set_text( config.unit_label( 'length' ) )

        # Not shown widgets
        self.entrydate = DateEntry( config )
        self.buttonnotfull = CheckButton()

        # To avoid confusion with FuelpadFullEdit
        self.entryservice = False

        # Set a handler for "switch-page" signal
        self.connect_object( "switch-page" , self.on_page_switch , config )

    def on_page_switch( self , config , page , num ) :
        if self.get_current_page() == 1 :
            tripadded( None , None , self , config )
        elif self.get_current_page() == 2 :
            kmadded( None , None , self , config )
        return True

class FuelpadAbstractEditwin :

    widgets = {}

    DIALOG_MIN_HEIGHT1 = 150
    DIALOG_MIN_HEIGHTMAX = 400

    def add_button ( self , table , item , row , col , end_col=False ) :
        end_col = end_col or col + 1
        table.attach(item, col, end_col, row, row+1,
                     gtk.EXPAND|gtk.FILL,
                     0, 0, 5)
        item.show()

    def add_label ( self , table , id , item , row , column=0 , end_col=False ) :
        label = self.get_label( id )
        self.add_button( table , label , row , column )
        end_col = end_col or column + 2
        self.add_widget( table , id , item , row , column+1 , end_col )

    def add_widget ( self , table , id , item , row , column=0 , end_col=False ) :
        if self.labels[id][2] :
            self.widgets[ self.labels[id][2] ] = item
        end_col = end_col or column + 2
        self.add_button( table , item , row , column , end_col )

    def add_item ( self , table , id , row , column=0 ) :
        item = Entry()
        item.set_max_length( self.labels[id][1] )
        self.add_label( table , id , item ,row , column )
        return item

    def add_floatitem ( self , table , id , row , column=0 ) :
        item = FloatEntry()
        item.set_max_length( self.labels[id][1] )
        self.add_label( table , id , item ,row , column )
        return item

    def add_textitem ( self , store , table , id , row , column=0 ) :
        completion = gtk.EntryCompletion()
        completion.set_model( store )
        completion.set_text_column( self.labels[id][2] )

        item = self.add_item( table , id , row , column )
        item.set_completion( completion )
        return item


class FuelpadAbstractFullEdit :

    labels = { 'EDIT_DATE':( "Date", 20 , configuration.column_dict['DAY']) ,
               'EDIT_LENGTH':( "length", 8 , configuration.column_dict['KM']) ,
               'EDIT_TRIP':( "Trip", 8 , configuration.column_dict['TRIP']) ,
               'EDIT_FILL':( "Fill", 8 , configuration.column_dict['FILL']) ,
               'EDIT_NOTFULL':( "Not full tank", None , None) ,
               'EDIT_PRICE':( "Price", 8 , configuration.column_dict['PRICE']) ,
               'EDIT_NOTES':( "Notes", 50 , configuration.column_dict['NOTES']) ,
               'EDIT_SERVICE':( "Service", 8 , configuration.column_dict['SERVICE']) ,
               'EDIT_OIL':( "Oil", 8 , configuration.column_dict['OIL']) ,
               'EDIT_TIRES':( "Tires", 8 , configuration.column_dict['TIRES']) ,
               'EDIT_CAR':( "Car", None , None ) ,
               'EDIT_DRIVER':( "Driver", None , None)
               }

    def get_label ( self , id ) :
        return gtk.Label( self.config.unit_label( self.labels[id][0] ) )


class FuelpadAbstractSettingsEdit :

    labels = { 'SETTINGS_UNITSYSTEM':( "Unit system", None , "current_unit") ,
               'SETTINGS_FONTSIZE':( "Font size", None , "mainviewfontsize") ,
               'SETTINGS_CURRENCY':( "Currency", 30 , "currency") ,
               'SETTINGS_WIZARDCOLS':( "Wizard items", None , None ) ,
               'SETTINGS_GPS':( "GPS settings", None , None) ,
               'SETTINGS_DELAY':( "Position timeout", 10 , "gps_timeout")
               }

    def get_label ( self , id ) :
        return gtk.Label( self.labels[id][0] )

    def wizard_items_box ( self , config ) :
        item = gtk.VBox()
        item.add( gtk.Label( self.labels['SETTINGS_WIZARDCOLS'][0] ) )
        frame = gtk.HBox()
        for i in range( len(config.wizarditems) ) :
            button = gtk.ToggleButton( label=config.wizarditems[i] )
            if config.wizarditems.is_on( i ) :
                button.set_active( True )
            button.connect("toggled", self.toggle_callback, config, i)
            frame.add( button )
        item.add( frame )
        return item

    def toggle_callback ( self , widget , config , wizard_item) :
        state = widget.get_active()
        if state :
            config.wizarditems.set( wizard_item )
        else :
            config.wizarditems.unset( wizard_item )

    def gps_box ( self , config ) :
        frame = gtk.VBox()
        frame.add( gtk.Label( self.labels['SETTINGS_GPS'][0] ) )
        switcher = CheckButton( "Use GPS" )
        switcher.set_active( config.use_gps )
        def gps_switch ( widget , config ) :
            config.use_gps = widget.get_active()
        switcher.connect("toggled", gps_switch, config )
        frame.add( switcher )
        id = 'SETTINGS_DELAY'
        delay_frame = gtk.HBox( homogeneous=False )
        delay_frame.add( gtk.Label( self.labels[id][0] ) )
        delay = Entry()
        if self.labels[id][2] :
            self.widgets[ self.labels[id][2] ] = delay
        delay.set_max_length( self.labels[id][1] )
        delay.set_text( "%s" % config.gps_timeout )
        delay_frame.add( delay )
        frame.add( delay_frame )
        return frame


if hildon :

    class FuelpadHildonEditwin ( hildon.PannableArea , FuelpadAbstractEditwin ) :

        def __init__( self , config ) :
            hildon.PannableArea.__init__( self )
            self.set_size_request( -1 , self.DIALOG_MIN_HEIGHTMAX )

        def add_table( self , table , label=None ) :
            self.add_with_viewport( table )
            table.show()

        def add_floatitem ( self , table , id , row , column=0 ) :
            item = FuelpadAbstractEditwin.add_floatitem( self , table , id , row , column )
            item.set_input_mode( gtk.HILDON_GTK_INPUT_MODE_NUMERIC|gtk.HILDON_GTK_INPUT_MODE_SPECIAL )
            return item

    class FuelpadFullEdit ( FuelpadHildonEditwin , FuelpadAbstractFullEdit ) :

        def __init__( self , pui , record_date ) :
            self.config = config = pui.config
            FuelpadHildonEditwin.__init__( self , config )

            if record_date is False :
                table = gtk.Table(12, 2, False)
            else :
                table = gtk.Table(10, 2, False)
            self.add_table( table, "Fuel fill" )

            row = 0

            if record_date is False :

                self.carcombo = combos.FuelpadCarCombo( config )
                self.add_button( table , self.carcombo , row , 0 , 2 )
                row += 1

                self.drivercombo = combos.FuelpadDriverCombo( config )
                self.add_button( table , self.drivercombo , row , 0 , 2 )
                row += 1

            # First row, first entry
            self.entrydate = DateEntry( config , record_date )
            self.add_widget( table , 'EDIT_DATE' , self.entrydate , row , 0 )
            row += 1

            # First row, second entry
            self.entrykm = self.add_floatitem( table , 'EDIT_LENGTH' , row )
            row += 1

            if record_date is False :
              self.entrykm.connect( "focus-out-event", kmadded , self , config )

            # Second row, first entry
            self.entrytrip = self.add_floatitem( table , 'EDIT_TRIP' , row )
            row += 1

            if record_date is False :
              self.entrytrip.connect( "focus-out-event", tripadded , self , config )

            # Second row, second entry
            self.entryfill = self.add_floatitem( table , 'EDIT_FILL' , row )
            row += 1

            # Not full button
            self.buttonnotfull = CheckButton( self.labels['EDIT_NOTFULL'][0] )
            self.add_button( self , table , self.buttonnotfull , row , 1 )
            row += 1

            # Third row, first entry
            self.entryprice = self.add_floatitem( table , 'EDIT_PRICE' , row )
            row += 1

            # Third row, second entry
            self.entrynotes = self.add_textitem( pui.view.get_model() , table , 'EDIT_NOTES' , row )
            row += 1

            self.entryservice = self.add_floatitem( table , 'EDIT_SERVICE' , row )
            row += 1

            # Second row, first entry
            self.entryoil = self.add_floatitem( table , 'EDIT_OIL' , row )
            row += 1

            # Third row, first entry
            self.entrytires = self.add_floatitem( table , 'EDIT_TIRES' , row )
            row += 1

    class FuelpadSettingsEdit ( FuelpadHildonEditwin , FuelpadAbstractSettingsEdit ) :

        def __init__( self , config ) :
            FuelpadHildonEditwin.__init__( self , config )

            table = gtk.Table(6, 4, False)
            self.add_table( table , "Visualization settings" )
            row = 0

            # First row, first entry
            item = combos.FuelpadUnitsystemCombo( config , self.labels['SETTINGS_UNITSYSTEM'][0] )
            self.add_widget( table , 'SETTINGS_UNITSYSTEM' , item , row , 0 )
            row += 1

            item = combos.FuelpadFontsizeCombo( config , self.labels['SETTINGS_FONTSIZE'][0] )
            self.add_widget( table , 'SETTINGS_FONTSIZE' , item , row , 0 )
            row += 1

            self.add_item( table , 'SETTINGS_CURRENCY' , row )
            self.widgets[ self.labels['SETTINGS_CURRENCY'][2] ].set_text( config.currency )
            row += 1

            item = self.wizard_items_box( config )
            self.add_widget( table , 'SETTINGS_WIZARDCOLS' , item , row )
            row += 1

            item = self.gps_box( config )
            self.add_widget( table , 'SETTINGS_GPS' , item , row )
            row += 1


else :

    class FuelpadGtkEditwin ( gtk.Notebook , FuelpadAbstractEditwin ) :

        def __init__( self , config ) :
            gtk.Notebook.__init__( self )
            self.set_tab_pos(gtk.POS_TOP)

        def add_table( self , table , label ) :
            scrollwin = gtk.ScrolledWindow(None, None)
            scrollwin.set_size_request(-1, self.DIALOG_MIN_HEIGHT1)
            scrollwin.set_policy(gtk.POLICY_NEVER,
                                 gtk.POLICY_AUTOMATIC)

            scrollwin.add_with_viewport( table )
            table.show()

            self.append_page( scrollwin , gtk.Label( label ) )
            scrollwin.show()

    class FuelpadFullEdit ( FuelpadGtkEditwin , FuelpadAbstractFullEdit ) :

        def __init__( self , pui , record_date ) :
            self.config = config = pui.config
            FuelpadGtkEditwin.__init__( self , config )

            table = gtk.Table(4, 4, False)
            self.add_table( table, "Fuel fill" )
            row = 0

            # First row, first entry
            self.entrydate = DateEntry( config , record_date )
            self.entrydate.set_max_length( self.labels['EDIT_DATE'][1] )
            self.add_label( table , 'EDIT_DATE' , self.entrydate , row )

            # First row, second entry
            self.entrykm = self.add_floatitem( table , 'EDIT_LENGTH' , row , 2 )
            row += 1

            if record_date is False :
              self.entrykm.connect( "focus-out-event", kmadded , self , config )

            # Second row, first entry
            self.entrytrip = self.add_floatitem( table , 'EDIT_TRIP' , row )

            if record_date is False :
              self.entrytrip.connect( "focus-out-event", tripadded , self , config )

            # Second row, second entry
            self.entryfill = self.add_floatitem( table , 'EDIT_FILL' , row , 2 )

            # Not full button
            self.buttonnotfull = CheckButton( self.labels['EDIT_NOTFULL'][0] )
            self.add_button( self , table , self.buttonnotfull , row , 3 )
            row += 1

            # Third row, first entry
            self.entryprice = self.add_floatitem( table , 'EDIT_PRICE' , row )

            # Third row, second entry
            self.entrynotes = self.add_textitem( pui.view.get_model() , table , 'EDIT_NOTES' , row , 2 )
            row += 1

            # Service etc. self
            table = gtk.Table(1, 3, False)
            self.add_table( table, "Service/oil/tires" )
            row = 0

            # First row, first entry
            self.entryservice = self.add_floatitem( table , 'EDIT_SERVICE' , row )
            row += 1

            # Second row, first entry
            self.entryoil = self.add_floatitem( table , 'EDIT_OIL' , row )
            row += 1

            # Third row, first entry
            self.entrytires = self.add_floatitem( table , 'EDIT_TIRES' , row )
            row += 1

            if record_date is False :
              table = gtk.Table(2, 2, False)
              self.add_table( table , "Driver and car" )
              row = 0

              # First row, first entry 
              self.carcombo = combos.FuelpadCarCombo( config )
              self.add_label( table , 'EDIT_CAR' , self.carcombo , row )
              row += 1

              # First row, second entry
              self.drivercombo = combos.FuelpadDriverCombo( config )
              self.add_label( table , 'EDIT_DRIVER' , self.drivercombo , row )
              row += 1

    class FuelpadSettingsEdit ( FuelpadGtkEditwin , FuelpadAbstractSettingsEdit ) :

        def __init__( self , config ) :
            FuelpadGtkEditwin.__init__( self , config )

            table = gtk.Table(6, 4, False)
            self.add_table( table , "Visualization settings" )
            row = 0

            # First row, first entry
            item = combos.FuelpadUnitsystemCombo( config , self.labels['SETTINGS_UNITSYSTEM'][0] )
            self.add_label( table , 'SETTINGS_UNITSYSTEM' , item , row )
            row += 1

            item = combos.FuelpadFontsizeCombo( config , self.labels['SETTINGS_FONTSIZE'][0] )
            self.add_label( table , 'SETTINGS_FONTSIZE' , item , row )
            row += 1

            self.add_item( table , 'SETTINGS_CURRENCY' , row )
            self.widgets[ self.labels['SETTINGS_CURRENCY'][2] ].set_text( config.currency )
            row += 1

            item = self.wizard_items_box( config )
            self.add_widget( table , 'SETTINGS_WIZARDCOLS' , item , row )
            row += 1

            item = self.gps_box( config )
            self.add_widget( table , 'SETTINGS_GPS' , item , row )
            row += 1


