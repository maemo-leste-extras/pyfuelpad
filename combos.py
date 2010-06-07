
import gtk
try :
    import hildon
except :
    hildon = None


class FuelpadAbstractCombo :

    def __init__ ( self , config=None , changed_cb=None ) :
        raise Exception( "Instantiating abstract class %s" % self.__class__ )

    def fill_combo( self , db ) :

        active=0
        i=0
        if db.is_open() :

#         # We'll need to block, otherwise changed_cb would be fired in between
#         self.handler_block_by_func( self.changed_cb )

         for row in db.get_rows( self.query ) :
            listitemtext = "%s %s" % ( row[0] , row[1] )
            self.append_text( listitemtext )
            if row[2] == db.get_current( self.key ) :
              active = i
            i += 1

#         self.handler_unblock_by_func( self.changed_cb )

         self.set_active( active )

    def changed_cb ( self , widget , database ) :
        index = widget.get_active()
        database.currentcar = int( database.carid( index ) )


class FuelpadAbstractItem ( gtk.ToolItem ) :

    def __init__ ( self , config ) :
        gtk.ToolItem.__init__( self )
        self.add( self.combo )

    def add_to( self , parent , position ) :
        parent.insert( self , position )


if hildon :

    class FuelpadSelector ( hildon.TouchSelector , FuelpadAbstractCombo ) :

        def __init__ ( self , config , parentCombo ) :
            hildon.TouchSelector.__init__( self , text=True )
            self.key = parentCombo.key
            self.query = parentCombo.query
            FuelpadAbstractCombo.fill_combo( self , config.db )
            # NOTE : registering the callback will drive permanent changes (even to DB) even with cancellation !!!
            self.connect( "changed", self.changed_cb, config.db )

        def set_active( self , index ) :
            return hildon.TouchSelector.set_active( self , 0 , index )

        def get_active( self ) :
            return hildon.TouchSelector.get_active( self , 0 )

        def changed_cb ( self , widget , id , database ) :
            FuelpadAbstractCombo.changed_cb( self , widget , database )

    class FuelpadCombo ( hildon.PickerButton ) :

        def __init__ ( self , config ) :
            hildon.PickerButton.__init__( self , gtk.HILDON_SIZE_AUTO, hildon.BUTTON_ARRANGEMENT_VERTICAL )
            self.set_title( self.key )
            selector = FuelpadSelector( config , self )
            self.set_selector( selector )

    class FuelpadItem ( FuelpadAbstractItem ) :

        def set_action_callback( self , callback , user_data ) :
            self.combo.connect( "value-changed" , callback , user_data ) 

        def set_active( self , state ) :
             gtk.ToolItem.set_active( self , 0 , active )

        def get_active ( self ) :
            return gtk.ToolItem.get_active( self , 0 )

else :

    class FuelpadCombo ( gtk.ComboBox , FuelpadAbstractCombo ) :

        def __init__ ( self , config ) :
            gtk.ComboBox.__init__( self , gtk.ListStore(str) )
            cell = gtk.CellRendererText()

            gtk.ComboBox.pack_start( self , cell , True )
            gtk.ComboBox.add_attribute( self , cell , 'text' , 0 )
            FuelpadAbstractCombo.fill_combo( self , config.db )

            # NOTE : If registerd before filling, we must ensure we block during that phase
            self.connect( "changed", self.changed_cb, config.db )

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
        self.query = "SELECT nickname,fullname,id FROM driver"
        FuelpadCombo.__init__( self , config )

class FuelpadCarCombo ( FuelpadCombo ) :

    def __init__ ( self , config ) :
        self.key = "Car"
        self.query = "SELECT mark,register,id FROM car"
        FuelpadCombo.__init__( self , config )

class FuelpadCarItem ( FuelpadItem ) :

    def __init__ ( self , config ) :
        self.combo = FuelpadCarCombo( config )
        FuelpadItem.__init__( self , config )

