# Homeassistant Homee (WIP)

Integration of [homee](https://hom.ee/) into [Homeassistant](https://www.home-assistant.io/).

## Current Supported Modules

* Thermostats
* Lights
* Switches
* Covers (untested)
* Window contacts as binary_sensors
* Other attributes as sensors

## Setup
Add directories from `custom_components` to Homeassistant `custom_components`:

````bash
cd config/custom_components
ln -s $PATH_TO_HOMEASSISTANT_HOMEE/homeassistant-homee/custom_components/{binary_sensors,climate,cover,homee,light,sensor,switch} .
````

Add IP and credentails to `configuration.yaml`:

```yaml
# configuration.yaml
homee:
  cube: LOCAL_IP_FROM_HOMEE
  username: foo
  password: bar
```