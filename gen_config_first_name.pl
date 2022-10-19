#!/usr/bin/perl

use strict;
use warnings;

my $config_template = "./template_config.json";
my $hostname = `hostname`; chomp $hostname;
my $template = `cat $config_template | sed 's/HOSTNAME/$hostname/g' > ./config.json`;

print $template;

