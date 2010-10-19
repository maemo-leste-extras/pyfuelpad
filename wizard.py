
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

    def __init__ ( self , title , decimals=False ) :

        gtk.Table.__init__( self , 4 , 4 , True )

        x , y = 0 , 0
        # Label for written values
        hbox = gtk.HBox()
        self.title = gtk.Label()
        attrs = configuration.font_attrs( -1 )
        self.title.set_attributes( attrs )
        hbox.pack_start( self.title , expand=False, fill=False )
        self.title.show()
        self.units = gtk.Label()
        attrs = configuration.font_attrs( -1 )
        self.units.set_attributes( attrs )
        hbox.pack_end( self.units , expand=False, fill=False )
        self.units.show()
        # FIXME : is self.label already allocated ???
        self.label = gtk.Label()
        attrs = configuration.font_attrs( -1 )
        self.label.set_attributes( attrs )
        hbox.pack_end( self.label , expand=True, fill=True )
        self.label.show()
        self.attach( hbox , x , x+4 , y , y+1 )
        hbox.show()

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
    if not editwin.entrytrip.get_text() :
        return False
    newkm = float( editwin.entrykm.get_text() or "0" )
    if newkm < 0.1 :
        trip = config.user2SIlength( editwin.entrytrip.get_text() )
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
    if not editwin.entrykm.get_text() :
        return False
    trip = float( editwin.entrytrip.get_text() or "0" )
    newkm = config.user2SIlength( editwin.entrykm.get_text() )
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


class WizardItems :

    def __init__( self ) :

        self.tabs = ( configuration.column_dict['PRICE'] , configuration.column_dict['FILL'] , configuration.column_dict['TRIP'], configuration.column_dict['KM'] )
        self.labels = ( "Price" , "Fill" , "Trip", "Total" )

class FuelpadEdit ( gtk.Notebook ) :

    def __init__( self , config , add ) :
        gtk.Notebook.__init__( self )
        self.set_size_request(450,260)

        page = {}
        page["Price"] = self.entryprice = ButtonPad( "Price" , True )
        page["Fill"] = self.entryfill = ButtonPad( "Fill" , True )
        page["Trip"] = self.entrytrip = ButtonPad( "Trip" ,  True )
        page["Total"] = self.entrykm = ButtonPad( "Total" )
        wizard_items = WizardItems()
        for i in range( len(wizard_items.tabs) ) :
            if config.wizardcol & (1<<configuration.column_info[wizard_items.tabs[i]][0]):
                self.append_page( page[ wizard_items.labels[i] ] , gtk.Label( wizard_items.labels[i] ) )
                page[ wizard_items.labels[i] ].title.set_text( wizard_items.labels[i] )
            else :
                page[ wizard_items.labels[i] ] = False
        if page["Price"] :
            page[ "Price" ].units.set_text( config.currency )
        if page["Fill"] :
            info =  configuration.column_info[wizard_items.tabs[1]]
            if config.isSI( "length" ) :
                page[ "Fill" ].units.set_text( "litres" )
            else :
                page[ "Fill" ].units.set_text( "gallons" )
        if page["Trip"] :
            info =  configuration.column_info[wizard_items.tabs[3]]
            if config.isSI( "length" ) :
                page[ "Trip" ].units.set_text( info[2] )
            else :
                page[ "Trip" ].units.set_text( info[4] )
        if page["Total"] :
            info =  configuration.column_info[wizard_items.tabs[3]]
            if config.isSI( "length" ) :
                page[ "Total" ].units.set_text( info[2] )
            else :
                page[ "Total" ].units.set_text( info[4] )

        # Not shown widgets
        self.entrydate = gtk.Entry()
        self.entrydate.set_text( utils.gettimefmt( config.dateformat ) )
        self.buttonnotfull = gtk.CheckButton()

        # To avoid confusion with FuelpadFullEdit
        self.entryservice = False

        # Set a handler for "switch-page" signal
        self.connect_object( "switch-page" , self.on_page_switch , config )

    def on_page_switch( self , config , page , num ) :
        print "switching",self,config,page,num
        if self.get_current_page() == 1 :
            callback_tripadded( None , None , self , config )
        elif self.get_current_page() == 2 :
            callback_kmadded( None , None , self , config )
        return True

class FuelpadAbstractEditwin :

    widgets = {}

    #DIALOG_MIN_HEIGHT0 = 300
    DIALOG_MIN_HEIGHT1 = 150
    #DIALOG_MIN_HEIGHT2 = 150
    DIALOG_MIN_HEIGHTMAX = 400
    #DIALOG_MIN_WIDTH1 = 720

    def add_label ( self , table , id , item , row , column=0 ) :
        if self.labels[id][2] :
            self.widgets[ self.labels[id][2] ] = item
        label = gtk.Label( self.labels[id][0] )
        table.attach(label, column, column+1, row, row+1,
                     gtk.EXPAND|gtk.FILL,
                     0, 0, 5)
        label.show()
        table.attach(item, column+1, column+2, row, row+1,
                     gtk.EXPAND|gtk.FILL,
                     0, 0, 5)
        item.show()

    def add_widget ( self , table , id , item , row , column=0 ) :
        if self.labels[id][2] :
            self.widgets[ self.labels[id][2] ] = item
        table.attach(item, column, column+2, row, row+1,
                     gtk.EXPAND|gtk.FILL,
                     0, 0, 5)
        item.show()

    def new_item ( self ) :
        raise Exception( "Calling uninmplemented method 'new_item' on class %s" % self.__class__ )

    def add_item ( self , table , id , row , column=0 ) :
        item = self.new_item()
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
               'EDIT_KM':( "Km", 8 , configuration.column_dict['KM']) ,
               'EDIT_MILES':( "Miles", 8 , configuration.column_dict['KM']) ,
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


class FuelpadAbstractSettingsEdit :

    labels = { 'SETTINGS_UNITSYSTEM':( "Unit system", None , "current_unit") ,
               'SETTINGS_FONTSIZE':( "Font size", None , "mainviewfontsize") ,
               'SETTINGS_CURRENCY':( "Currency", 30 , "currency") ,
               'SETTINGS_WIZARDCOLS':( "Wizard items", None , None )  
               }

    def wizard_items_box ( self , config ) :
        item = gtk.VBox()
        item.add( gtk.Label( self.labels['SETTINGS_WIZARDCOLS'][0] ) )
        frame = gtk.HBox()
        wizard_items = WizardItems()
        for i in range( len(wizard_items.tabs) ) :
            button = gtk.ToggleButton( label=wizard_items.labels[i] )
            if config.wizardcol & (1<<configuration.column_info[wizard_items.tabs[i]][0]) :
                button.set_active( True )
            button.connect("toggled", self.toggle_callback, config, wizard_items.tabs[i])
            frame.add( button )
        item.add( frame )
        return item

    def toggle_callback ( self , widget , config , wizard_item) :
        state = widget.get_active()
        if state :
            config.wizardcol += 1<<configuration.column_info[wizard_item][0]
        else :
            config.wizardcol -= 1<<configuration.column_info[wizard_item][0]

if hildon :

    class FuelpadHildonEditwin ( hildon.PannableArea , FuelpadAbstractEditwin ) :

        def __init__( self , config ) :
            hildon.PannableArea.__init__( self )
            self.set_size_request( -1 , self.DIALOG_MIN_HEIGHTMAX )

        def add_table( self , table ) :
            self.add_with_viewport( table )
            table.show()

        def new_item ( self ) :
            return hildon.Entry( gtk.HILDON_SIZE_FINGER_HEIGHT )

        def add_button ( self , table , item , row ) :
            table.attach(item, 0, 2, row, row+1,
                         gtk.EXPAND|gtk.FILL,
                         0, 0, 5)
            item.show()

    class FuelpadFullEdit ( FuelpadHildonEditwin , FuelpadAbstractFullEdit ) :

        def __init__( self , pui , record_date ) :
            config = pui.config
            FuelpadHildonEditwin.__init__( self , config )

            if record_date is False :
                table = gtk.Table(12, 2, False)
            else :
                table = gtk.Table(10, 2, False)
            self.add_table( table )

            row = 0

            if record_date is False :

                self.carcombo = combos.FuelpadCarCombo( config )
                self.add_button( table , self.carcombo , row )
                row += 1

                self.drivercombo = combos.FuelpadDriverCombo( config )
                self.add_button( table , self.drivercombo , row )
                row += 1

            # First row, first entry
            self.entrydate = hildon.DateButton( gtk.HILDON_SIZE_FINGER_HEIGHT , hildon.BUTTON_ARRANGEMENT_VERTICAL )
            if record_date :
                datestruct = utils.getdatestruct( record_date )
                self.entrydate.set_date( datestruct[0] , datestruct[1]-1 , datestruct[2] )
            self.add_button( table , self.entrydate , row )
            self.widgets[ self.labels['EDIT_DATE'][2] ] = self.entrydate
            row += 1

            # First row, second entry
            if config.isSI( 'length' ) :
              self.entrykm = self.add_item( table , 'EDIT_KM' , row )
            else :
              self.entrykm = self.add_item( table , 'EDIT_MILES' , row )
            row += 1

            if record_date is False :
              self.entrykm.connect( "focus-out-event", callback_kmadded , self , config )

            # Second row, first entry
            self.entrytrip = self.add_item( table , 'EDIT_TRIP' , row )
            row += 1

            if record_date is False :
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
            self.entrynotes = self.add_textitem( pui.view.get_model() , table , 'EDIT_NOTES' , row )
            row += 1

            self.entryservice = self.add_item( table , 'EDIT_SERVICE' , row )
            row += 1

            # Second row, first entry
            self.entryoil = self.add_item( table , 'EDIT_OIL' , row )
            row += 1

            # Third row, first entry
            self.entrytires = self.add_item( table , 'EDIT_TIRES' , row )
            row += 1

        def add_item ( self , table , id , row , column=0 ) :
            item = FuelpadHildonEditwin.add_item( self , table , id , row , column )
            if id != 'EDIT_NOTES' :
                item.set_input_mode( gtk.HILDON_GTK_INPUT_MODE_NUMERIC|gtk.HILDON_GTK_INPUT_MODE_SPECIAL )
            #    item.set_property( "autocap", False)
            return item

    class FuelpadSettingsEdit ( FuelpadHildonEditwin , FuelpadAbstractSettingsEdit ) :

        def __init__( self , config ) :
            FuelpadHildonEditwin.__init__( self , config )

            table = gtk.Table(6, 4, False)
            self.add_table( table )

            # First row, first entry
            item = combos.FuelpadUnitsystemCombo( config , self.labels['SETTINGS_UNITSYSTEM'][0] )
            self.widgets[ self.labels['SETTINGS_UNITSYSTEM'][2] ] = item
            self.add_button( table , item , 0 )

            item = combos.FuelpadFontsizeCombo( config , self.labels['SETTINGS_FONTSIZE'][0] )
            self.widgets[ self.labels['SETTINGS_FONTSIZE'][2] ] = item
            self.add_button( table , item , 1 )

            self.add_item( table , 'SETTINGS_CURRENCY' , 2 )
            self.widgets[ self.labels['SETTINGS_CURRENCY'][2] ].set_text( config.currency )

            item = self.wizard_items_box( config )
            self.add_widget( table , 'SETTINGS_WIZARDCOLS' , item , 3 )

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

        def new_item ( self ) :
            return gtk.Entry()

    class FuelpadFullEdit ( FuelpadGtkEditwin , FuelpadAbstractFullEdit ) :

        def __init__( self , pui , record_date ) :
            config = pui.config
            FuelpadGtkEditwin.__init__( self , config )

            table = gtk.Table(4, 4, False)
            self.add_table( table, "Fuel fill" )

            # First row, first entry
            self.entrydate = self.add_item( table , 'EDIT_DATE' , 0 )
            if record_date :
                print "SETTING DATE TO %s" % record_date
                self.entrydate.set_text( utils.gettimefmt( config.dateformat , record_date ) )
            else :
                self.entrydate.set_text( utils.gettimefmt( config.dateformat ) )

            # First row, second entry
            if config.isSI( 'length' ) :
              self.entrykm = self.add_item( table , 'EDIT_KM' , 0 , 2 )
            else :
              self.entrykm = self.add_item( table , 'EDIT_MILES' , 0 , 2 )

            if record_date is False :
              self.entrykm.connect( "focus-out-event", callback_kmadded , self , config )

            # Second row, first entry
            self.entrytrip = self.add_item( table , 'EDIT_TRIP' , 1 )

            if record_date is False :
              self.entrytrip.connect( "focus-out-event", callback_tripadded , self , config )

            # Second row, second entry
            self.entryfill = self.add_item( table , 'EDIT_FILL' , 1 , 2 )

            # Not full button
            self.buttonnotfull = gtk.CheckButton( label=self.labels['EDIT_NOTFULL'][0] )
            table.attach( self.buttonnotfull, 3, 4, 2, 3,
                       gtk.EXPAND|gtk.FILL,
                       0, 0, 5)
            self.buttonnotfull.show()

            # Third row, first entry
            self.entryprice = self.add_item( table , 'EDIT_PRICE' , 3 )

            # Third row, second entry
            self.entrynotes = self.add_textitem( pui.view.get_model() , table , 'EDIT_NOTES' , 3 , 2 )

            completion = gtk.EntryCompletion()
            store = pui.view.get_model()
            completion.set_model( store )
            completion.set_text_column( configuration.column_dict['NOTES'] )
            self.entrynotes.set_completion( completion )

            # Service etc. self
            table = gtk.Table(1, 3, False)
            self.add_table( table, "Service/oil/tires" )

            # First row, first entry
            self.entryservice = self.add_item( table , 'EDIT_SERVICE' , 0 )

            # Second row, first entry
            self.entryoil = self.add_item( table , 'EDIT_OIL' , 1 )

            # Third row, first entry
            self.entrytires = self.add_item( table , 'EDIT_TIRES' , 2)

            if record_date is False :
              table = gtk.Table(2, 2, False)
              self.add_table( table , "Driver and car" )

              # First row, first entry 
              self.carcombo = combos.FuelpadCarCombo( config )
              self.add_label( table , 'EDIT_CAR' , self.carcombo , 0 )

              # First row, second entry
              self.drivercombo = combos.FuelpadDriverCombo( config )
              self.add_label( table , 'EDIT_DRIVER' , self.drivercombo , 1 )

    class FuelpadSettingsEdit ( FuelpadGtkEditwin , FuelpadAbstractSettingsEdit ) :

        def __init__( self , config ) :
            FuelpadGtkEditwin.__init__( self , config )

            table = gtk.Table(6, 4, False)
            self.add_table( table , "Visualization settings" )

            # First row, first entry
            item = combos.FuelpadUnitsystemCombo( config )
            self.add_label( table , 'SETTINGS_UNITSYSTEM' , item , 0 )

            item = combos.FuelpadFontsizeCombo( config )
            self.add_label( table , 'SETTINGS_FONTSIZE' , item , 1 )

            self.add_item( table , 'SETTINGS_CURRENCY' , 2 )
            self.widgets[ self.labels['SETTINGS_CURRENCY'][2] ].set_text( config.currency )

            item = self.wizard_items_box( config )
            self.add_widget( table , 'SETTINGS_WIZARDCOLS' , item , 3 )

