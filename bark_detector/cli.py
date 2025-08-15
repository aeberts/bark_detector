"""Command line interface for bark detector"""

import argparse
import logging
from pathlib import Path

from .core.detector import AdvancedBarkDetector
from .utils.helpers import setup_logging

logger = logging.getLogger(__name__)


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Advanced YAMNet Bark Detector v3.0',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m bark_detector                          # Start monitoring with default settings
  python -m bark_detector --sensitivity 0.5       # Lower sensitivity
  python -m bark_detector --profile myprofile     # Use saved profile
  python -m bark_detector --calibrate samples/    # Calibrate from files
        """
    )
    
    # Core detection parameters
    parser.add_argument('--sensitivity', type=float, default=0.68,
                        help='Detection sensitivity (0.01-1.0, default: 0.68)')
    parser.add_argument('--output-dir', type=str, default='recordings',
                        help='Output directory for recordings (default: recordings)')
    
    # Profile management
    parser.add_argument('--profile', type=str,
                        help='Load calibration profile by name')
    parser.add_argument('--save-profile', type=str,
                        help='Save current settings as profile')
    parser.add_argument('--list-profiles', action='store_true',
                        help='List available calibration profiles')
    
    # Calibration modes
    parser.add_argument('--calibrate', type=str,
                        help='Calibrate using files in directory')
    parser.add_argument('--calibrate-realtime', action='store_true',
                        help='Start real-time calibration mode')
    
    # Analysis modes
    parser.add_argument('--analyze-violations', type=str,
                        help='Analyze recordings for violations (date: YYYY-MM-DD)')
    parser.add_argument('--violation-report', nargs=2, metavar=('START_DATE', 'END_DATE'),
                        help='Generate violation report for date range')
    parser.add_argument('--export-violations', type=str,
                        help='Export violations to CSV file')
    
    # Audio file processing
    parser.add_argument('--convert-all', type=str,
                        help='Convert all audio files with date (YYYY-MM-DD)')
    parser.add_argument('--list-convertible', type=str,
                        help='List convertible audio files in directory')
    
    # Recording modes
    parser.add_argument('--manual-record', action='store_true',
                        help='Start manual recording mode')
    
    return parser.parse_args()


def main():
    """Main function with command line support."""
    # Setup logging
    logger = setup_logging()
    
    args = parse_arguments()
    
    logger.info("=" * 70)
    logger.info("Advanced YAMNet Bark Detector v3.0")
    logger.info("ML-based Detection with Legal Evidence Collection")
    logger.info("=" * 70)
    
    # Initialize detector
    config = {
        'sensitivity': args.sensitivity,
        'sample_rate': 16000,          # YAMNet requirement
        'chunk_size': 1024,
        'channels': 1,
        'quiet_duration': 30.0,
        'session_gap_threshold': 10.0,  # Recording sessions
        'output_dir': args.output_dir,
        'profile_name': args.save_profile
    }
    
    try:
        detector = AdvancedBarkDetector(**config)
        
        # Handle different modes
        if args.list_profiles:
            profiles = detector.list_profiles()
            if profiles:
                logger.info("📂 Available Calibration Profiles:")
                for profile in profiles:
                    logger.info(f"  {profile['name']} - Sensitivity: {profile['sensitivity']:.3f}")
                    logger.info(f"    Created: {profile['created'][:10]} - {profile['notes']}")
            else:
                logger.info("No calibration profiles found")
            return
        
        if args.calibrate:
            from .calibration.file_calibration import FileBasedCalibration
            
            calibrator = FileBasedCalibration(detector)
            directory = Path(args.calibrate).expanduser()
            
            if not directory.exists():
                logger.error(f"Directory not found: {directory}")
                return
            
            logger.info(f"🔍 Scanning {directory} for audio files...")
            
            # Find audio files in directory
            audio_extensions = ['.wav', '.m4a', '.mp3', '.aac', '.flac']
            audio_files = []
            for ext in audio_extensions:
                audio_files.extend(directory.glob(f"*{ext}"))
            
            if not audio_files:
                logger.error(f"No audio files found in {directory}")
                return
            
            logger.info(f"📁 Found {len(audio_files)} audio files")
            
            try:
                # Run calibration
                profile = calibrator.calibrate_from_files(audio_files)
                logger.info(f"✅ Calibration complete! Profile: {profile.name}")
                logger.info(f"   Optimal sensitivity: {profile.sensitivity:.3f}")
                logger.info(f"   Notes: {profile.notes}")
                
                # Save profile
                profiles_dir = Path.home() / '.bark_detector' / 'profiles'
                profiles_dir.mkdir(parents=True, exist_ok=True)
                profile_path = profiles_dir / f"{profile.name}.json"
                profile.save(profile_path)
                logger.info(f"💾 Profile saved: {profile_path}")
                
            except Exception as e:
                logger.error(f"Calibration failed: {e}")
                return 1
            return
        
        if args.calibrate_realtime:
            from .calibration.realtime_calibration import CalibrationMode
            from pathlib import Path
            
            try:
                # Set up detector for calibration mode
                detector.calibration_mode = CalibrationMode(detector, duration_minutes=10)
                detector.is_calibrating = True
                
                logger.info("🎯 Starting real-time calibration with bark detection...")
                logger.info("Both the detector and calibration system are now active")
                
                # Start detector in background
                detector.start()
                
                # Run calibration
                calibration_results = detector.calibration_mode.start_calibration()
                
                if calibration_results:
                    # Create and save profile
                    profile = detector.calibration_mode.create_calibration_profile(calibration_results)
                    
                    # Save profile
                    profiles_dir = Path.home() / '.bark_detector' / 'profiles'
                    profiles_dir.mkdir(parents=True, exist_ok=True)
                    profile_path = profiles_dir / f"{profile.name}.json"
                    profile.save(profile_path)
                    
                    logger.info(f"💾 Calibration profile saved: {profile_path}")
                    logger.info(f"🎯 You can now use this profile with: --profile {profile.name}")
                else:
                    logger.info("❌ Calibration was cancelled - no profile created")
                    
            except Exception as e:
                logger.error(f"Real-time calibration failed: {e}")
                return 1
            finally:
                detector.stop()
            return
        
        if args.analyze_violations:
            try:
                violations = detector.analyze_violations_for_date(args.analyze_violations)
                
                if violations:
                    logger.info(f"✅ Found {len(violations)} violations for {args.analyze_violations}")
                    for i, violation in enumerate(violations, 1):
                        logger.info(f"  📅 Violation {i}: {violation.violation_type}")
                        logger.info(f"     Duration: {violation.total_bark_duration/60:.1f} minutes")
                        logger.info(f"     Audio files: {len(violation.audio_files)} files")
                        logger.info(f"     Confidence: {violation.avg_confidence:.3f}")
                else:
                    logger.info(f"No violations found for {args.analyze_violations}")
                    
            except Exception as e:
                logger.error(f"Violation analysis failed: {e}")
                return 1
            return
        
        if args.convert_all:
            from .utils.audio_converter import AudioFileConverter
            
            try:
                converter = AudioFileConverter()
                recordings_dir = Path(args.output_dir)
                
                # Convert files for specified date
                results = converter.convert_files_for_date(recordings_dir, args.convert_all)
                
                if results['total_files'] > 0:
                    logger.info(f"✅ Conversion complete!")
                    logger.info(f"   Converted: {results['converted']} files")
                    logger.info(f"   Skipped: {results['skipped']} (already converted)")
                    logger.info(f"   Failed: {results['failed']} files")
                    
                    if results['converted_files']:
                        logger.info(f"📁 Converted files:")
                        for converted_file in results['converted_files']:
                            logger.info(f"   {Path(converted_file).name}")
                else:
                    logger.info(f"📁 No audio files found for date {args.convert_all}")
                    
            except Exception as e:
                logger.error(f"Conversion failed: {e}")
                return 1
            return
        
        if args.list_convertible:
            from .utils.audio_converter import AudioFileConverter
            
            try:
                converter = AudioFileConverter()
                directory = Path(args.list_convertible)
                
                if not directory.exists():
                    logger.error(f"Directory not found: {directory}")
                    return 1
                
                files = converter.get_convertible_files_in_directory(directory)
                
                if files:
                    logger.info(f"📁 Found {len(files)} convertible files in {directory}:")
                    for file_path in files:
                        logger.info(f"   {file_path.name}")
                else:
                    logger.info(f"📁 No convertible files found in {directory}")
                    
            except Exception as e:
                logger.error(f"List convertible files failed: {e}")
                return 1
            return
        
        if args.violation_report:
            from .legal.database import ViolationDatabase
            
            try:
                start_date, end_date = args.violation_report
                db = ViolationDatabase()
                
                violations = db.get_violations_by_date_range(start_date, end_date)
                
                if violations:
                    logger.info(f"📋 Found {len(violations)} violations from {start_date} to {end_date}:")
                    for i, violation in enumerate(violations, 1):
                        logger.info(f"  {i}. {violation.date} - {violation.violation_type}")
                        logger.info(f"     Duration: {violation.total_bark_duration/60:.1f}min, Files: {len(violation.audio_files)}")
                else:
                    logger.info(f"📋 No violations found from {start_date} to {end_date}")
                    
            except Exception as e:
                logger.error(f"Violation report failed: {e}")
                return 1
            return
        
        if args.export_violations:
            from .legal.database import ViolationDatabase
            
            try:
                db = ViolationDatabase()
                output_path = Path(args.export_violations)
                
                if not db.violations:
                    logger.info("📋 No violations found in database to export")
                    return
                
                db.export_to_csv(output_path)
                logger.info(f"✅ Exported {len(db.violations)} violations to {output_path}")
                logger.info(f"📋 CSV file ready for RDCO submission")
                    
            except Exception as e:
                logger.error(f"Export violations failed: {e}")
                return 1
            return
        
        if args.manual_record:
            from .recording.manual_recorder import ManualRecorder
            from datetime import datetime
            
            try:
                # Generate output path
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = Path(args.output_dir) / f"manual_recording_{timestamp}.wav"
                
                # Create and start manual recorder
                recorder = ManualRecorder(detector, output_path)
                recorder.start_recording()
                
            except Exception as e:
                logger.error(f"Manual recording failed: {e}")
                return 1
            return
        
        # Default: Start monitoring
        logger.info("🐕 Starting bark detection...")
        logger.info(f"🎛️ Sensitivity: {args.sensitivity}")
        logger.info("Press Ctrl+C to stop")
        
        detector.start_monitoring()
        
    except KeyboardInterrupt:
        logger.info("\\nReceived interrupt signal...")
        logger.info("Stopping bark detector...")
    except Exception as e:
        logger.error(f"Error: {e}")
        return 1
    
    return 0


if __name__ == '__main__':
    exit(main())