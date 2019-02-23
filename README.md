# julid-be
Lari di belakang yuk.


# Scraper
```console
> python julid/scrapper.py
```

```python

#
# See config_scrapper.yaml to see configuration value for scapper
#

forever_run(update_media_ids=True)
"""
	Running scrape, request label, save for media_ids in media_ids file (MEDIA_ID_SAVE_FILE, see config_scraper.yaml)
"""

scrape_and_save_for_media_id(media_id)
"""
	Running scrape, request label, and save for certain media_id
"""

scrape_and_save_for_media_ids(media_ids)
"""
	Running scrape, request label, and save for certain media_ids. media_ids is a list
"""

update_media_ids()
"""
	Check if there are new media_id and update media_ids file with new media_id (MEDIA_ID_SAVE_FILE, see config_scraper.yaml)
	Return type: list
"""

get_n_last_media_ids(n=conf['MONITORED_N_LAST_MEDIA_ID'], update_first=False)
"""
	Get n last media ids from media_ids file. If update_first=True, it will called get_n_last_media_ids first.
	Return type: list
"""

```