# PeakPause
This is a remedy of small CPU/GPU mining margin, pause mining process during peak hour.
To use with GPU mining, simply modify and replace xmrig to miner that you prefer.

# Key idea
With the drop of crypto prices, mining during high electricity cost period makes less sense and should be stopped.
Use Kill pause and continue would cause some stale share, it should be restarted. Also heat makes sense during evening.

# My On-peak TOU
On-peak	Weekdays from 7 a.m. to 11 a.m. and 5 p.m. to 7 p.m.
Righ now the way it is coded is that we only mine during off-peak.

# Usage
```
./gen_config_first_name.pl # will generate a clean config
```
modify wallet address to yours, current is my NiceHash BTC

modify your root crontab via
```
sudo crontab -e
# inside crontab, do something like this
*/5 * * * * /home/wyatt/PeakPause/cron_run.pl > /home/wyatt/PeakPause/cron_run.log
```

The script will run every 5 minutes and check if miner should start or stop

You could download and compile xmrig yourself + modify TOU settings

```
my $off_peak_start = 19; # this is the afternoon when offpeak starts
my $off_peak_end = 7;  # 7am, nighttime cheap rate is over
```

# Temperature control
if the temp is too high, then it will pause mining. My setup expects a socket server sitting at
```
PeerAddr => '192.168.1.185',   
PeerPort => '48910',   
```
Where write "temp" to the server would return a float. The bias is just adjust the value from sensor compared to my thermal stat.
 
