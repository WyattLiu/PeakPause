#!/usr/bin/perl

use strict;
use warnings;
use IO::Socket;
use File::Basename;
my $dirname = dirname(__FILE__);
print "Dir name: $dirname\n";

my $on_peak_temp = 20;
my $mid_peak_temp = 25;
my $weekend_off_peak_temp = 26;
my $ulo = 28;

my %hour_map_week_day = (
	0 => $ulo,
	1 => $ulo,
	2 => $ulo,
	3 => $ulo,
	4 => $ulo,
	5 => $ulo,
	6 => $ulo,
	7 => $mid_peak_temp,
	8 => $mid_peak_temp,
	9 => $mid_peak_temp,
	10 => $mid_peak_temp,
	11 => $mid_peak_temp,
	12 => $mid_peak_temp,
	13 => $mid_peak_temp,
	14 => $mid_peak_temp,
	15 => $mid_peak_temp,
	16 => $on_peak_temp,
	17 => $on_peak_temp,
	18 => $on_peak_temp,
	19 => $on_peak_temp,
	20 => $on_peak_temp,
	21 => $mid_peak_temp,
	22 => $mid_peak_temp,
	23 => $ulo
);

my %hour_map_weekends = (
	0 => $ulo,
	1 => $ulo,
	2 => $ulo,
	3 => $ulo,
	4 => $ulo,
	5 => $ulo,
	6 => $ulo,
	7 => $weekend_off_peak_temp,
	8 => $weekend_off_peak_temp,
	9 => $weekend_off_peak_temp,
	10 => $weekend_off_peak_temp,
	11 => $weekend_off_peak_temp,
	12 => $weekend_off_peak_temp,
	13 => $weekend_off_peak_temp,
	14 => $weekend_off_peak_temp,
	15 => $weekend_off_peak_temp,
	16 => $weekend_off_peak_temp,
	17 => $weekend_off_peak_temp,
	18 => $weekend_off_peak_temp,
	19 => $weekend_off_peak_temp,
	20 => $weekend_off_peak_temp,
	21 => $weekend_off_peak_temp,
	22 => $weekend_off_peak_temp,
	23 => $ulo
);

my $xmrig_path = `readlink -f $dirname/xmrig`; chomp $xmrig_path;
print "Resolved xmrig path $xmrig_path\n";

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
	my $temp = $buffer;
	my $max_temp = shift @_;
	print "Current max_temp is $max_temp\n";
	if ($temp > $max_temp) {
		print "Too hot, we are at $temp\n";
		return 1;
	}
	print "Good temp: $temp\n";
	return 0;
}

sub should_run {
	my $now = shift @_;
	my $run = 0;
	my $day = `date '+%A' -d \@$now`;
	chomp $day;
	my $temp = 0;
	# check if today is weekends
	my $hour = `date +%-H -d \@$now`; chomp $hour;
	if ($day eq "Sunday" or $day eq "Saturday") {
		$temp = $hour_map_weekends{$hour};
	} else {
		$temp = $hour_map_week_day{$hour};
	}
	# if too warm the dont run
	if(if_temp_too_high($temp)) {
		return 0;
	}
	return 1;
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
        		`$xmrig_path > $xmrig_path.log &`;
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
