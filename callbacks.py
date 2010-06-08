
# ToDo : update_record_model not implemented

# NOTE : Moved config into pui
import configuration

import wizard

import utils

import gtk , gobject
try :
    import hildon
except :
    hildon = False


delay_quit_interval = 10

def delete_event ( widget , event , data=None ) :
  locator = None
  if data :
    if data.config.db.locator :
      locator = data.config.db.locator 
  else :
    if event.config.db.locator :
      locator = event.config.db.locator 
  if locator :
    if locator.timeout_handler :
      gobject.timeout_add( delay_quit_interval * 1000 , mainloop_exit , locator )
    else :
      gtk.main_quit()
  else :
    gtk.main_quit()

def mainloop_exit ( locator ) :
  if locator.timeout_handler :
    return True
  gtk.main_quit()
  return False

def destroy_event ( widget , event , data=None ) :
  widget.destroy()


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
        editwin = wizard.FuelpadEdit( pui.config , 1 )
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


