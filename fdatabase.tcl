proc fdb_read {fname} {
	set fidx [open $fname]
	set data [read $fidx]
	foreach i [lindex $data 0] j [lrange $data 1 end] {
	    if {[string index $i 0] == "@"} {
		global [string range $i 1 end]
		array set [string range $i 1 end] $j
	    } else {
		global $i
		set $i $j
	    }
	}
	close $fidx
}

proc fdb_save {fname arrays} {
	set fidx [open $fname w]
	puts $fidx [list $arrays]
	foreach i $arrays {
	    if {[string index $i 0] == "@"} {
		global [string range $i 1 end]
		puts $fidx [list [array get [string range $i 1 end]]]
	    } else {
		global $i
		puts $fidx [list [set $i]]
	    }
	}
	close $fidx
}
