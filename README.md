# HTTP TTS for Home Assistant

*The project is a work in progress*

This project provides a media player (custom component) for Home Assistant that plays TTS (text-to-speech) via a Bluetooth speaker.

If you're using HA's Bluetooth device tracker (for presence detection), this project also provides a replacement Bluetooth tracker that allows both components to play nicely together.

Since the Bluetooth tracker constantly scans for devices, playback of audio on the Bluetooth speaker may be disrupted / become choppy while scanning. These custom components work together to ensure only one of them is accessing Bluetooth at any given time.

The flow is something like this:

- Bluetooth tracker component continually scans for devices (presence detection)
- TTS service gets called to play something on the Bluetooth speaker
- TTS Bluetooth speaker component disables Bluetooth tracker component
- Bluetooth tracker component terminates any running Bluetooth scans
- TTS Bluetooth speaker component plays the TTS MP3 file
- TTS Bluetooth speaker component enables Bluetooth tracker component
- Bluetooth tracker component continues scanning for devices (presence detection)

## Getting Started

### 1) Install Pulse Audio (with Bluetooth support), MPlayer and SoX (with MP3 support)

```
sudo apt-get install pulseaudio pulseaudio-module-bluetooth bluez mplayer sox libsox-fmt-mp3
```

### 2) Add HA and pi user to 'pulse-access' group (pi user for testing, homeassistant for the service)

```
sudo adduser pi pulse-access
sudo adduser homeassistant pulse-access
```

### 3) Add Bluetooth discovery to Pulse Audio

In `/etc/pulse/system.pa`, add the following to the bottom of the file:

```
### Bluetooth Support
.ifexists module-bluetooth-discover.so
load-module module-bluetooth-discover
.endif

#set-card-profile bluez_card.00_2F_AD_12_0D_42 a2dp_sink
```

The last part is to persist the setting for a2dp, in case your bluetooth seems to default to a different profile.  I have commented it out because it seems to be flakey.

You may want to uncomment this line if your audio is getting cut off:
```
### Automatically suspend sinks/sources that become idle for too long
#load-module module-suspend-on-idle
```

### 4) Create a service to run Pulse Audio at startup
Create the file `/etc/systemd/system/pulseaudio.service` and add the following to it:

```
[Unit]
Description=Pulse Audio

[Service]
Type=simple
Environment=DBUS_SESSION_BUS_ADDRESS=unix:path=/run/dbus/system_bus_socket
ExecStart=/usr/bin/pulseaudio --system --disallow-exit --disable-shm --exit-idle-time=-1

[Install]
WantedBy=multi-user.target
```

Enable the service to start at boot time.

```
sudo systemctl daemon-reload
sudo systemctl enable pulseaudio.service
```

Give pulse user access to bluetooth interfaces

edit `/etc/dbus-1/system.d/bluetooth.conf`

add the following lines:
```
  <policy user="pulse">
    <allow send_destination="org.bluez"/>
    <allow send_interface="org.bluez.MediaEndpoint1"/>
  </policy>
```
### 5) Create a script to pair the Bluetooth speaker at startup

```
sudo bluetoothctl
scan on
pair 00:2F:AD:12:0D:42
trust 00:2F:AD:12:0D:42
connect 00:2F:AD:12:0D:42
quit
```

Create the file `[PATH_TO_YOUR_HOME_ASSSISTANT]/scripts/pair_bluetooth.sh` and add the following to it. Make sure to replace the Bluetooth address with that of your Bluetooth speaker.

```
#!/bin/bash

bluetoothctl << EOF
connect 00:2F:AD:12:0D:42
EOF
```
Make sure to grant execute permissions for the script.

```
sudo chmod a+x [PATH_TO_YOUR_HOME_ASSSISTANT]/scripts/pair_bluetooth.sh
```

In `/etc/rc.local`, add the following to the end of the file to run the script at startup:

```
# Pair Bluetooth devices
[PATH_TO_YOUR_HOME_ASSSISTANT]/scripts/pair_bluetooth.sh

exit 0
```

### 6) Add the TTS Bluetooth Speaker to HA

Copy the TTS Bluetooth Speaker component (from this GitHub repo) and save it to your Home Assistant config directory.

```
custom_components/tts_bluetooth_speaker/media_player.py
```

### 7) Optional - Add the (new) Bluetooth Tracker to HA

This step only applies if you're using the Bluetooth tracker.

Copy the Bluetooth Tracker component and save it to your Home Assistant config directory.

```
custom_components/bluetooth_tracker/device_tracker.py
```

### 8) Validate audio sink is available

`pactl list sinks`

You should see something like:

```
Sink #1
        State: SUSPENDED
        Name: bluez_sink.00_2F_AD_12_0D_42.a2dp_sink
```

If it instead says headset_head_unit, you can switch to a2dp profile as follows:

```
pactl set-card-profile bluez_card.00_2F_AD_12_0D_42 a2dp_sink
```

Check again and validate it is using a2dp.

Test using command line if mplayer can stream to a2dp

```
mplayer -ao pulse::bluez_sink.00_2F_AD_12_0D_42.a2dp_sink -channels 2 -volume 100 /some/mp3file.mp3
```


### 9) Start using it in HA

By this stage (after a reboot), you should be able to start using the TTS Bluetooth speaker in HA.

Below is an example of how the component is configured. You need to specify the Bluetooth address of your speaker, and optionally set the `volume` level (must be between 0 and 1). If you find your speaker is not playing the first part of the audio (i.e. first second is missing when played back), then you can optionally add some silence before and/or after the original TTS audio hsing the `pre_silence_duration` and `post_silence_duration` options (must be between 0 and 60 seconds). If you've change your TTS cache directory (in your TTS config), then you should set the `cache_dir` here to match.

```
media_player:
  - platform: tts_bluetooth_speaker
    address: [BLUETOOTH_ADDRESS]   # Required - for example, 00:2F:AD:12:0D:42
    volume: 0.45                   # Optional - default is 0.5
#    pre_silence_duration: 1       # Optional - No. of seconds silence before the TTS (default is 0)
#    post_silence_duration: 0.5    # Optional - No. of seconds silence after the TTS (default is 0)
#    cache_dir: /tmp/tts           # Optional - make sure it matches the same setting in TTS config
```

If you're using the Bluetooth tracker, you probably already have this in your config:

```
device_tracker:
  - platform: bluetooth_tracker
```

To test that it's all working, you can use **Developer Tools > Services** in the HA frontend to play a TTS message through your Bluetooth speaker:

![image](https://user-images.githubusercontent.com/8870047/57437834-b773ef00-7296-11e9-891e-9a181ebb6520.png)

`{ "entity_id": "media_player.tts_bluetooth_speaker", "message": "Hello" }`

Another way to test it is to add an automation that plays a TTS message whenever HA is started:

```
automation: 
  - alias: Home Assistant Start
    trigger:
      platform: homeassistant
      event: start
    action:
      - delay: '00:00:10'
      - service: tts.google_translate_say
        data:
          entity_id: media_player.tts_bluetooth_speaker
          message: 'Home Assistant has started'
```
