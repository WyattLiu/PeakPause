# PeakPause
This is a remedy of small CPU mining margin, pause mining process during peak hour

# Key idea
With the drop of crypto prices, mining during high electricity cost period makes less sense and should be stopped.
Use Kill pause and continue would cause some stale share, it should be restarted at the cost of dev fee.
Restart also helps with buggy CPU miners that would generate lots of stale shares after a while.

# My On-peak TOU
On-peak	Weekdays from 7 a.m. to 11 a.m. and 5 p.m. to 7 p.m.

# Usage
```
./gen_config_first_name.pl # will generate a clean config
```
modify wallet address to yours, current is my NiceHash BTC
```
sudo ./run.pl 
```

You could download and compile xmrig yourself + modify TOU settings

```
my $off_peak_start = 19; # this is the afternoon when offpeak starts
my $off_peak_end = 7;  # 7am, nighttime cheap rate is over
```
