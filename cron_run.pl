#!/usr/bin/perl

use strict;
use warnings;
use IO::Socket;
use File::Basename;
my $dirname = dirname(__FILE__);
print "Dir name: $dirname\n";

my $off_peak_start = 19;
my $off_peak_end = 7;
my $xmrig_path = `readlink -f $dirname/xmrig`; chomp $xmrig_path;
print "Resolved xmrig path $xmrig_path\n";
#19:00 - midnight - 11:00 is off peak
#weekends is off peak by default

my $max_temp = 24;
my $sensor_to_home_bias = 1;

sub if_temp_too_high {
	my $socket = new IO::Socket::INET (   
	PeerAddr => '192.168.1.185',   
	PeerPort => '48910',   
	Proto => 'tcp',   
	);   
	if(not $socket) {
		print "Failed to connect\n";
		return 0;	
	}

	my $data = "temp";
	chomp $data;
	print $socket $data;
	my $buffer = "";
	$socket->recv($buffer, 1024);
	close $socket;
	
	if($buffer eq "") {
		print "buffer is empty, maybe it just during midnight\n";
		return 0;
	}
	my $temp = $buffer - $sensor_to_home_bias;
	if ($temp > $max_temp) {
		print "Too hot, we are at $temp\n";
		return 1;
	}
	return 0;
}

sub should_run {
	# if too warm the dont run
	if(if_temp_too_high()) {
		return 0;
	}

	my $now = shift @_;
	my $run = 0;
	my $day = `date '+%A' -d \@$now`;
	chomp $day;
	# check if today is weekends
	if ($day eq "Sunday" or $day eq "Saturday") {
		$run = 1;
	} else {
		my $hour = `date +%-H -d \@$now`; chomp $hour;
		if ($hour >= $off_peak_end and $hour < $off_peak_start) {
			$run = 0;
		} else {
			$run = 1;
		}
	}
	return $run;
}

sub get_xmrig_pid {
	my @pid = `ps aux | egrep $xmrig_path | egrep -v grep | egrep -v perl | awk '{print \$2}'`;
	chomp @pid;
	if(scalar @pid > 1) {
		my $i = 0;
		foreach my $pid_ (@pid) {
			if($i != 0) {
				`sudo kill $pid_`;
				print "Kill multiple xmrig $pid_\n";
			}
			$i++;
		}
		return $pid[0];
	}
	if(scalar @pid < 1) {
		return -2;
	}
	return $pid[0];
}

my $now = `date +%s`; chomp $now;
my $xmrig_ps = get_xmrig_pid();

if(should_run($now)) {
	if ($xmrig_ps < 0){
		print "Restart the process\n";
		my $xmrig = fork();
		if($xmrig == 0) {
        		`$xmrig_path &`;
        		exit;
		}
		print "Restarted process: $xmrig\n";
	} else {
		print "Keep $xmrig_ps running\n";
	}
} else  {
	if ($xmrig_ps > 0) {
		print "Kill the process $xmrig_ps\n";
		`kill -9 $xmrig_ps`;
	} else {
		print "Nothing need to do\n";
	}
}
