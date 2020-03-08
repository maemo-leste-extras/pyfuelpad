
import utils
import configuration , callbacks
import combos
import db


import gtk
try :
    import hildon
except :
    hildon = None


def cell_data_func (column, renderer, model, iter, user_data) :
    value = model.get( iter, user_data[0] )[0]
    if user_data[0] == configuration.column_dict["CONSUM"] or user_data[0] == configuration.column_dict["CO2EMISSION"] :
        if (value*value) < 1e-10 :
            renderer.set_property( "text", "-")
            return
    renderer.set_property( "text" , user_data[1] % value )

# Reworked, but completelly ported (except for gettext)
def get_column_header ( info , config ) :

    format = info[3] or "%s"
    label = config.unit_label( info[2] )
    return format % label


class FuelpadModel ( gtk.TreeModelSort ) :

    def __init__( self , config ) :

        if not config.db.is_open() :
            raise Exception( "There is no database available" )

        store = gtk.ListStore(str, float, float, float, float, float , float , float , float , float , float , float , str, int, bool)

        query = "SELECT day,km,trip,fill,consum,price,priceperlitre,service,oil,tires,notes,id FROM record WHERE carid=%d ORDER BY km" % config.db.currentcar
        for row in config.db.get_rows( query ) :

            date = utils.convdate( config.dateformat , None , row[0] )

	    convnotes = row[10]
	    trip , fill = utils.doubleornothing( row[2] ) , utils.doubleornothing( row[3] )
	    price , consum = utils.doubleornothing( row[5] ) , utils.doubleornothing( row[4] )
	    length , priceperlitre = utils.doubleornothing( row[1] ) , utils.doubleornothing( row[6] )
            co2 = utils.calc_co2_emission( consum , config.db.fueltype() )
            if price and trip :
                pricepertrip = price / config.SIlength2user(trip)
            else :
                pricepertrip = 0
	    iter = store.append()
            store.set( iter ,
                       configuration.column_dict['DAY'], date,
                       configuration.column_dict['KM'], config.SIlength2user(length),
                       configuration.column_dict['TRIP'], config.SIlength2user(trip),
                       configuration.column_dict['FILL'], config.SIvolume2user(fill),
                       configuration.column_dict['CONSUM'], config.SIconsumption2user(consum),
                       configuration.column_dict['PRICE'], price,
                       configuration.column_dict['PRICEPERTRIP'], pricepertrip,
                       configuration.column_dict['PRICEPERLITRE'], config.SIppl2user(priceperlitre),
                       configuration.column_dict['SERVICE'], utils.doubleornothing( row[7] ),
                       configuration.column_dict['OIL'], utils.doubleornothing( row[8] ),
                       configuration.column_dict['TIRES'], utils.doubleornothing( row[9] ),
                       configuration.column_dict['CO2EMISSION'], config.SIemission2user( co2 ),
                       configuration.column_dict['NOTES'], convnotes,
                       configuration.column_dict['ID'], row[11],
                       configuration.column_dict['VISIBLE'], True
                       )

        gtk.TreeModelSort.__init__( self , store )

        self.connect_object( "sort-column-changed", self.sort_change , config )

    def sort_change( self , config ) :
        colid , order = self.get_sort_column_id()
        if colid is None :
            config.maintablesorted = False
        else :
            config.maintablesorted = True
            config.maintablesortcol = colid
            config.maintablesortorder = int(order)


class FuelpadAbstractView :

    def __init__ ( self , config ) :

        attrs = configuration.font_attrs ( config.fontsize  )

        for info in configuration.column_info :
            col = gtk.TreeViewColumn()

            if info[6] : # column is showable

                label = gtk.Label()
                col.set_widget( label )
                label.set_attributes( attrs )
                label.show()

                # pack cell renderer into tree view column 
                renderer = gtk.CellRendererText()
                col.pack_start(renderer, True)

                col.add_attribute(renderer, "text", info[0])
                if info[4] :
                    col.set_cell_data_func( renderer , cell_data_func, ( info[0] , info[4] ) )

                col.set_resizable( True )
                renderer.set_property( "scale" , configuration.fontscalefactors[config.fontsize] )

                col.set_sort_column_id( info[0] )

            else :
                col.set_visible( False )

            # pack tree view column into tree view 
            self.append_column(col)


        self.update_column_headers( config )
        self.set_headers_visible( True )

        select = self.get_selection()
        select.set_mode( gtk.SELECTION_SINGLE )

    def update_column_headers ( self , config ) :

        for col in self.get_columns() :
          colid = col.get_sort_column_id()
          if colid != -1 :
              colinfo = configuration.column_info[colid]
              header = get_column_header( colinfo , config )
              col.get_widget().set_text( header )
              self.get_column(colinfo[0]).set_visible( config.dispcol & (1<<colinfo[0]) )

    def update ( self , pui ) :

        # Update the UI
        while gtk.events_pending() :
            gtk.main_iteration()

        if pui.config.changed :
           pui.stb_car.select_combo_item( pui.view.get_model() , pui.config.db )
        pui.config.changed = False

        self.set_model( FuelpadModel( pui.config ) )
        self.update_column_headers( pui.config )
        pui.update_totalkm()


class FuelpadAbstractWindow :

    def __init__ ( self , config ) :

        self.connect( "delete_event" , callbacks.delete_event , self )

        self.mainfullscreen = False
        self.config = config

        self.warn = False
        self.create_mainwin_widgets()

        # Begin the main application
        self.show_all()

        self.toolbar_show_hide()

    # Show or hide toolbars (with reversed logic)
    def toolbar_show_hide ( self ) :
        if self.config.main_toolbar_visible : 
            self.main_toolbar.show()
        else :
            self.main_toolbar.hide()
        if self.config.secondary_toolbar_visible :
            self.secondary_toolbar.show()
        else :
            self.secondary_toolbar.hide()

    def create_mainwin_widgets ( self ) :

        vbox = gtk.VBox(False, 0)
        self.add( vbox )

        self.create_mainwin_menu( vbox )

        vbox.pack_start( self.datascrollwin, True , True , 0 )

        self.view = FuelpadView( self.config )
        self.datascrollwin.add( self.view )

        self.create_mainwin_toolbar( )
        self.create_secondary_toolbar( )

        # Add toolbars
        self.pack_toolbars( vbox )

        self.enable_mainmenu_items()

        vbox.show_all()

    def create_mainwin_menu ( self , vbox ) :

         self.main_menu.show_all()

    def create_mainwin_toolbar ( self ) :

        # Create toolbar
        self.main_toolbar = gtk.Toolbar();

        # Create toolbar button items
        self.mtb_add = gtk.ToolButton( gtk.STOCK_ADD )
        self.mtb_edit = gtk.ToolButton( gtk.STOCK_EDIT )
        self.mtb_delete = gtk.ToolButton( gtk.STOCK_DELETE )
        self.mtb_close = gtk.ToolButton( gtk.STOCK_QUIT )

        self.mtb_add.set_expand( True )
        self.mtb_edit.set_expand( True )
        self.mtb_delete.set_expand( True )
        self.mtb_close.set_expand( True )

        # Add all items to toolbar
        self.main_toolbar.insert( self.mtb_add, -1)
        self.main_toolbar.insert( gtk.SeparatorToolItem(), -1)
        self.main_toolbar.insert( self.mtb_edit, -1)
        self.main_toolbar.insert( self.mtb_delete, -1)
        self.main_toolbar.insert( gtk.SeparatorToolItem(), -1)
        self.main_toolbar.insert( self.mtb_close, -1)

        self.mtb_add.connect( "clicked" , callbacks.newrecord , self )
        self.mtb_edit.connect( "clicked", callbacks.editrecord, self)
        self.mtb_delete.connect( "clicked", callbacks.deleterecord, self)
        self.mtb_close.connect( "clicked" , callbacks.delete_event , self )

    def create_secondary_toolbar( self ) :

        # Create toolbar
        self.secondary_toolbar = gtk.Toolbar()

        # Create toolbar items

        attrs = configuration.font_attrs ( 1 )

        # Car combo
        self.stb_car = combos.FuelpadCarItem( self.config )

        # Total distance
        self.stb_totalkm = gtk.ToolItem()
        self.stb_totalkmlabel = gtk.Label()
        self.stb_totalkmlabel.set_selectable( True )
        self.stb_totalkmlabel.set_attributes( attrs )
        self.stb_totalkm.add( self.stb_totalkmlabel )

        # Average consumption
        self.stb_avgconsum = gtk.ToolItem()
        self.stb_avgconsumlabel = gtk.Label()
        self.stb_avgconsumlabel.set_selectable( True )
        self.stb_avgconsumlabel.set_attributes( attrs )
        self.stb_avgconsum.add( self.stb_avgconsumlabel )

        # Total cost
        self.stb_totcost = gtk.ToolItem()
        self.stb_totcostlabel = gtk.Label()
        self.stb_totcostlabel.set_selectable( True )
        self.stb_totcostlabel.set_attributes( attrs )
        self.stb_totcost.add( self.stb_totcostlabel )

        self.update_totalkm()

        self.stb_car.set_expand( False )
        self.stb_totalkm.set_expand( True )
        self.stb_avgconsum.set_expand( True )
        self.stb_totcost.set_expand( True )
        self.stb_add.set_expand( True )

        # Add all items to toolbar
        self.stb_car.add_to( self.secondary_toolbar , -1 )
        self.secondary_toolbar.insert(self.stb_totalkm, -1);
        self.secondary_toolbar.insert(self.stb_avgconsum, -1);
        self.secondary_toolbar.insert(self.stb_totcost, -1);
        self.secondary_toolbar.insert(self.stb_add, -1);

        self.stb_car.set_action_callback( callbacks.car_apply_cb , self )

    def enable_mainmenu_items( self ) :

        dbopen = self.config.db.is_open()
        self.mtb_add.set_sensitive( dbopen )
        self.mtb_edit.set_sensitive( dbopen )

    def update_totalkm ( self ) :

        totalkm = self.config.db.totalkm(self.config.stbstattime)

	str = "%.0f %s" % ( self.config.SIlength2user(totalkm) , self.config.unit_label( "length" ) )
        self.stb_totalkmlabel.set_text( str )

        totalfill = self.config.db.totalfill(self.config.stbstattime)
        totalfillkm = self.config.db.totalfillkm(self.config.stbstattime)
        if totalfillkm != 0.0 :
            str = "%.1f %s" % ( self.config.SIconsumption2user(totalfill/totalfillkm*100) , self.config.unit_label( "consume" ) )
        else :
            str = "%.1f %s" % ( 0.0 , self.config.unit_label( "consume" ) )
        self.stb_avgconsumlabel.set_text( str )

        str = "%.0f %s" % ( self.config.db.totalcost() , self.config.currency )
        self.stb_totcostlabel.set_text( str )


if hildon :

    class FuelpadView ( hildon.GtkTreeView , FuelpadAbstractView ) :

        def __init__ ( self , config ) :

            config.main_toolbar_visible = False
            config.secondary_toolbar_visible = True

            model = FuelpadModel( config )
            hildon.GtkTreeView.__init__( self , gtk.HILDON_UI_MODE_EDIT , model )
            FuelpadAbstractView.__init__( self , config )
            self.connect( "hildon-row-tapped" , callbacks.recordactivated )
            self.taptime , self.taprow = -1 , -1

            if config.maintablesorted :
                self.get_model().set_sort_column_id( config.maintablesortcol , config.maintablesortorder )

    class FuelpadWindow( hildon.StackableWindow , FuelpadAbstractWindow ) :

        def __init__ ( self , config ) :

            # Create the hildon program and setup the title
            program = hildon.Program.get_instance()
            gtk.set_application_name( "Fuelpad" )

            # Create HildonWindow and set it to HildonProgram
            hildon.StackableWindow.__init__( self )
            program.add_window( self )

            FuelpadAbstractWindow.__init__( self , config )

        def create_mainwin_widgets ( self ) :

            self.datascrollwin = hildon.PannableArea()
            self.datascrollwin.set_property( "mov-mode" , hildon.MOVEMENT_MODE_BOTH )

            FuelpadAbstractWindow.create_mainwin_widgets( self )

        def pack_toolbars( self , widget=None ) :
            self.add_toolbar( self.main_toolbar )
            self.add_toolbar( self.secondary_toolbar )

        def create_secondary_toolbar( self ) :
            self.stb_add = gtk.ToolItem()
            self.stb_addbutton = hildon.Button(gtk.HILDON_SIZE_AUTO,
                                                          hildon.BUTTON_ARRANGEMENT_HORIZONTAL,
                                                          None,
                                                          "Add record")
            image = gtk.image_new_from_stock(gtk.STOCK_ADD, gtk.ICON_SIZE_BUTTON)
            self.stb_addbutton.set_image(image)
            self.stb_add.add( self.stb_addbutton )
            self.stb_addbutton.connect( "clicked" , callbacks.newrecord , self , True )
            FuelpadAbstractWindow.create_secondary_toolbar( self )

        def create_mainwin_menu ( self , vbox ) :

            self.main_menu = hildon.AppMenu()

            self.mm_item_new = hildon.Button(gtk.HILDON_SIZE_AUTO,
                                                          hildon.BUTTON_ARRANGEMENT_VERTICAL,
                                                          "Add record",
                                                          None)
            self.main_menu.append( self.mm_item_new )

            self.mm_item_edit = hildon.Button(gtk.HILDON_SIZE_AUTO,
                                                          hildon.BUTTON_ARRANGEMENT_VERTICAL,
                                                          "Edit record" ,
                                                          None)
            self.main_menu.append( self.mm_item_edit )

            self.mm_item_delete = hildon.Button(gtk.HILDON_SIZE_AUTO,
                                                          hildon.BUTTON_ARRANGEMENT_VERTICAL,
                                                          "Delete record" ,
                                                          None)
            self.main_menu.append( self.mm_item_delete )

            self.mm_item_settings = hildon.Button(gtk.HILDON_SIZE_AUTO,
                                                          hildon.BUTTON_ARRANGEMENT_VERTICAL,
                                                          "Settings",
                                                          None)
            self.main_menu.append( self.mm_item_settings )

            self.mm_item_about = hildon.Button(gtk.HILDON_SIZE_AUTO,
                                                          hildon.BUTTON_ARRANGEMENT_VERTICAL,
                                                          "About ..." ,
                                                          None)
            self.main_menu.append( self.mm_item_about )

            self.mm_item_new.connect( "clicked", callbacks.newrecord , self )
            self.mm_item_edit.connect( "clicked", callbacks.editrecord , self )
            self.mm_item_settings.connect( "clicked", callbacks.settings , self )
            self.mm_item_delete.connect( "clicked", callbacks.deleterecord , self )
            self.mm_item_about.connect( "clicked", callbacks.about , self )

            self.set_app_menu( self.main_menu )

            FuelpadAbstractWindow.create_mainwin_menu( self , vbox )


else :

    class FuelpadView ( gtk.TreeView , FuelpadAbstractView ) :

        def __init__ ( self , config ) :
            model = FuelpadModel( config )
            gtk.TreeView.__init__( self , model )
            FuelpadAbstractView.__init__( self , config )
            self.connect( "row-activated" , callbacks.recordactivated )
            self.taptime , self.taprow = -1 , -1

    class FuelpadWindow( gtk.Window , FuelpadAbstractWindow ) :

        def __init__ ( self , config ) :

            # Create the main window
            gtk.Window.__init__( self , gtk.WINDOW_TOPLEVEL )
            self.set_title( "fuelpad" )

            # NOTE : temporary to get a decent window
            self.set_size_request(640,480)

            FuelpadAbstractWindow.__init__( self , config )

        def create_mainwin_widgets ( self ) :

            self.datascrollwin = gtk.ScrolledWindow( None , None )

            FuelpadAbstractWindow.create_mainwin_widgets( self )

        def pack_toolbars( self , widget ) :
            widget.pack_start( self.main_toolbar , False , False , 5 )
            widget.pack_start( self.secondary_toolbar , False , False , 5 )

        def create_secondary_toolbar( self ) :
            self.stb_add = gtk.ToolButton( gtk.STOCK_ADD )
            self.stb_add.connect( "clicked" , callbacks.newrecord , self , True )
            FuelpadAbstractWindow.create_secondary_toolbar( self )

        def create_mainwin_menu ( self , vbox ) :

            self.main_menu = gtk.Menu()
            self.mm_menu_db = gtk.Menu()
            self.mm_menu_record = gtk.Menu()
            self.mm_menu_stat = gtk.Menu()
            self.mm_menu_view = gtk.Menu()
            self.mm_menu_toolbar = gtk.Menu()
            self.mm_menu_fontsize = gtk.Menu()

            # Create main menu items
            self.mm_item_db = gtk.MenuItem( label="Database" )
            self.mm_item_record = gtk.MenuItem( label="Record" )
            self.mm_item_stat = gtk.MenuItem( label="Statistics" )
            self.mm_item_alarm = gtk.MenuItem( label="Reminders..." )
            self.mm_item_view = gtk.MenuItem( label="View" )
            self.mm_item_settings = gtk.MenuItem( label="Settings..." )
            self.mm_item_about = gtk.MenuItem( label="About" )
            self.mm_item_exit = gtk.MenuItem( label="Exit" )

            # Create database menu items
            self.mm_item_open = gtk.MenuItem( label="Open..." )
            self.mm_item_close = gtk.MenuItem( label="Close" )
            self.mm_item_import = gtk.MenuItem( label="Import..." )
            self.mm_item_export = gtk.MenuItem( label="Export..." )

            # Create record menu items
            self.mm_item_new = gtk.MenuItem( label="New" )
            self.mm_item_edit = gtk.MenuItem( label="Edit" )
            self.mm_item_delete = gtk.MenuItem( label="Delete" )
            # Create statistics menu items
            self.mm_item_quick = gtk.MenuItem( label="Quick" )
            self.mm_item_monthly = gtk.MenuItem( label="Graphical" )
            self.mm_item_report = gtk.MenuItem( label="Yearly report" )

            # Create view menu items
            self.main_menu_item_fullscreen = gtk.CheckMenuItem("Full screen" )
            self.main_menu_item_fullscreen.set_active( self.mainfullscreen )
            self.mm_item_toolbar = gtk.MenuItem( label="Toolbars" )
            self.mm_item_fontsize = gtk.MenuItem( label="Table font size" )
            self.mm_item_columnselect = gtk.MenuItem( label="Select columns..." )
            self.mm_item_filter = gtk.MenuItem( label="Filter records..." )

            # Create toolbar menu items
            self.mm_item_toolbar_main = gtk.CheckMenuItem( "Buttons" )
            self.mm_item_toolbar_main.set_active( self.config.main_toolbar_visible )
            self.mm_item_toolbar_secondary = gtk.CheckMenuItem( "Information" )
            self.mm_item_toolbar_secondary.set_active( self.config.secondary_toolbar_visible )

            # Create fontsize menu items
            radio_menu_group = self.mm_item_fontsize_x_small = gtk.RadioMenuItem( None , "Extra small" )
            if self.config.fontsize == configuration.XSMALL :
                self.mm_item_fontsize_x_small.set_active(True)
            radio_menu_group = self.mm_item_fontsize_small = gtk.RadioMenuItem( radio_menu_group , "Small" )
            if self.config.fontsize == configuration.SMALL :
                self.mm_item_fontsize_small.set_active( True )
            radio_menu_group = self.mm_item_fontsize_medium = gtk.RadioMenuItem( radio_menu_group , "Medium" )
            if self.config.fontsize == configuration.MEDIUM :
                self.mm_item_fontsize_medium.set_active( True )
            radio_menu_group = self.mm_item_fontsize_large = gtk.RadioMenuItem( radio_menu_group , "Large" )
            if self.config.fontsize == configuration.LARGE :
                self.mm_item_fontsize_large.set_active( True )

            # Add menu items to right menus
            # Main menu
            self.main_menu.append( self.mm_item_record )
            self.main_menu.append( self.mm_item_stat )
            self.main_menu.append( gtk.SeparatorMenuItem() )
            self.main_menu.append( self.mm_item_alarm )
            self.main_menu.append( gtk.SeparatorMenuItem() )
            self.main_menu.append( self.mm_item_view )
            self.main_menu.append( gtk.SeparatorMenuItem() )
            self.main_menu.append( self.mm_item_settings )
            self.main_menu.append( gtk.SeparatorMenuItem() )
            self.main_menu.append( self.mm_item_about )
            self.main_menu.append( self.mm_item_exit )

            # Database menu
            self.mm_menu_db.append( self.mm_item_open )
            self.mm_menu_db.append( self.mm_item_close )
            self.mm_menu_db.append( self.mm_item_import )
            self.mm_menu_db.append( self.mm_item_export )

            # Record menu
            self.mm_menu_record.append( self.mm_item_new )
            self.mm_menu_record.append( self.mm_item_edit )
            self.mm_menu_record.append( self.mm_item_delete )

            # Statistics menu
            self.mm_menu_stat.append( self.mm_item_quick )
            self.mm_menu_stat.append( self.mm_item_monthly )
            self.mm_menu_stat.append( self.mm_item_report )

            # View menu
            self.mm_menu_view.append( self.main_menu_item_fullscreen )
            self.mm_menu_view.append( self.mm_item_toolbar )
            self.mm_menu_view.append( self.mm_item_fontsize )
            self.mm_menu_view.append( self.mm_item_columnselect )
            self.mm_menu_view.append( self.mm_item_filter )

            # Toolbars menu
            self.mm_menu_toolbar.append( self.mm_item_toolbar_main )
            self.mm_menu_toolbar.append( self.mm_item_toolbar_secondary )

            # Font size menu
            self.mm_menu_fontsize.append( self.mm_item_fontsize_x_small )
            self.mm_menu_fontsize.append( self.mm_item_fontsize_small )
            self.mm_menu_fontsize.append( self.mm_item_fontsize_medium )
            self.mm_menu_fontsize.append( self.mm_item_fontsize_large )

            self.mm_menubar = gtk.MenuBar()
            vbox.pack_start( self.mm_menubar, False, False, 2)
            self.mm_menubar.show()
            self.mm_item_db.set_submenu( self.mm_menu_db )
            self.mm_menubar.append( self.mm_item_db )
            self.mm_item_fuelpad = gtk.MenuItem( label="fuelpad" )
            self.mm_item_fuelpad.show()
            self.mm_item_fuelpad.set_submenu( self.main_menu )
            self.mm_menubar.append( self.mm_item_fuelpad )
            self.mm_item_record.set_submenu( self.mm_menu_record )
            self.mm_item_stat.set_submenu( self.mm_menu_stat )
            self.mm_item_view.set_submenu( self.mm_menu_view )
            self.mm_item_toolbar.set_submenu( self.mm_menu_toolbar )
            self.mm_item_fontsize.set_submenu( self.mm_menu_fontsize )

            # Attach the callback functions to the activate signal
            self.mm_item_settings.connect( "activate", callbacks.settings, self)
            self.mm_item_about.connect( "activate", callbacks.about, self )
            self.mm_item_exit.connect( "activate", callbacks.delete_event, self )

            self.mm_item_new.connect( "activate" , callbacks.newrecord, self )
            self.mm_item_edit.connect( "activate" , callbacks.editrecord, self )
            self.mm_item_delete.connect( "activate" , callbacks.deleterecord, self )

            self.main_menu_item_fullscreen.connect( "toggled" , callbacks.main_fullscreen , self )

            self.mm_item_toolbar_main.connect( "toggled" , callbacks.main_toolbar , self )
            self.mm_item_toolbar_secondary.connect( "toggled" , callbacks.secondary_toolbar , self )
            self.mm_item_fontsize_x_small.connect( "toggled", callbacks.fontsize_x_small , self )
            self.mm_item_fontsize_small.connect( "toggled" , callbacks.fontsize_small , self )
            self.mm_item_fontsize_medium.connect( "toggled", callbacks.fontsize_medium , self )
            self.mm_item_fontsize_large.connect( "toggled" , callbacks.fontsize_large , self )

            FuelpadAbstractWindow.create_mainwin_menu( self , vbox )

        def enable_mainmenu_items( self ) :

            dbopen = self.config.db.is_open()
            self.mm_item_new.set_sensitive( dbopen )
            self.mm_item_edit.set_sensitive( dbopen )
            self.mm_item_delete.set_sensitive( dbopen )
            self.mm_item_monthly.set_sensitive( dbopen )
            self.mm_item_report.set_sensitive( dbopen )
            self.mm_item_close.set_sensitive( dbopen )
            self.mm_item_import.set_sensitive( dbopen )
            self.mm_item_export.set_sensitive( dbopen )

            FuelpadAbstractWindow.enable_mainmenu_items( self )

def main_loop ( ) :
    gtk.main()

