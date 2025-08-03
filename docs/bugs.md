# YAMNet Error when starting the project (RESOLVED)

## Resolution

**Root Cause**: Corrupted TensorFlow Hub cache files
**Solution**: Clear the TensorFlow Hub cache directory and restart the application

```bash
# Remove the corrupted cache
rm -rf /var/folders/8x/yr8h7zks5r98fq1rs4n9ythc0000gn/T/tfhub_modules

# Or more generally (finds user-specific temp folders)
rm -rf /tmp/tfhub_modules
find /var/folders -name "tfhub_modules" -type d 2>/dev/null | xargs rm -rf
```

After clearing the cache, the bark detector will automatically re-download the YAMNet model on the next startup.

**Status**: This troubleshooting information has been added to README.md and project_overview.md for future reference.

## Error Output:
  Downloading YAMNet model2025-08-03 06:49:46,918 - INFO - Using 
  /var/folders/8x/yr8h7zks5r98fq1rs4n9ythc0000gn/T/tfhub_modules to cache modules.
  2025-08-03 06:49:46,920 - ERROR - Error loading YAMNet model: Trying to load a model of 
  incompatible/unknown type. '/var/folders/8x/yr8h7zks5r98fq1rs4n9ythc0000gn/T/tfhub_modules/9616fd04ec2
  360621642ef9455b84f4b668e219e' contains neither 'saved_model.pb' nor 'saved_model.pbtxt'.
  Traceback (most recent call last):
    File "/Users/zand/dev/bark_detector/bd.py", line 1897, in <module>
      main()
    File "/Users/zand/dev/bark_detector/bd.py", line 1714, in main
      detector = AdvancedBarkDetector(**config)
                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    File "/Users/zand/dev/bark_detector/bd.py", line 929, in __init__
      self._load_yamnet_model()
    File "/Users/zand/dev/bark_detector/bd.py", line 966, in _load_yamnet_model
      self.yamnet_model = hub.load('https://tfhub.dev/google/yamnet/1')
                          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    File "/Users/zand/dev/bark_detector/.venv/lib/python3.11/site-packages/tensorflow_hub/module_v2.py",
   line 107, in load
      raise ValueError("Trying to load a model of incompatible/unknown type. "
  ValueError: Trying to load a model of incompatible/unknown type. '/var/folders/8x/yr8h7zks5r98fq1rs4n9
  ythc0000gn/T/tfhub_modules/9616fd04ec2360621642ef9455b84f4b668e219e' contains neither 'saved_model.pb'
   nor 'saved_model.pbtxt'.