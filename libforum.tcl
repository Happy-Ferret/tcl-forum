# $Forum: libforum.tcl,v 1.17 2000/12/29 14:20:12 uri

proc forum_version {} {
    return 1.17
}

proc forum_link {args} {
    global env forum
    array set options $args
    set link $env(SCRIPT_NAME)?name=$forum(name)
    if [info exists options(cmd)] {
	append link ,cmd=$options(cmd)
    }
    if [info exists options(page)] {
	append link ,page=$options(page)
    } else {
	append link ,page=$forum(page)
    }
    if [info exists options(msgid)] {
	append link ,msgid=$options(msgid)
    } else {
	append link ,msgid=$forum(msgid)
    }
    if [info exists forum(session_id)] {
	append link ,session_id=$forum(session_id)
    }
    return $link
}

proc hebpipe {text} {
    global theme
    if !$theme(rtl) {
	return $text
    }
    set result ""
    foreach i [split $text \n] {
	lappend result [bidi $i]
    }
    return [join $result \n]
}

proc forum_format {text args} {
    global selfurl
    return [eval [list search_and_replace $text			\
		@NAME@ [forum name]				\
		@SELFURL@ $selfurl				\
		@VERSION@ [forum_version]			\
		@DESCRIPTION@ [forum description]]		\
		$args]
}

proc search_and_replace {text args} {
    foreach {i j} $args {
	set newtext ""
	while {[set k [string first $i $text]] != -1} {
	    append newtext [string range $text 0 [expr $k - 1]]$j
	    set text [string range $text [expr $k + [string length $i]] end]
	}
	set text $newtext$text
    }
    return $text
}

proc parse_condstr {text defs args} {
    set newtext ""
    while {[set k [string first "@IF " $text]] != -1} {
	set if_end [string first @ [string range $text [expr $k + 1] end]]
	set endif_place [string first @END@ [string range $text $k end]]
	set else_place [string first @ELSE@ [string range $text $k end]]
	if {$endif_place == -1} {
	    return [eval forum_format \$newtext\$text $args]
	}
	if {$else_place == -1 || $else_place > $endif_place} {
	    set else_place [expr $k + $endif_place]
	} else {
	    incr else_place $k
	}
	incr endif_place $k
	incr if_end $k
	set cond [string range $text [expr $k + 4] $if_end]
	if {[lsearch $defs [string toupper $cond]] != -1} {
	    set text_start [expr $if_end + 2]
	    set text_end [expr $else_place - 1]
	} else {
	    set text_start [expr $else_place + 6]
	    set text_end [expr $endif_place - 1]
	}
	append newtext [string range $text 0 [expr $k - 1]][string range $text $text_start $text_end]
	set text [string range $text [expr $endif_place + 5] end]
    }
    return [eval forum_format \$newtext\$text $args]
}

proc parse_query_str {text} {
    set counter 0
    set next_match [string first "%" $text]
    set outstr ""
    while { $next_match != -1 } {
        append outstr [string range $text $counter [expr $counter + $next_match -1]]
	if [catch {expr 0x[string range $text [expr $counter + $next_match + 1] [expr $counter + $next_match + 2]]} value] {
	    append outstr %
	} else {
	    append outstr [binary format c $value]
	    incr counter 2
	}
        set counter [expr $counter + $next_match + 1]
        set next_match [string first "%" [string range $text $counter end]]
    }
    return $outstr[string range $text $counter end]
}

proc time_format {time format} {
    global forum
    return [clock format [expr $time + [forum gmtdiff] * 3600] -format $format -gmt 1]
}

proc invalid {text} {
    global forum theme
    puts [search_and_replace $theme(invalid) @ERRORTEXT@ $text @VERSION@ [forum_version]]
    finish
}

proc load_theme {name} {
    global theme
    if ![file readable themes/$name.thm] {
	invalid "Unable to read theme data \"$name\""
    }
    set theme(rtl) 0
    set idx [open themes/$name.thm r]
    array set theme [read $idx]
    close $idx
    if $theme(rtl) {
	load ./bidi.so
    }
}

proc load_forum {name} {
    global forum msgs
    set allowedchars "abcdefghijlmnopqrstuvwxyz0123456789-_"
    foreach i [split $name ""] {
	if {[string first $i $allowedchars] == -1} {
	    invalid "Invalid forum name \"$name\": name contains invalid chars"
	}
    }
    init_db 							\
		html_sep	"&nbsp;&nbsp;&nbsp;"		\
		theme	 	default				\
		message_line	"@TEXT@<br>"			\
		pagesize	20				\
		gmtdiff		0				\
		newmsg_time	86000				\
		name		"Unnamed forum"			\
		description	""				\
		password	""
    if ![load_db $name] {
	invalid "Invalid forum name \"$name\": forum does not exists"
    }
}

proc init_selfurl {} {
    global env selfurl
    set selfurl $env(SCRIPT_NAME)
    if [info exists env(QUERY_STRING)] {
        append selfurl ?$env(QUERY_STRING)
    }
}

proc finish {} {
    finish_db
    exit
}
