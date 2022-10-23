#!/usr/bin/perl

use strict;
use warnings;
use IO::Socket;

my $off_peak_start = 19;
my $off_peak_end = 7;
my $xmrig_path = "./xmrig";
#19:00 - midnight - 11:00 is off peak
#weekends is off peak by default

my $max_temp = 27;
my $sensor_to_home_bias = 3;

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
		return -1;
	}
	if(scalar @pid < 1) {
		return -2;
	}
	return $pid[0];
}
my $base_date = `date +%s`; chomp $base_date;
my $tests = 10;
while($tests) {
	my $test_date = $base_date + int(rand(7*24*3600));
	my $result = should_run($test_date);
	my $str = `date -d \@$test_date`; chomp $str;
	print "$str: $result\n";
	$tests--;
}

my $xmrig = fork();
if($xmrig == 0) {
	`$xmrig_path`;
	exit;
}

my $run = 1;

while(1) {
	my $now = `date +%s`; chomp $now;
	if(should_run($now)) {
		if($run == 1) {
			print "Keep the process running: $xmrig\n";
		} else {
			print "Restart the process\n";
			$xmrig = fork();
			if($xmrig == 0) {
        			`$xmrig_path`;
        			exit;
			}
			print "Restarted process: $xmrig\n";
			$run = 1;
		}
	} else  {
		if($run == 1) {
			print "Kill the process $xmrig\n";
			`kill -9 $xmrig`;
			my $pid = get_xmrig_pid();
			`kill -9 $pid`;
			$run = 0;
		} else {
			print "Waiting for restart moment\n";
		}
	}
	my $xmrig_ps = get_xmrig_pid();
	print "Now is $now, xmrig running at $xmrig_ps\n";
	if($xmrig_ps == -1) {
		exit;
	}
	if($xmrig_ps == -2) {
		$run = 0;
	}
	sleep(10);
}
