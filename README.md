# PeakPause
This is a remedy of small CPU mining margin, pause mining process during peak hour

# Key idea
With the drop of crypto prices, mining during high electricity cost period makes less sense and should be stopped.
Use Kill pause and continue would cause some stale share, it should be restarted. Also heat makes sense during evening.

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

# temperature control
if the temp is too high, then it will pause mining. My setup expects a socket server sitting at
	PeerAddr => '192.168.1.185',   
	PeerPort => '48910',   
 Where write anything to the server would return a float. The bias is just adjust the value from sensor compared to my thermal stat.
 
