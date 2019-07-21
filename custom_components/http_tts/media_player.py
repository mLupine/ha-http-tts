"""
Support for TTS on a HTTP endpoint

"""
import voluptuous as vol

from homeassistant.components.media_player import (
    SUPPORT_PLAY_MEDIA,
    PLATFORM_SCHEMA,
    MediaPlayerDevice)
from homeassistant.const import (
    CONF_NAME, STATE_OFF, STATE_PLAYING)
import homeassistant.helpers.config_validation as cv

import subprocess

import logging

import os
import re
import requests
import sys
import time

DEFAULT_NAME = 'http_tts'
DEFAULT_CACHE_DIR = "tts"

SUPPORT_HTTP_TTS_SPEAKER = SUPPORT_PLAY_MEDIA

CONF_ENDPOINT = 'endpoint'
CONF_CACHE_DIR = 'cache_dir'

_LOGGER = logging.getLogger(__name__)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
    vol.Required(CONF_ENDPOINT): cv.url,
    vol.Optional(CONF_CACHE_DIR, default=DEFAULT_CACHE_DIR): cv.string,
})

def setup_platform(hass, config, add_devices, discovery_info=None):
    """Setup the HTTP TTS Speaker platform."""
    name = config.get(CONF_NAME)
    endpoint = config.get(CONF_ENDPOINT)
    cache_dir = get_tts_cache_dir(hass, config.get(CONF_CACHE_DIR))

    add_devices([HTTPTTSSpeakerDevice(hass, name, endpoint, cache_dir)])
    return True

def get_tts_cache_dir(hass, cache_dir):
    """Get cache folder."""
    if not os.path.isabs(cache_dir):
        cache_dir = hass.config.path(cache_dir)
    return cache_dir

class HTTPTTSSpeakerDevice(MediaPlayerDevice):
    """Representation of an HTTP TTS Speaker on the network."""

    def __init__(self, hass, name, endpoint, cache_dir):
        """Initialize the device."""
        self._hass = hass
        self._name = name
        self._is_standby = True
        self._current = None
        self._endpoint = endpoint
        self._cache_dir = self.get_tts_cache_dir(cache_dir)
#        _LOGGER.debug('Bluetooth tracker integration:  {}'.format(str(self._tracker)))

    def get_tts_cache_dir(self, cache_dir):
        """Get cache folder."""
        if not os.path.isabs(cache_dir):
            cache_dir = hass.config.path(cache_dir)
        return cache_dir

    def update(self):
        """Retrieve latest state."""
        if self._is_standby:
            self._current = None
        else:
            self._current = True

    @property
    def name(self):
        """Return the name of the device."""
        return self._name

    # MediaPlayerDevice properties and methods
    @property
    def state(self):
        """Return the state of the device."""
        if self._is_standby:
            return STATE_OFF
        else:
            return STATE_PLAYING

    @property
    def supported_features(self):
        """Flag media player features that are supported."""
        return SUPPORT_HTTP_TTS_SPEAKER

    @property
    def volume_level(self):
        """Volume level of the media player (0..1)."""
        return 1

    def play_media(self, media_type, media_id, **kwargs):
        """Send play commmand."""
        _LOGGER.info('play_media: %s', media_id)
        self._is_standby = False

        media_file = self._cache_dir + '/' + media_id[media_id.rfind('/') + 1:];
        
        media_file_to_play = media_file

#         if (self._pre_silence_duration > 0) or (self._post_silence_duration > 0):
#             media_file_to_play = "/tmp/tts_{}".format(os.path.basename(media_file))

#             if (self._pre_silence_duration > 0):
#               pre_silence_file = "/tmp/pre_silence.mp3"
#               command = "sox -c 1 -r 24000 -n {} synth {} brownnoise gain -50".format(pre_silence_file, self._pre_silence_duration)
#               _LOGGER.debug('Executing command: %s', command)
#               subprocess.call(command, shell=True)

#             if (self._post_silence_duration > 0):
#               post_silence_file = "/tmp/post_silence.mp3"
#               command = "sox -c 1 -r 24000 -n {} synth {} brownnoise gain -50".format(post_silence_file, self._post_silence_duration)
#               _LOGGER.debug('Executing command: %s', command)
#               subprocess.call(command, shell=True)

#             command = "sox {} {} {} {}".format(pre_silence_file, media_file, post_silence_file, media_file_to_play)
#             _LOGGER.debug('Executing command: %s', command)
#             subprocess.call(command, shell=True)

#         if self._tracker:
#             self._hass.services.call(bluetooth_tracker.DOMAIN, bluetooth_tracker.BLUETOOTH_TRACKER_SERVICE_TURN_OFF, None)
#             while self._hass.states.get(bluetooth_tracker.DOMAIN + '.' + bluetooth_tracker.ENTITY_ID).state == bluetooth_tracker.STATE_ON:
#                 _LOGGER.debug('Waiting for Bluetooth tracker to turn off')
#                 time.sleep(0.5)

        endpoint = self._endpoint
        
        try:
          _LOGGER.debug("Pushing to endpoint %s", endpoint)
          f = open(media_file_to_play, 'rb')
          r = requests.post(endpoint, files={'media': f})
          _LOGGER.debug("Endpoint response %d: %s", r.status_code, r.text)
        except Exception as e:
          _LOGGER.error("Error pushing to the endpoint: %s", e)
  
#         command = "mplayer -ao {} -quiet -channels 2 -volume {} {}".format(sink, volume, media_file_to_play);
#         _LOGGER.debug('Executing command: %s', command)
#         subprocess.call(command, shell=True)

#         if (self._pre_silence_duration > 0) or (self._post_silence_duration > 0):
#             command = "rm {} {} {}".format(pre_silence_file, media_file_to_play, post_silence_file);
#             _LOGGER.debug('Executing command: %s', command)
#             subprocess.call(command, shell=True)

#         if self._tracker:
#             self._hass.services.call(bluetooth_tracker.DOMAIN, bluetooth_tracker.BLUETOOTH_TRACKER_SERVICE_TURN_ON, None)

        self._is_standby = True
