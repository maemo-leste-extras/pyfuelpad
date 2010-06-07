
# ToDo : update_record_model not implemented

# NOTE : Moved config into pui
import configuration

import combos

import utils

import gtk
try :
    import hildon
except :
    hildon = False


def delete_event ( widget , event , data=None ) :
  gtk.main_quit()

def destroy_event ( widget , event , data=None ) :
  widget.destroy()


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

def get_store_and_iter ( model , view , iter , storeiter , config ) :
  sortable = view.get_model()
  store = sortable.get_model()
#  sortable=gtk_tree_view_get_model(GTK_TREE_VIEW(view));
#  filter=gtk_tree_model_sort_get_model(GTK_TREE_MODEL_SORT(sortable));
#  *store = GTK_LIST_STORE(gtk_tree_model_filter_get_model(GTK_TREE_MODEL_FILTER(filter)));
  if model is None or iter is None :
    storeiter = None
  else :
    print "MODEL",dir(model)
    print "SORT",dir(sortable)
    raise Exception ("Not implemented")
    # model.sort_convert_iter_to_child_iter(GTK_TREE_MODEL_SORT(model), &filteriter, iter);
    # filter.convert_iter_to_child_iter(GTK_TREE_MODEL_FILTER(filter), storeiter, &filteriter);
  return store

def ui_update_row_data ( store , iter , config , date, km, trip, fill, consum, price, service, oil, tires, notes , id , visible ) :

  if date :
    userdate = utils.convdate( config.dateformat , None , date )
    store.set( iter, configuration.column_dict['DAY'],  userdate)

  priceperlitre = -1
  if fill > 0 :
    priceperlitre = price / fill

  if not km < 0.0 : store.set( iter, configuration.column_dict['KM'], config.SIlength2user(km) )
  if not trip < 0.0 : store.set( iter, configuration.column_dict['TRIP'], config.SIlength2user(trip) )
  if not fill < 0.0 : store.set( iter, configuration.column_dict['FILL'], config.SIvolume2user(fill) )
  if not consum < 0.0 : store.set( iter, configuration.column_dict['CONSUM'], config.doubleornothing(config.SIconsumption2user(consum)) )
  if not price < 0.0 : store.set( iter, configuration.column_dict['PRICE'], price )
  if not ( price < 0.0 or trip < 0.0 ) : store.set( iter, configuration.column_dict['PRICEPERTRIP'], config.doubleornothing(price/config.SIlength2user(trip)) )
  if not priceperlitre < 0.0 : store.set( iter, configuration.column_dict['PRICEPERLITRE'], config.doubleornothing(config.SIppl2user(priceperlitre)) )
  if not service < 0.0 : store.set( iter, configuration.column_dict['SERVICE'], service )
  if not oil < 0.0 : store.set( iter, configuration.column_dict['OIL'], oil )
  if not tires < 0.0 : store.set( iter, configuration.column_dict['TIRES'], tires )
#                                /*                      INSURANCE, sqlite3_column_double(ppStmtRecords,5), */
#                                /*                      OTHER, sqlite3_column_double(ppStmtRecords,5), */
  if not consum < 0.0 : store.set( iter, configuration.column_dict['CO2EMISSION'], 0.0) #JP# config.SIemission2user(calc_co2_emission(consum,currentcar)) )
  if notes != None : store.set( iter, configuration.column_dict['NOTES'], notes)
  store.set( iter, configuration.column_dict['ID'], id, configuration.column_dict['VISIBLE'], visible);

def add_record_response ( widget , event , editwin , pui ) :

  view , config = pui.view , pui.config

  if not config.db.is_open() :
       widget.destroy()
       return

  # NOTE : response from hildon wizard is an unexpected value
  if event == gtk.RESPONSE_ACCEPT or event == 2 :

#    if (carchanged)
#      update_car_changed(pui);

    if False : #  hildon : JP
      if maemo5 :
        _date = editwin.entrydate.get_date() # &year, &month, &day);  /* Month is betweewn 0 and 11 */
        month += 1
      else :
        _date = editwin.entrydate.get_date() #  &year, &month, &day);
      print "DATE:",_date
      date = "%d-%02d-%02d" % _date
    else :
      date = editwin.entrydate.get_text()
    date = utils.date2sqlite( config.dateformat , date )

    km  = config.user2SIlength( float( editwin.entrykm.get_text() or "-1" ) )
    trip = config.user2SIlength( float( editwin.entrytrip.get_text() or "-1" ) )
    fill  = config.user2SIvolume( float( editwin.entryfill.get_text() or "-1" ) )
    if editwin.entryprice :
        price = float( editwin.entryprice.get_text() or "-1" )
        service = float( editwin.entryservice.get_text() or "-1" )
        oil = float( editwin.entryoil.get_text() or "-1" )
        tires = float( editwin.entrytires.get_text() or "-1" )
        notes = editwin.entrynotes.get_text()
    else :
        price = service = oil = tires = 0
        notes = ""

    if editwin.buttonnotfull.get_active() :

	# For this record
	consum = 0.0
	print "DEQUENO"

#	# Find next full record 
#	fullid=db_find_next_full(km, &fullfill, &fullkm);
#	if (fullid>=0) {
# ...
#	}
#	else
#	  PDEBUG("Full fill not found\n");
#      }
    else :
      # Find if there are any not full fills before this record
      fullfill , fullkm = config.db.find_prev_full( km )

      consum = (fullfill+fill)/(fullkm+trip)*100;

    # This is verified also within add_record method
    if config.db.is_open() :
	recordid = config.db.add_record(date, km, trip, fill, consum, price, service, oil, tires, notes)
	if recordid : # record succesfully inserted
	  store = get_store_and_iter(None, view, None, None, config)
	  storeiter = store.append()
	  ui_update_row_data(store, storeiter, config, date, km, trip, fill, consum, price, service, oil, tires, notes, recordid, True)
          pui.update_totalkm()

    widget.destroy()

  elif event == gtk.RESPONSE_REJECT :
     widget.destroy()


def callback_recordactivated ( view , path , col , pui ) :
  model = view.get_model()
  iter = model.get_iter(path) 
  if iter :
    callback_editrecord(None, pui)

def callback_editrecord ( action , pui ) :
   # NOT EDITABLE
   pass

def callback_newrecord ( action, pui ) :

    header = ( "Add a new record" , )

    if pui.config.db.is_open() :
        editwin = FuelpadEdit( pui.config , 1 )
        if hildon :
            dialog = hildon.WizardDialog( pui , header[0] , editwin )
        else :
            dialog = gtk.Dialog( header[0],
                                 pui,
                                 gtk.DIALOG_MODAL,
                                 ( gtk.STOCK_OK, gtk.RESPONSE_ACCEPT,
                                   gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT
                                   )
                                 )
            dialog.vbox.pack_start(editwin , True, True, 0)
        dialog.connect( "response", add_record_response, editwin , pui )

        #if libhelp :
        #    help_dialog_help_enable(GTK_DIALOG(dialog),
        #                                   HELP_ID_ADDRECORD,
        #                                   pui->app->osso);


    else :
        dialog = gtk.Dialog( header[0],
                             pui ,
                             gtk.DIALOG_MODAL ,
                             ( gtk.STOCK_OK, gtk.RESPONSE_REJECT )
                             )

        label = gtk.Label( "Can't access database - adding records not possible" )
        dialog.vbox.pack_start( label, True, True, 5)
        label.show()

        dialog.connect( "response", destroy_event , None )

    dialog.show_all()


# Actions for carcombo item done
def update_car_changed ( pui ) :
  pui.config.save()
  pui.view.update( pui )

def car_apply_cb ( widget , window ) :

    update_car_changed( window )

    # Update the next event estimates
    #window.alarmview = create_alarmview_and_model( window )
    #window.warn = update_next_event( window.alarmview.get_model() )
    #update_reminder_toolbutton (window, window.warn);

    window.toolbar_show_hide()


# BUG : Under font change, labels are not rescaled
# Font scaling done
def update_font_scale ( view , fontsize ) :
  view.hide()
  for info in configuration.column_info :
    if info[6] : 
      col = view.get_column( info[0] )
      attrs = configuration.font_attrs( fontsize , col.get_widget() )
      for renderer in col.get_cell_renderers() :
        renderer.set_property( "scale" , configuration.fontscalefactors[fontsize] )
  view.show()

def cb_fontsize_x_small ( action , pui ) :
  pui.config.fontsize = configuration.XSMALL;
  update_font_scale( pui.view , pui.config.fontsize )
  update_record_model( pui )

def cb_fontsize_small ( action, pui ) :
  pui.config.fontsize = configuration.SMALL;
  update_font_scale( pui.view , pui.config.fontsize )

def cb_fontsize_medium ( action , pui ) :
  pui.config.fontsize = configuration.MEDIUM;
  update_font_scale( pui.view , pui.config.fontsize )

def cb_fontsize_large ( action , pui ) :
  pui.config.fontsize = configuration.LARGE;
  update_font_scale( pui.view , pui.config.fontsize )


# Toolbars toggles done
def cb_main_fullscreen ( action , pui ) :
  main_window_fullscreen(pui)
  pui.main_menu_item_fullscreen.set_active( pui.mainfullscreen )

def cb_main_toolbar ( action , pui ) :
  pui.config.main_toolbar_visible = not pui.config.main_toolbar_visible;
  pui.toolbar_show_hide()

def cb_secondary_toolbar ( action , pui ) :
  pui.config.secondary_toolbar_visible = not pui.config.secondary_toolbar_visible;
  pui.toolbar_show_hide()


