# $Forum: forumdb.tcl,v 1.17 2000/12/29 14:06:20 uri

source fdatabase.tcl

proc init_db {args} {
    global db_forum
    foreach {i j} $args {
	set db_forum($i) $j
    }
}

proc finish_db {} {
}

proc load_db {fname} {
    global db_forum db_fname
    if ![file readable forum/$fname.fdb] {
	return 0
    }
    set db_fname forum/$fname.fdb
    fdb_read $db_fname
    return 1
}

proc db_writable {} {
    global db_fname
    return [file writable $db_fname]
}

proc forum {entry} {
    global db_forum
    if [info exists db_forum($entry)] {
	return $db_forum($entry)
    } else {
	return ""
    }
}

proc message {id entry} {
    global db_messages
    if [info exists db_messages($id,$entry)] {
	return $db_messages($id,$entry)
    } else {
	return ""
    }
}

proc add_message {parent values} {
    global db_messages db_fname
    if ![info exists db_messages(count)] {
	set db_messages(count) 1
    } else {
	incr db_messages(count)
    }
    if ![info exists db_messages(nextid)] {
	set db_messages(nextid) 1
    }
    set newid $db_messages(nextid)
    incr db_messages(nextid)
    lappend db_messages($parent,children) $newid
    set db_messages($newid,parent) $parent
    foreach {i j} $values {
	set db_messages($newid,$i) $j
    }
    fdb_save $db_fname {@db_forum @db_messages}
    return $newid
}

proc modify_message {id values} {
    global db_messages db_fname
    if ![info exists db_messages($id,time)] return
    foreach {i j} $values {
	set db_messages($id,$i) $j
    }
    fdb_save $db_fname {@db_forum @db_messages}
}

proc rec_delete_msg {id} {
    global db_messages
    if [info exists db_messages($id,children)] {
	foreach i $db_messages($id,children) {
	    rec_delete_msg $i
	}
    }
    foreach i [array names db_messages $id,*] {
	unset db_messages($i)
    }
    incr db_messages(count) -1
}

proc delete_message {id} {
    global db_messages db_fname
    if ![info exists db_messages($id,parent)] return
    set parent $db_messages($id,parent)
    rec_delete_msg $id
    if [info exists db_messages($parent,children)] {
	set place [lsearch $db_messages($parent,children) $id]
	if {$place != -1} {
	    set db_messages($parent,children) [lreplace $db_messages($parent,children) $place $place]
	}
    }
    fdb_save $db_fname {@db_forum @db_messages}
}

proc msg_count {} {
    global db_messages
    return $db_messages(count)
}

proc msg_list {{id 0}} {
    global db_messages
    if [info exists db_messages($id,children)] {
	return $db_messages($id,children)
    } else {
	return ""
    }
}
