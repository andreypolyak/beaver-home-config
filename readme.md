# Beaver Home Config

<img align="left" src="screenshots/beaver.PNG?raw=true">

- Home Assistant setup
- 18+ months of development
- 4 ZigBee networks with 100+ devices
- Smart light bulbs everywhere for circadian lighting
- 70+ AppDaemon automations
- Highly customized mobile-only dashboard

<br/>

## TOC

- [Overview](#overview)
- [Hardware](#hardware)
    - [Main](#main)
    - [Lighting](#lighting)
    - [Sensors](#sensors)
    - [Multimedia](#multimedia)
    - [Remotes](#remotes)
    - [Other devices](#other-devices)
- [User Interface](#user-interface)
- [Automations](#automations)

## Overview

After a year and a half of building my smart home, I finally decided that it's time to share its details and configs with a broader audience. Why it's called Beaver Home? Because I love beavers!

My smart home is built using multi-vendor and multi-protocol hardware (see below), mostly ready-made but sometimes DIY. I use [Home Assistant](https://www.home-assistant.io) — privacy-oriented open-source home automation software, which is the central part of my smart home.

It is my strong belief that home becomes smart not when it's full of devices which can be controlled from smartphone or voice assistants but when these devices are controlled by automations. To develop and run automations I'm using [AppDaemon](https://appdaemon.readthedocs.io/en/latest/). See below for an overview of all my automations.

## Hardware

My main (highly subjective!) principles for choosing the hardware:

- ZigBee is better than WiFi
- WiFi is better than Bluetooth
- Local is better than cloud
- Open source is better than a close source
- Ready-made is better than DIY (I'm lazy!)
- Customizable is better than non-customizable
- Smart light bulbs are better than smart switches (see below for explanations)
- All rules have exceptions

### Main

- Mac Mini (Late 2012, Intel i5, 16GB RAM, SSD) — main server with macOS installed on it. Home Assistant OS is launched as a Virtual Box virtual machine on it
- Apple Time Machine — used to backup all Macs in the house
- Unifi Dream Machine — router and WiFi access point
- 3x Raspberry PIs (2x2b and 1x3b) — used to [forward](https://www.zigbee2mqtt.io/how_tos/how_to_connect_to_a_remote_adapter.html) Zigbee [sticks and shields](https://t.me/zigberu) (3xCC2652 and 1xCC2531) over Ethernet to the main server which runs four different Zigbee2Mqtt instances. It's easier to admin them when they are installed on the main server rather than on PIs. Three CC2652 sticks/shields are located in different rooms to minimize the number of devices on each network, it was discovered that CC2652 provides the best performance for networks under 60 devices. One CC2531 stick is used to control Legrand switches which are working only on 11 channel
2x Raspberry PIs (1xZero and 1x3b, same as previous) — used to track iPhones with Bluetooth using [Monitor](https://github.com/andrewjfreyer/monitor)

### Lighting

I am the biggest fan of [Circadian](https://hoarelea.com/2019/01/15/the-ultimate-guide-to-circadian-lighting/)/[Adaptive](https://9to5mac.com/2020/12/18/adaptive-lighting-homekit/) lighting concept. In brief, it changes the color temperature throughout the day, putting hotter color temperature at evenings and nights and colder color temperature at daytime. Because of that, my only option is to use smart light bulbs all over the place.

I use Ikea Tradfri (E27, E14, GU10, total 27x bulbs) as they have all the necessary features (like reporting) and are cheap enough. Ikea has both CCT and RGB bulbs, but I prefer RGB bulbs because they have a wider color temperature range.

I also use Ikea Tradfri Driver for lighting in the wardrobe, 2x Gledopto GL-C-008P with LED strips mounted under the bed and the sofa, and Zigbee On/Off Controller to control the integrated bathroom mirror lights. 

Lights are mostly automated (motion sensors and scenes, see below), so people rarely need to control the lights manually. But for convenience, there are Legrand Valena Life Wireless Switches (06773) screwed in the place of traditional switches. This is a big advantage of Legrand switches because all other wireless switches (as far as I know) can only be glued to the wall and not screwed in it. A wireless switch, in this case, acts as a button and doesn't directly controls the lights, instead it sends signals to Home Assistant which then controls the lights. It doesn't change latency dramatically but gives room for customizations. Of course, it also means that lights can't be controlled when Home Assistant is down. To overcome it I have Ikea Tradfri Remote Controls (E1524/E1810) which are directly [bound](https://www.zigbee2mqtt.io/information/binding.html) to ZigBee groups of lights. So even when Home Assistant is not working lights can be directly controlled from the remotes. As a second-level backup Sonoff Mini WiFi relays (flashed with ESPHome firmware) are installed in ceilings to cut the power to some bulbs.

### Sensors

- 2x ZigBee DIYRuz [CO2 Sensors](https://diyruz.github.io/posts/airsense/) — uses SenseAir S8 for measuring
- 4x ZigBee DIYRuz [Plant Sensors](https://diyruz.github.io/posts/flower/)
- 2x DIY [bed occupancy sensor](https://github.com/eoncire/HA_bed_presence) — uses ESP32 and film pressure sensors, ESPHome firmware
- 12x Aqara human body movement and illuminance sensor (RTCGQ11LM) — [hacked](https://community.smartthings.com/t/making-xiaomi-motion-sensor-a-super-motion-sensor/139806) to have 5 seconds occupancy timeout
- 7x Aqara temperature, humidity and pressure sensor (WSDCGQ11LM)
- 12x Aqara door & window contact sensor (MCCGQ11LM)
- 10x Aqara water leak sensor (SJCGQ11LM) — 7 of which I'm using as actual water leak sensors and 3 as a chair occupancy sensor together with [this](https://aliexpress.com/item/4000151259805.html) pressure sensor
- MiJia light intensity sensor (GZCGQ01LM)

### Multimedia

- Philips TV 65PFT6520 — the software on this TV is horrible: Android TV is slow and buggy (use Apple TV instead) and API is unreliable (use a smart plug to monitor the state and IR blaster to control)
- Digma SmartControl IR1 — IR blaster flashed with ESPHome firmware, used to control TV and AC
- Apple TV
- Sony PlayStation 4
- Sonos Beam, Sonos Sub, 2x Sonos One, 2x Ikea Symfonisk bookshelf speakers, 2x Ikea Symfonisk table lamp speakers, Sonos Move — multiroom audio all over the place
- 2x Yandex Station Mini — voice assistant which supports the Russian language
- KDM XM200-8GH — peephole camera

### Remotes

- 4x Legrand Valena Life Wireless Switch (067773) — see above
- 4x Ikea Tradfri Remote Control (E1524/E1810) — see above
- Aqara Wireless Switch (WXKG11LM) — used as doorbell
- Tuya Wireless Switch with 3 Buttons (TS0043) — used to select the radio station
- 3x Ikea Tradfri Blind Remote (E1766) — directly bound to Ikea Blinds/Aqara Curtain to manually control them
- Ikea Tradfri Shortcut Button (E1812) — used to turn on night mode
- Ikea Tradfri On/Off Switch (E1743) — used to toggle bedside light (direct bind)

### Other devices

- 9x GS SKHMP30-I1 ZigBee Smart Plugs (OEM analog of Heiman HS2SK)
- Danalock V3 Smart Lock (Bluetooth & Zigbee)
- 2x Ikea Fyrtur Roller Blinds
- Aqara Curtain Motor (ZNCLDJ11LM)
- 2x Drivent — [window opener](https://www.youtube.com/watch?v=j29n-o0UPzY) device created by enthusiasts
- Xiaomi Roborock S5 Vacuum — used with [Valetudo RE](https://github.com/rand256/valetudo) firmware (removes cloud)
- 2x [Saures](https://www.saures.ru) controllers — used to meter water and electricity usage
- DIY [air freshener](https://jcallaghan.com/2020/03/can-you-iot-an-airwick-air-freshener/) — AirWick freshener with integrated ESP8266, ESPHome firmware
- Xiaomi Mi Smart Scale 2 (XMTZC04HM) — used with ESP32 to track weight

## User Interface

I'm building the mobile-only dashboard with the idea to have as low click and scroll interactions as possible to reach any element of the UI.

<details>
<summary><b>Screenshots</b></summary>

| Home page. No one is home so lights are off and scenes are not selected | Home page. Light cinema scene is selected, light in the living zone is on. It's evening so the card with alarms is displayed as well | Bathroom and Entrance page | Living Room page |
|---|---|---|---|
| ![Home](screenshots/home-away.PNG?raw=true) | ![Home](screenshots/home.PNG?raw=true) | ![Bathroom and Entrance](screenshots/bathroom-entrance.PNG?raw=true) | ![Living Room](screenshots/living-room.PNG?raw=true) |

| Living Room page. Additional light details are shown (brightness, color, auto turn on/off) | Kitchen page | Bedroom page | Bedroom page. Additional controls for bedroom window and cover are shown |
|---|---|---|---|
| ![Living Room](screenshots/living-room-lights.PNG?raw=true) | ![Kitchen](screenshots/kitchen.PNG?raw=true) | ![Bedroom](screenshots/bedroom.PNG?raw=true) | ![Bedroom](screenshots/bedroom-devices.PNG?raw=true) |

| Outside page. Control balcony lights and show people location | Outside page. Continued. Weather and climate | Settings page. 1 HACS update is available, 3 entities are unavailable. Notice also exclamation mark in the top right corner — attention needed indicator |
|---|---|---|
| ![Outside](screenshots/outside.PNG?raw=true) | ![Outside](screenshots/outside-more.PNG?raw=true) | ![Settings](screenshots/settings.PNG?raw=true) |

</details>

I don't like how the header bar looks on the mobile, so it's hidden with CSS and instead the row of [button cards](https://github.com/custom-cards/button-card) is used for navigation (see [lovelace/elements/navigation.yaml](lovelace/elements/navigation.yaml)).

There are 7 main pages on the dashboard:
- home — scene selection, light controls, climate details all over the place
- bathroom and entrance — bathroom and entrance devices and details
- living room — living room devices and details
- kitchen — kitchen devices and details
- bedroom — bedroom devices and details
- outside — balcony light control, person tracking and outside climate
- settings — open specific settings pages, check updates and other critical information, restart everything

And 13 additional pages are accessible from the settings page:
- entities — new and unavailable entities
- batteries — all battery levels
- sensors — all sensors
- lights — all lights and switches
- inputs — all input_booleans, input_texts, input_datetimes, and input_selects
- timers — all timers
- trackers — all WiFi, BLE, and other trackers
- appliances — home appliances (washing and coffee machines at the moment) settings and controls
- vacuum — vacuum cleaner settings and controls
- climate — climate setting, controls, and details
- media — media devices controls
- consumption — daily and monthly electricity and water consumption (don't like the current state, need to redo)
- logging — Telegram logging controls, incl. entity logging UI which is used to send Telegram updates on each entity state change

As you can see the [button cards](https://github.com/custom-cards/button-card) are used a lot in the Lovelace UI and instead of having options specified for each button card [templates](https://github.com/custom-cards/button-card/blob/master/README.md#configuration-templates) are used (see [lovelace/templates/buttons.yaml](lovelace/templates/buttons.yaml)). Templates are also used for [ApexCharts cards](https://github.com/RomRider/apexcharts-card) (see [lovelace/templates/charts.yaml](lovelace/templates/charts.yaml)).

I'm using slightly modified [Google Dark Theme](https://github.com/JuanMTech/google_dark_theme).

## Software

### Custom Integrations

- [adaptive_lighting](https://github.com/basnijholt/adaptive-lighting) — get circadian light sensor which shows color temperature for cureent time of a day based on the sun position. I use this sensor in automations as a backup if MiJia light intensity sensor (GZCGQ01LM) will be unavailable
- [deepstack face custom integration](https://github.com/robmarkcole/HASS-Deepstack-face) — recognize faces from camera stream
- [Favicon changer](https://github.com/thomasloven/hass-favicon) — change Home Assistant favicon
- [HACS](https://github.com/hacs/integration) — install custom integrations and cards
- [Integration Saures controllers with HA](https://github.com/volshebniks/sauresha) — get consumption data from [Saures](https://www.saures.ru) cloud
- [WebRTC Camera](https://github.com/AlexxIT/WebRTC) — view camera stream almost in real-time from Lovelace
- [Yandex Dialogs](https://github.com/AlexxIT/YandexDialogs) — 
- [Yandex Smart Home](https://github.com/dmitry-k/yandex_smart_home) — control Home Assistant from Yandex Stations
- [Yandex.Station](https://github.com/AlexxIT/YandexStation) — control Yandex Stations from Home Assistant
- [Личный кабинет Интер РАО (Энергосбыт)](https://github.com/alryaz/hass-lkcomu-interrao) — send electricity stats to local energy supplier

### Add-ons

- [AdGuard Home](https://github.com/hassio-addons/addon-adguard-home) — run local DNS server to block ads and trackers
- [AppDaemon 4](https://github.com/hassio-addons/addon-appdaemon) — run Python powered automations
- [Duck DNS](https://github.com/home-assistant/hassio-addons/tree/master/duckdns) — get remote access to Home Assitant using dynamic DNS service
- [ESPHome](https://esphome.io/) — build firmwares for ESP boards
- [File editor](https://github.com/home-assistant/hassio-addons/tree/master/configurator) — edit configuration files on a mobile
- [Glances](https://github.com/hassio-addons/addon-glances) — monitor system (rarely used)
- [Grafana](https://github.com/hassio-addons/addon-grafana) — monitor entity states stored on InfluxDB and logs stored in Loki
- [Home Assistant Google Drive Backup](https://github.com/sabeechen/hassio-google-drive-backup) — automatically backup Home Assistant configuration
- [InfluxDB](https://github.com/hassio-addons/addon-influxdb) — long-term store entity states
- [Loki](https://github.com/mdegat01/addon-loki) — store logs sent from Promtail
- [MariaDB](https://github.com/home-assistant/hassio-addons/tree/master/mariadb) — SQL database for Home Assistant recorder
- [Mosquitto broker](https://github.com/home-assistant/hassio-addons/tree/master/mosquitto) — MQTT broker
- [motionEye](https://github.com/hassio-addons/addon-motioneye) — network video recorder
- [NGINX Home Assistant SSL proxy](https://github.com/home-assistant/hassio-addons/tree/master/nginx_proxy) — proxy HTTP config pages for Roborock and Drivent into Home Assistant
- [phpMyAdmin](https://github.com/hassio-addons/addon-phpmyadmin) — UI for MariaDB
- [Portainer](https://github.com/hassio-addons/addon-portainer) — run and control Docker containers
- [Promtail](https://github.com/mdegat01/addon-promtail) — gather Docker logs from all add-ons and containers and store them in Loki to later view in Grafana
- [SSH & Web Terminal](https://github.com/hassio-addons/addon-ssh) — SSH access to Home Assistant
- [Valetudo Mapper](https://github.com/Poeschl/Hassio-Addons/tree/master/valetudo-mapper) — generate Valetudo map
- [Visual Studio Code](https://github.com/hassio-addons/addon-vscode) — edit configuration files on a laptop or desktop
- [WireGuard](https://github.com/hassio-addons/addon-wireguard) — VPN access to home network
- [Zigbee2mqtt](https://github.com/zigbee2mqtt/hassio-zigbee2mqtt/tree/master/zigbee2mqtt) — control and organize Zigbee network. I have multiple copies of this add-on for all Zigbee networks that I have, using [Github action](https://github.com/andreypolyak/zigbee2mqtt-multi-addon-action) that I wrote

## Automations

[AppDaemon](https://appdaemon.readthedocs.io/en/latest/) is used for automations. I find it much more powerful and easier to develop and support than YAML automations and Node-RED.

I'll try to list and describe all of my AppDaemon automations (or apps as they are called in AD world) here but before it happens you can find them in [appdaemon/apps](../../tree/master/appdaemon/apps) directory.
