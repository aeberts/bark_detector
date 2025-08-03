# ERROR Saving violations database.

(bark_detector) ➜  bark_detector git:(main) ✗ uv run bd.py --analyze-violations 2025-08-02
/Users/zand/dev/bark_detector/.venv/lib/python3.11/site-packages/tensorflow_hub/__init__.py:61: UserWarning: pkg_resources is deprecated as an API. See https://setuptools.pypa.io/en/latest/pkg_resources.html. The pkg_resources package is slated for removal as early as 2025-11-30. Refrain from using this package or pin to Setuptools<81.
  from pkg_resources import parse_version
2025-08-03 11:03:12,469 - INFO - ======================================================================
2025-08-03 11:03:12,469 - INFO - Advanced YAMNet Bark Detector v3.0
2025-08-03 11:03:12,469 - INFO - ML-based Detection with Legal Evidence Collection
2025-08-03 11:03:12,469 - INFO - ======================================================================
2025-08-03 11:03:12,469 - INFO - Downloading YAMNet model (this may take a few minutes on first run)...
Downloading YAMNet model2025-08-03 11:03:12,469 - INFO - Using /var/folders/8x/yr8h7zks5r98fq1rs4n9ythc0000gn/T/tfhub_modules to cache modules.
2025-08-03 11:03:14,005 - INFO - YAMNet model downloaded successfully!
2025-08-03 11:03:14,005 - INFO - Loading class names...
2025-08-03 11:03:14,038 - INFO - YAMNet model loaded successfully!
2025-08-03 11:03:14,039 - INFO - Model supports 521 audio classes
2025-08-03 11:03:14,039 - INFO - Found 13 bark-related classes
2025-08-03 11:03:14,039 - INFO - Advanced Bark Detector initialized:
2025-08-03 11:03:14,039 - INFO -   Sensitivity: 0.05
2025-08-03 11:03:14,039 - INFO -   Sample Rate: 16000 Hz
2025-08-03 11:03:14,039 - INFO -   Session Gap Threshold: 10.0s
2025-08-03 11:03:14,039 - INFO -   Quiet Duration: 30.0s
2025-08-03 11:03:14,039 - INFO -   Output Directory: recordings
2025-08-03 11:03:14,039 - INFO - 🔍 Analyzing recordings for violations on 2025-08-02
2025-08-03 11:03:14,042 - INFO - Found 8 recording files for 2025-08-02
2025-08-03 11:03:14,042 - INFO - Analyzing recording: bark_recording_20250802_060706.wav
2025-08-03 11:03:19,211 - INFO - Found 238 bark events in 6 sessions from bark_recording_20250802_060706.wav
2025-08-03 11:03:19,214 - INFO - Analyzing recording: bark_recording_20250802_062045.wav
2025-08-03 11:03:20,958 - INFO - Found 139 bark events in 3 sessions from bark_recording_20250802_062045.wav
2025-08-03 11:03:20,960 - INFO - Analyzing recording: bark_recording_20250802_062159.wav
2025-08-03 11:03:21,045 - INFO - Found 3 bark events in 2 sessions from bark_recording_20250802_062159.wav
2025-08-03 11:03:21,045 - INFO - Analyzing recording: bark_recording_20250802_062233.wav
2025-08-03 11:03:21,124 - INFO - Found 5 bark events in 2 sessions from bark_recording_20250802_062233.wav
2025-08-03 11:03:21,124 - INFO - Analyzing recording: bark_recording_20250802_062410.wav
2025-08-03 11:03:21,304 - INFO - Found 18 bark events in 1 sessions from bark_recording_20250802_062410.wav
2025-08-03 11:03:21,304 - INFO - Analyzing recording: bark_recording_20250802_062525.wav
2025-08-03 11:03:21,414 - INFO - Found 9 bark events in 2 sessions from bark_recording_20250802_062525.wav
2025-08-03 11:03:21,414 - INFO - Analyzing recording: bark_recording_20250802_062724.wav
2025-08-03 11:03:21,667 - INFO - Found 22 bark events in 3 sessions from bark_recording_20250802_062724.wav
2025-08-03 11:03:21,667 - INFO - Analyzing recording: bark_recording_20250802_074046.wav
2025-08-03 11:03:32,213 - INFO - Found 261 bark events in 4 sessions from bark_recording_20250802_074046.wav
2025-08-03 11:03:32,219 - INFO - Total sessions for 2025-08-02: 23
2025-08-03 11:03:32,220 - ERROR - Could not save violation database: Object of type float32 is not JSON serializable
2025-08-03 11:03:32,220 - ERROR - Could not save violation database: Object of type float32 is not JSON serializable
2025-08-03 11:03:32,220 - ERROR - Could not save violation database: Object of type float32 is not JSON serializable
2025-08-03 11:03:32,220 - ERROR - Could not save violation database: Object of type float32 is not JSON serializable
2025-08-03 11:03:32,220 - ERROR - Could not save violation database: Object of type float32 is not JSON serializable
2025-08-03 11:03:32,221 - ERROR - Could not save violation database: Object of type float32 is not JSON serializable
2025-08-03 11:03:32,221 - INFO - Detected 6 violations for 2025-08-02
2025-08-03 11:03:32,221 - INFO -   Constant violation: 6:07 AM - 6:19 AM (11.1min barking)
2025-08-03 11:03:32,221 - INFO -   Constant violation: 6:21 AM - 6:33 AM (9.9min barking)
2025-08-03 11:03:32,221 - INFO -   Constant violation: 6:26 AM - 6:32 AM (5.2min barking)
2025-08-03 11:03:32,221 - INFO -   Intermittent violation: 6:07 AM - 6:34 AM (32.2min barking)
2025-08-03 11:03:32,221 - INFO -   Constant violation: 7:43 AM - 8:53 AM (67.2min barking)
2025-08-03 11:03:32,221 - INFO -   Intermittent violation: 7:40 AM - 8:53 AM (68.3min barking)
2025-08-03 11:03:32,221 - INFO - ✅ Found 6 violations:
2025-08-03 11:03:32,221 - INFO -   📅 2025-08-02 6:07 AM - 6:19 AM
2025-08-03 11:03:32,221 - INFO -      Type: Constant, Duration: 11.1min
2025-08-03 11:03:32,221 - INFO -   📅 2025-08-02 6:21 AM - 6:33 AM
2025-08-03 11:03:32,221 - INFO -      Type: Constant, Duration: 9.9min
2025-08-03 11:03:32,221 - INFO -   📅 2025-08-02 6:26 AM - 6:32 AM
2025-08-03 11:03:32,221 - INFO -      Type: Constant, Duration: 5.2min
2025-08-03 11:03:32,221 - INFO -   📅 2025-08-02 6:07 AM - 6:34 AM
2025-08-03 11:03:32,221 - INFO -      Type: Intermittent, Duration: 32.2min
2025-08-03 11:03:32,221 - INFO -   📅 2025-08-02 7:43 AM - 8:53 AM
2025-08-03 11:03:32,221 - INFO -      Type: Constant, Duration: 67.2min
2025-08-03 11:03:32,221 - INFO -   📅 2025-08-02 7:40 AM - 8:53 AM
2025-08-03 11:03:32,221 - INFO -      Type: Intermittent, Duration: 68.3min

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