
import gtk
try :
    import hildon
except :
    hildon = None


class FuelpadAbstractCombo :

    def __init__ ( self ) :
        raise Exception( "Instantiating abstract class %s" % self.__class__ )

    def fill_combo( self , items , active=None ) :
        raise Exception( "Calling uninmplemented method 'fill_combo' on class %s" % self.__class__ )

class  FuelpadAbstractDBCombo ( FuelpadAbstractCombo ) :

    toggle = False

    def render_label ( self , row ) :
        return( "%s %s" % ( row[0] , row[1] ) )

    def fill_combo( self , db , active=None ) :

        active=0
        i=0
        if db.is_open() :

         for row in db.get_rows( self.query ) :
            listitemtext = self.render_label( row )
            self.append_text( listitemtext )
            if row[2] == db.get_current( self.key ) :
              active = i
            i += 1

         self.set_active( active )

    def set_toggle( self , toggle ) :
        self.toggle = toggle

    def changed_cb ( self , widget , database ) :
        index = widget.get_active()
        database.currentcar = int( database.carid( index ) )
        if self.toggle :
            self.toggle.changed = True

class  FuelpadAbstractListCombo ( FuelpadAbstractCombo ) :

    def fill_combo( self , items , active=None ) :

        for i in range(len(items)) :
            listitemtext = "%s" % items[i]
            self.append_text( listitemtext )
            if i == active :
              active = i

        self.set_active( active )

class FuelpadAbstractItem ( gtk.ToolItem ) :

    def __init__ ( self , config ) :
        gtk.ToolItem.__init__( self )
        self.add( self.combo )

    def add_to( self , parent , position ) :
        parent.insert( self , position )


if hildon :

    class FuelpadSelector ( hildon.TouchSelector ) :

        def __init__ ( self ) :
            hildon.TouchSelector.__init__( self , text=True )

        def set_active( self , index ) :
            return hildon.TouchSelector.set_active( self , 0 , index )

        def get_active( self ) :
            return hildon.TouchSelector.get_active( self , 0 )

    class FuelpadDBSelector ( FuelpadSelector , FuelpadAbstractDBCombo ) :

        def __init__ ( self , config , parentCombo ) :
            self.key = parentCombo.key
            self.query = parentCombo.query
            FuelpadSelector.__init__( self )
            self.fill_combo( config.db )
            # NOTE : registering the callback will drive permanent changes (even to DB) even with cancellation !!!
            self.connect( "changed", self.changed_cb, config.db )

        def changed_cb ( self , widget , id , database ) :
            FuelpadAbstractDBCombo.changed_cb( self , widget , database )

    class FuelpadListSelector ( FuelpadSelector , FuelpadAbstractListCombo ) :

        def __init__ ( self , items , active ) :
            FuelpadSelector.__init__( self )
            self.fill_combo( items , active )

    class FuelpadButton ( hildon.PickerButton ) :

        def __init__ ( self , title , selector ) :
            hildon.PickerButton.__init__( self , gtk.HILDON_SIZE_AUTO, hildon.BUTTON_ARRANGEMENT_VERTICAL )
            self.set_title( title )
            self.set_selector( selector )

    class FuelpadCombo ( FuelpadButton ) :

        def __init__ ( self , config ) :
            selector = FuelpadDBSelector( config , self )
            FuelpadButton.__init__( self , self.key , selector )

        def render_label ( self , row ) :
            return self.get_selector().render_label( row )

        def set_toggle( self , toggle ) :
            self.get_selector().set_toggle( toggle )

    class FuelpadListCombo ( FuelpadButton ) :

        def __init__ ( self , items , active=None ) :
            selector = FuelpadListSelector( items , active )
            FuelpadButton.__init__( self , self.key , selector )

    class FuelpadItem ( FuelpadAbstractItem ) :

        def set_action_callback( self , callback , user_data ) :
            self.combo.connect( "value-changed" , callback , user_data ) 

        def set_active( self , state ) :
             gtk.ToolItem.set_active( self , 0 , active )

        def get_active ( self ) :
            return gtk.ToolItem.get_active( self , 0 )

else :

    class FuelpadCombo ( gtk.ComboBox , FuelpadAbstractDBCombo ) :

        def __init__ ( self , config ) :
            gtk.ComboBox.__init__( self , gtk.ListStore(str) )
            cell = gtk.CellRendererText()

            gtk.ComboBox.pack_start( self , cell , True )
            gtk.ComboBox.add_attribute( self , cell , 'text' , 0 )
            self.fill_combo( config.db )

            # NOTE : If registerd before filling, we must ensure we block during that phase
            self.connect( "changed", self.changed_cb, config.db )

    class  FuelpadListCombo ( gtk.ComboBox , FuelpadAbstractListCombo ) :

        def __init__ ( self , items , active=None ) :
            gtk.ComboBox.__init__( self , gtk.ListStore(str) )
            cell = gtk.CellRendererText()

            gtk.ComboBox.pack_start( self , cell , True )
            gtk.ComboBox.add_attribute( self , cell , 'text' , 0 )
            self.fill_combo( items , active )

    class FuelpadItem ( FuelpadAbstractItem ) :

        def __init__ ( self , config ) :
            self.apply = gtk.ToolButton(gtk.STOCK_OK)
            FuelpadAbstractItem.__init__( self , config )

        def add_to( self , parent , position ) :
            FuelpadAbstractItem.add_to( self , parent , position )
            parent.insert( self.apply , position )

        def set_action_callback( self , callback , user_data ) :
            self.apply.connect( "clicked" , callback , user_data )

        def set_expand( self , value ) :
            FuelpadAbstractItem.set_expand( self , value )
            self.apply.set_expand( value )


class FuelpadDriverCombo ( FuelpadCombo ) :

    def __init__ ( self , config ) :
        self.key = "Driver"
        self.query = config.db.ppStmtDriver
        FuelpadCombo.__init__( self , config )

class FuelpadCarCombo ( FuelpadCombo ) :

    def __init__ ( self , config ) :
        self.key = "Car"
        self.query = config.db.ppStmtCar
        FuelpadCombo.__init__( self , config )

class FuelpadCarItem ( FuelpadItem ) :

    def __init__ ( self , config ) :
        self.combo = FuelpadCarCombo( config )
        self.combo.set_toggle( config )
        FuelpadItem.__init__( self , config )

    def select_combo_item ( self , model , db ) :
        query = "SELECT mark,register,id FROM car WHERE id=%s" % db.currentcar
        itemtext = self.combo.render_label( db.get_rows( query )[0] )
        iter = model.get_iter_first()
        while iter :
            if model.get( iter , 0 )[0] == itemtext :
                self.set_active_iter( iter )
                return
            iter = model.iter_next( iter )

import configuration

class FuelpadUnitsystemCombo ( FuelpadListCombo ) :

    def __init__ ( self , config , label=None ) :
        self.key = label
        FuelpadListCombo.__init__( self , configuration.unitsystem , config.units["main"] )

class FuelpadFontsizeCombo ( FuelpadListCombo ) :

    def __init__ ( self , config , label=None ) :
        self.key = label
        FuelpadListCombo.__init__( self , configuration.fontsizes , config.fontsize )

