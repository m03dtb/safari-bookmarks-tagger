# Notizen  Aufbau 


1.
  -> fn call_from: **Class MainWindow** 
      [[x+y -> mydict]]

  create: {list mylist: list: mytags } erstellt 
  -> fn call: *return_input_list* 
  -> fn return: **mydict**              || -> used_in: class Table 


2. a) zu Tabelle: 
    [[mydict.key -> table.0=mydict.key, table.1=mydict.value]]
  
fn_call_from: MainWindow: as "self.table" 
-> fn call: class Table(mydict, line=None)

  -> fn_from: "self.mydict" ->           
  -> fn return: "all_tags_full" 
  -> fn return: "set_of_tags"             || -> used_in:  2. b) 

  -> fills table "self.table"
      with: table[[0]] = mydict:str ["Name"]
            table[[1]] = mydict:list [["Tags"]]


2. b) CLASS: Table:
- fn_call: **get_all_tags**:
-> sorted("set_of_tags") 

- fn_call: **filter_table**             || -> called_by: LineEdit.on_text_changed 
-> filters out entries in Table.table where not all tags in table[[1]] contained 


3. CLASS: LineEdit

** FOCUS_EVENTS: 
  - focusInEvent:

  - focusOutEvent:

** KEY_PRESS EVENTS:
  1. textChanged  || -> calls: on_text_changed 
  2. return_pressed || -> calls: on_return_pressed
  3. dropdown.itemActivated || -> calls: on_dropdown_item_activated
                                || -> calls: on_return_pressed  
      [[ensures]: "Enter" only works on dropdown_list]


  1. -> on_text_changed:
  
  ***fn***: on_return_pressed:
    [[takes item chosen by *return_pressed*] and [does string stuff]]
    -> "string stuff":
      - Ex.: SearchBar: "mytag1, myt" -> [keypress_enter] -> 
          "mytag1, myt" ->  SEP: "mytag1, || myt"  -->  DROP_TILL_COMMA_INCL:
          -> REST: "mytag1" (Dropped: ",myt") -> 
          -> ADD: "," -> "mytag1,"
          -> ADD: tag+"," -> "mytag1,mytag2" 
          [via: "RPARTITION"]

