# $Forum: admin.tcl,v 1.17 2000/12/29 14:06:12 uri

proc check_admin {} {
    global forum env
    if [info exists forum(session_id)] {
	set ipmatch 0
	catch {
	    set atime [file atime sessions/$forum(session_id)]
	    set f [open sessions/$forum(session_id) r]
	    set ip [gets $f]
	    if {$env(REMOTE_ADDR) == $ip} {
		set ipmatch 1
	    }
	    close $f
	}
	if !$ipmatch {
	    invalid "Invalid session #$forum(session_id)"
	}
	if {$atime + 1800 < [clock seconds]} {
	    invalid "Session expired"
	}
	set forum(admin) 1
    }
    if [info exists forum(upassword)] {
	if ![string length [forum password]] {
	    invalid "Forum is not administrativable"
	}
	if {$forum(upassword) == [forum password]} {
	    set forum(session_id) [expr rand() * [clock seconds]]
	    if [catch {
		set f [open sessions/$forum(session_id) w]
		puts $f $env(REMOTE_ADDR)
		close $f
	    }] {
		invalid "Unable to create a new administration session"
	    }
	    set forum(admin) 1
	} else {
	    invalid "Bad password"
	}
    }
}
