#! /bin/sh
# $Forum: forum.cgi,v 1.17 2000/12/29 14:06:15 uri

# restart using tclex, exit \
/usr/local/bin/tclex $0 2>/dev/stdout ; exit

set default_theme default

source libforum.tcl
source forumdb.tcl
source admin.tcl

proc read_reply_request {isedit} {
    global forum theme qdata
    if ![db_writable] {
	invalid "Can't write reply to forum \"$forum(name)\": forum is read-only"
    }
    set msg(sender) ""
    set msg(sender_email) ""
    set msg(subject) ""
    set msg(text) ""
    foreach i $qdata {
	set i [split $i =]
	set entry [lindex $i 0]
	set val [join [split [parse_query_str [join [split [join [lrange $i 1 end] =] +] " "]] "\r"] ""]
	switch -glob -- $entry {
	    url? {
		set msg($entry) [search_and_replace $val \" \\\" < "&lt;" > "&gt;"]
	    }
	    sender - sender_email - subject - text {
		set msg($entry) [search_and_replace [hebpipe $val] & "&amp;" < "&lt;" > "&gt;"]
	    }
	    default {
		set msg($entry) [search_and_replace $val & "&amp;" < "&lt;" > "&gt;"]
	    }
	}
    }
    if ![string length [string trim $msg(subject)]] {
	invalid "Bad subject name: must be at least 1 char"
    }
    if ![string length [string trim $msg(sender)]] {
	invalid "Bad sender name: must be at least 1 char"
    }
    foreach i [array names msg url?] {
	set linkid [string index $i 3]
	if ![info exists msg(url${linkid}_desc)] continue
	if {$msg(url${linkid}_desc) == "" || $msg($i) == ""} continue
	lappend links [list $msg($i) [hebpipe $msg(url${linkid}_desc)]]
    }
    if $isedit {
	# links edit isn't fully supported yet, so let's restore original links
	set links [message $forum(msgid) links]
    }
    lappend msg_values 		\
	sender $msg(sender)	\
        email $msg(sender_email) \
        text $msg(text)		\
	links $links		\
	subject $msg(subject)
    if $isedit {
        modify_message $forum(msgid) $msg_values
	return [do_getmsg]
    }
    lappend msg_values time [clock seconds]
    add_message $forum(msgid) $msg_values
    set forum(page) 1
    puts [forum_format $theme(msg_added)					\
	    @LINKFORUM@ [forum_link cmd list]				\
	    @LINKVIEW@ [forum_link cmd view]]
}

proc do_getreplypage {} {
    global forum theme
    puts [format_forum_msg $forum(msgid) $theme(msg_new)		\
	    @LINKPOST@ [forum_link cmd postreply msgid $id]		\
	 ]
}

proc format_forum_msg {id html args} {
    global forum spacing theme
    if [info exists forum(defs)] {
	set defs $forum(defs)
    } else {
	set defs ""
    }
    if ![info exists spacing] {
	set spacing ""
    }
    if $forum(admin) {
	lappend defs ADMIN
    }
    if [llength [msg_list $id]] {
	lappend defs GOTREPLIES
    }
    set linklist [message $id links]
    set links ""
    if [llength $linklist] {
	lappend defs GOTLINKS
	foreach i $linklist {
	    append links [forum_format $theme(msg_link) @LINK@ [lindex $i 0] @LINKDESC@ [lindex $i 1]]\n
	} 
    }
    unset linklist
    if {$forum(msgid) == 0} {
	lappend defs ROOTMSGID
    }
    set email [message $id email]
    if [string length $email] {
	lappend defs EMAILSET
    }
    set text ""
    foreach i [split [message $id text] \n] {
	append text [search_and_replace [forum message_line] @TEXT@ $i]\n
    }
    if [info exists theme(icons)] {
	set text [eval search_and_replace \$text $theme(icons)]
    }
    set time [message $id time]
    if {[clock seconds] - $time < [forum newmsg_time]} {
	lappend defs NEW
    }
    if {![string length [string trim [message $id text] " \t\r\n"]] && ![llength $links]} {
	lappend defs NOCONTENTS
    }
    return [eval {parse_condstr $html $defs				\
	    @TEXT@ $text						\
	    @PAGE@ $forum(page)						\
	    @TIME@ [time_format $time %R]				\
	    @DATE@ [time_format $time %e/%m/%Y]				\
	    @LINKS@ $links						\
	    @EMAIL@ $email						\
	    @SENDER@ [message $id sender]				\
	    @SUBJECT@ [message $id subject]				\
	    @SPACING@ $spacing						\
	    @FOLLOWUPS@ [get_msg_followups $id]				\
	    @LINKADD@ [forum_link cmd reply]				\
	    @LINKFORUM@ [forum_link]					\
	    @LINKVIEW@ [forum_link cmd view msgid $id]			\
	    @LINKREPLY@ [forum_link cmd reply msgid $id]		\
	    @LINKDELETE@ [forum_link cmd del msgid $id]			\
	    @LINKEDIT@ [forum_link cmd edit msgid $id]			\
	    @MSGID@ $id							\
	    @MSGCOUNT@ [msg_count]					\
	    @PAGECOUNT@ $forum(pagecount)} $args			]
}

proc get_msg_followups {msgid} {
    global msglevel theme forum spacing
    if ![info exists msglevel] {
	set msglevel 0
    }
    set my_spacing ""
    for {set i 0} {$i < $msglevel} {incr i} {
	append my_spacing [forum html_sep]
    }
    set result ""
    incr msglevel
    foreach i [msg_list $msgid] {
	set spacing $my_spacing
	append result [format_forum_msg $i $theme(forum_message)]
    }
    incr msglevel -1
    return $result
}

proc format_forum_html {html defs} {
    global forum
    return [parse_condstr $html $defs 					\
	    @PAGE@ $forum(page)						\
	    @LINKADD@ [forum_link cmd reply msgid 0]			\
	    @LINKPREV@ [forum_link page [expr $forum(page) - 1]]	\
	    @LINKNEXT@ [forum_link page [expr $forum(page) + 1]]	\
	    @MSGCOUNT@ [msg_count]					\
	    @PAGECOUNT@ $forum(pagecount)				]
}

proc do_getmsg {} {
    global forum theme
    if !$forum(msgid) {
        invalid "Message #0 doesn't exist."
    }
    puts [format_forum_msg $forum(msgid) $theme(msg_view)]
}

proc do_getlist {} {
    global forum msglevel forum theme spacing
    set defs ""
    if {($forum(page) > $forum(pagecount) || $forum(page) < 1) && [llength [msg_list]]} {
	invalid "Invalid page #$forum(page)"
    } elseif {$forum(page) < $forum(pagecount)} {
	lappend defs NEXTPAGE
    }
    if {$forum(page) > 1} {
	lappend defs PREVPAGE
    }
    puts [format_forum_html $theme(forum_start) $defs]
    set msglist [msg_list]
    for {set i [expr ($forum(page) - 1) * [forum pagesize]]} {$i <= [expr $forum(page) * [forum pagesize] - 1]} {incr i} {
	if {[set msgid [lindex $msglist [expr [llength $msglist] - $i - 1]]] != ""} {
	    set msglevel 1
	    set spacing ""
	    puts [format_forum_msg $msgid $theme(forum_message)]
	}
    }
    puts [format_forum_html $theme(forum_end) $defs]
}

proc rec_deletemsg {id} {
    global msgs
    incr msgs(count) -1
    if [info exists msgs($id,replies)] {
	foreach i $msgs($id,replies) {
	    rec_deletemsg $i
	}
    }
    foreach i [array names msgs $id,*] {
	unset msgs($i)
    }
}

proc do_deletemsg {} {
    global forum
    if !$forum(admin) {
	invalid "Permission denied"
    }
    if {$forum(msgid) == 0} {
	invalid "Unable to delete the root message #0"
    }
    if ![db_writable] {
	invalid "Can't delete message #$forum(msgid) from forum \"$forum(name)\": forum is read-only"
    }
    delete_message $forum(msgid)
    do_getlist
}

proc do_editmsg {} {
    global forum theme
    set forum(defs) EDIT
    set forum(edit) 1
    set id $forum(msgid)
    puts [format_forum_msg $id $theme(msg_edit)				\
	    @EDITTEXT@ [hebpipe [message $id text]]			\
	    @EDITSENDER@ [hebpipe [message $id sender]]			\
	    @EDITSUBJECT@ [hebpipe [message $id subject]]		\
	    @EDITEMAIL@ [hebpipe [message $id email]]			\
	    @LINKPOST@ [forum_link cmd postedit msgid $id]		\
	 ]
}

proc do_editsettings {} {
    global qdata forum theme
    if ![db_writable] {
	invalid "Can't write reply to forum \"$forum(name)\": forum is read-only"
    }
    foreach i $qdata {
	set i [split $i =]
	set entry [lindex $i 0]
	set val [join [split [parse_query_str [join [split [join [lrange $i 1 end] =] +] " "]] "\r"] ""]
	if {[string range $entry 0 3] = "set_"} {
	    lappend newvalues [string range $entry 4 end] $val
	}
    }
    forum_set $newvalues
    foreach {i j} [forum_get] {
	lappend values @[string toupper $i]@ [search_and_replace $j & "&amp;" < "&lt;" > "&gt;"]
    }
    puts [eval {search_and_replace $theme(prefs_edit) @VERSION@ [forum_version]} $values]
}

proc forum_process_query {query} {
    global forum default_theme qdata
    set qdata [split $query "&;,"]
    set cmd		"list"
    set forum(name)	"default"
    set forum(msgid)	0
    set forum(admin)	0
    set forum(page)	1
    foreach i $qdata {
	set i [split $i =]
	set name [lindex $i 0]
	set val [join [lrange $i 1 end] =]
	switch -- [string tolower $name] {
	    cmd {set cmd $val}
	    page {set forum(page) $val}
	    name {set forum(name) [string tolower $val]}
	    msgid {set forum(msgid) $val}
	    password {set forum(upassword) $val}
	    session_id {set forum(session_id) $val}
	}
    }
    set digits "1234567890"
    foreach i [split $forum(page) ""] {
	if {[string first $i $digits] == -1} {
	    invalid "Bad page number \"$forum(page)\": invalid number"
	}	
    } 
    foreach i [split $forum(msgid) ""] {
	if {[string first $i $digits] == -1} {
	    invalid "Bad message id \"$forum(msgid)\": invalid number"
	}	
    }
    load_forum $forum(name)
    if {[forum theme] != $default_theme} {
	load_theme [forum theme]
    }
    if {$forum(msgid) != 0 && ![string length [message $forum(msgid) time]] && $cmd !="list"} {
	invalid "Message #$forum(msgid) doesn't exist"
    }
    check_admin
    set forum(pagecount) [expr ([llength [msg_list]] + [forum pagesize] - 1) / [forum pagesize]]
    switch -- $cmd {
        "view"		{do_getmsg}
        "reply"		{do_getreplypage}
	"del"		{do_deletemsg}
	"edit"		{do_editmsg}
	"postreply"	{read_reply_request 0}
	"postedit"	{read_reply_request 1}
	"settings"	{do_editsettings}
        "list"		{do_getlist}
	default		{invalid "Unknown command \"$cmd\""}
    }
}

puts "Content-Type: text/html\n"

load_theme $default_theme

if ![info exists env(REQUEST_METHOD)] {
    invalid "No request method (?)"
}

if ![info exists env(SCRIPT_NAME)] {
    invalid "No script name (?)"
}

if ![info exists env(REMOTE_ADDR)] {
    invalid "No remote addr (?)"
}

init_selfurl

if {$env(REQUEST_METHOD) == "POST"} {
    if [info exists env(QUERY_STRING)] {
	forum_process_query [read stdin],$env(QUERY_STRING)
    } else {
	forum_process_query [read stdin]
    }
} elseif {$env(REQUEST_METHOD) == "GET"} {
    if [info exists env(QUERY_STRING)] {
	forum_process_query $env(QUERY_STRING)
    } else {
    invalid "No query"
    }
} else {
    invalid "Unknown request method $env(REQUEST_METHOD)"
}

finish
