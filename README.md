# Simple Geiger counter support for Raspberry Pi 
This set of scripts allow you to generate charts (rotated hourly/daily/weekly/monthly/yearly) as well as (almost) real-time reporting.
## Hardware setup
You need a Geiger counter with pulse output (in the future, I might publish a circuit diagram) connected to RPi GPIO 4 (or modify the `geiger.py` to use a different pin). Right now I assume idle high (thus each Geiger pulse will start with falling edge, but I think inverted logic should work as well). Be sure to clamp the output to +3.3V and GND, as not to damage RPi GPIO input.
## Software setup
1. Run install.sh
2. Configure webserver to enable cgi-bin scripting, and use `/usr/local/lib/cgi-bin` as `/cgi-bin/`directory.
3. Configure webserver alias for `/geiger/img` directory to `/run/geiger/img/` (directory with generated charts)
4. Hopefully done

## Example lighttpd config
```
server.modules += (
        "mod_cgi"
)
$HTTP["url"] =~ "^/cgi-bin/" {
        cgi.assign = ( ".cgi" => "" )
        alias.url += ( "/cgi-bin/" => "/usr/local/lib/cgi-bin/" )
}
alias.url += ( "/geiger/img" => "/run/geiger/img/" )
```
