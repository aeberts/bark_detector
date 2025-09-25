"""Command line interface for bark detector"""

import os
import argparse
import logging
from pathlib import Path

# Apply comprehensive TensorFlow logging suppression early (critical for Intel Macs)
from .utils.tensorflow_suppression import suppress_tensorflow_logging
suppress_tensorflow_logging()

from .core.detector import AdvancedBarkDetector
from .utils.helpers import setup_logging
from .utils.config import ConfigManager, BarkDetectorConfig

logger = logging.getLogger(__name__)


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Advanced YAMNet Bark Detector v3.0',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m bark_detector                          # Start monitoring with default settings
  python -m bark_detector --config myconfig.json  # Use configuration file
  python -m bark_detector --sensitivity 0.5       # Lower real-time sensitivity
  python -m bark_detector --analysis-sensitivity 0.25  # Lower analysis sensitivity for more detections
  python -m bark_detector --profile myprofile     # Use saved profile
  python -m bark_detector --calibrate samples/    # Calibrate from files
  python -m bark_detector --create-config config.json  # Create default config file
        """
    )
    
    # Configuration file
    parser.add_argument('--config', type=str,
                        help='Load configuration from JSON file')
    parser.add_argument('--create-config', type=str,
                        help='Create default configuration file at specified path')
    
    # Core detection parameters
    parser.add_argument('--sensitivity', type=float,
                        help='Real-time detection sensitivity (0.01-1.0, default: 0.68)')
    parser.add_argument('--analysis-sensitivity', type=float,
                        help='Analysis mode sensitivity for comprehensive bark detection (0.1-1.0, default: 0.30)')
    parser.add_argument('--output-dir', type=str,
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
    parser.add_argument('--calibrate-files', action='store_true',
                        help='Start file-based calibration mode')
    
    # File-based calibration arguments
    parser.add_argument('--audio-files', nargs='+',
                        help='Audio files for file-based calibration (WAV format)')
    parser.add_argument('--ground-truth-files', nargs='+',
                        help='Ground truth JSON files (optional, can be fewer than audio files for background/negative samples)')
    parser.add_argument('--create-template', type=str,
                        help='Create ground truth template for specified audio file')
    parser.add_argument('--sensitivity-range', nargs=2, type=float, default=[0.01, 0.5],
                        help='Sensitivity range for sweep (default: 0.01 0.5)')
    parser.add_argument('--steps', type=int, default=20,
                        help='Number of steps in calibration sweep (default: 20)')
    
    # Analysis modes
    parser.add_argument('--analyze-violations', type=str,
                        help='Analyze recordings for bylaw violations using YAMNet ML analysis (date: YYYY-MM-DD). Creates structured JSON files with bark events and violations in violations/[DATE]/ directory.')
    parser.add_argument('--violation-report', type=str, metavar='YYYY-MM-DD',
                        help='Generate PDF violation report for specified date (automatically runs analysis if needed)')
    parser.add_argument('--export-violations', type=str,
                        help='Export violations to CSV file')
    parser.add_argument('--list-violations', action='store_true',
                        help='List all detected violations')
    parser.add_argument('--enhanced-violation-report', type=str,
                        help='Generate enhanced violation report from logs (date: YYYY-MM-DD)')
    
    # Audio file processing
    parser.add_argument('--convert-all', type=str,
                        help='Convert all audio files with date (YYYY-MM-DD)')
    parser.add_argument('--list-convertible', type=str,
                        help='List convertible audio files in directory')
    parser.add_argument('--convert-files', nargs='+',
                        help='Convert specific audio files to WAV 16kHz format')
    parser.add_argument('--convert-directory', type=str,
                        help='Convert all convertible audio files in specified directory')
    
    # Recording modes
    parser.add_argument('--manual-record', action='store_true',
                        help='Start manual recording mode')
    parser.add_argument('--record', type=str,
                        help='Record calibration sample to specified file (WAV format)')
    parser.add_argument('--duration', type=int, default=10,
                        help='Duration for calibration/recording (default: 10 minutes)')
    
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
    
    # Handle config file creation
    if args.create_config:
        config_manager = ConfigManager()
        config_manager.create_default_config(args.create_config)
        return
    
    # Load configuration
    config_manager = ConfigManager()
    try:
        config = config_manager.load_config(args.config)
        # Merge CLI arguments with config file (CLI takes precedence)
        config = config_manager.merge_cli_args(config, args)
        
        if args.config:
            logger.info(f"📝 Configuration loaded from: {args.config}")
        
    except (FileNotFoundError, ValueError, RuntimeError) as e:
        logger.error(f"Configuration error: {e}")
        return
    
    # Convert config to detector parameters
    detector_config = {
        'sensitivity': config.detection.sensitivity,
        'analysis_sensitivity': config.detection.analysis_sensitivity,
        'sample_rate': config.detection.sample_rate,
        'chunk_size': config.detection.chunk_size,
        'channels': config.detection.channels,
        'quiet_duration': config.detection.quiet_duration,
        'session_gap_threshold': config.detection.session_gap_threshold,
        'output_dir': config.output.recordings_dir,
        'profile_name': args.save_profile,
        'config': config
    }

    try:
        detector = AdvancedBarkDetector(**detector_config)
        
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
                detector.calibration_mode = CalibrationMode(detector, duration_minutes=args.duration)
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
        
        if args.calibrate_files:
            from .calibration.file_calibration import FileBasedCalibration
            from pathlib import Path
            
            if not args.audio_files:
                logger.error("--audio-files required for file-based calibration")
                logger.info("Example: uv run python -m bark_detector --calibrate-files --audio-files bark1.wav bark2.wav")
                return 1
            
            logger.info("📁 Starting file-based calibration...")
            
            calibrator = FileBasedCalibration(detector)
            
            # Add test files
            audio_paths = [Path(f) for f in args.audio_files]
            ground_truth_paths = []
            
            if args.ground_truth_files:
                if len(args.ground_truth_files) > len(args.audio_files):
                    logger.error("Cannot have more ground truth files than audio files")
                    return 1
                ground_truth_paths = [Path(f) for f in args.ground_truth_files]
            
            # Validate files exist
            for audio_path in audio_paths:
                if not audio_path.exists():
                    logger.error(f"Audio file not found: {audio_path}")
                    return 1
            
            for gt_path in ground_truth_paths:
                if not gt_path.exists():
                    logger.error(f"Ground truth file not found: {gt_path}")
                    return 1
            
            # Add files to calibrator
            for i, audio_path in enumerate(audio_paths):
                gt_path = ground_truth_paths[i] if i < len(ground_truth_paths) else None
                calibrator.add_test_file(audio_path, gt_path)
            
            # Run calibration
            try:
                results = calibrator.run_sensitivity_sweep(
                    sensitivity_range=tuple(args.sensitivity_range),
                    steps=args.steps
                )
                
                # Create and save profile if requested
                if args.save_profile:
                    from .core.models import CalibrationProfile
                    from datetime import datetime
                    
                    best_result = results['best_result']
                    
                    profile = CalibrationProfile(
                        name=args.save_profile,
                        sensitivity=results['optimal_sensitivity'],
                        min_bark_duration=0.5,
                        session_gap_threshold=10.0,
                        background_noise_level=0.01,
                        created_date=datetime.now().isoformat(),
                        location="File-based Calibration",
                        notes=f"F1={best_result['f1_score']:.3f}, "
                              f"P={best_result['precision']:.1%}, "
                              f"R={best_result['recall']:.1%}, "
                              f"Files={len(audio_paths)}"
                    )
                    
                    # Save profile
                    profiles_dir = Path.home() / '.bark_detector' / 'profiles'
                    profiles_dir.mkdir(parents=True, exist_ok=True)
                    profile_path = profiles_dir / f"{profile.name}.json"
                    profile.save(profile_path)
                    
                    logger.info(f"✅ File-based calibration complete! Profile '{args.save_profile}' saved.")
                    logger.info(f"   To use: uv run python -m bark_detector --profile {args.save_profile}")
                else:
                    logger.info("✅ File-based calibration complete! Use --save-profile to save settings.")
                    
            except Exception as e:
                logger.error(f"Calibration failed: {e}")
                return 1
            
            return
        
        if args.create_template:
            from .calibration.file_calibration import FileBasedCalibration
            from pathlib import Path
            
            audio_path = Path(args.create_template)
            if not audio_path.exists():
                logger.error(f"Audio file not found: {audio_path}")
                return 1
            
            calibrator = FileBasedCalibration(detector)
            template_path = calibrator.create_ground_truth_template(audio_path)
            logger.info(f"✅ Template created: {template_path}")
            logger.info("Edit the template file to add bark timestamps, then run:")
            logger.info(f"  uv run python -m bark_detector --calibrate-files --audio-files {audio_path} --ground-truth-files {template_path}")
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
            from .utils.pdf_generator import PDFGenerationService
            from datetime import datetime
            from pathlib import Path as PathLib

            try:
                # Parse and validate date format
                target_date = args.violation_report
                try:
                    datetime.strptime(target_date, '%Y-%m-%d')
                except ValueError:
                    logger.error(f"❌ Invalid date format: {target_date}. Use YYYY-MM-DD format")
                    return 1

                logger.info(f"📊 Generating PDF violation report for {target_date}...")

                # Check if violations file exists, run analysis if needed
                violation_db = ViolationDatabase(violations_dir=PathLib('violations'))
                violation_file_path = PathLib('violations') / target_date / f'{target_date}_violations.json'

                if not violation_file_path.exists():
                    logger.info(f"📋 No existing violation analysis found for {target_date}")
                    logger.info(f"🔍 Automatically running violation analysis...")

                    # Run analysis using the detector
                    violations = detector.analyze_violations_for_date(target_date)

                    if violations is None:
                        logger.error(f"❌ Failed to run violation analysis for {target_date}")
                        return 1

                    if not violations:
                        logger.info(f"📋 No violations found for {target_date}. Skipping PDF generation.")
                        return 0

                    logger.info(f"✅ Analysis complete. Found {len(violations)} violations")

                # Create reports directory if it doesn't exist
                reports_dir = PathLib('reports')
                reports_dir.mkdir(parents=True, exist_ok=True)

                # Generate PDF using PDF Generation Service
                pdf_service = PDFGenerationService()
                pdf_output_path = pdf_service.generate_pdf_from_date(
                    violation_date=target_date,
                    output_dir=reports_dir,
                    violation_db=violation_db
                )

                if pdf_output_path and pdf_output_path.exists():
                    logger.info(f"✅ PDF violation report generated: {pdf_output_path}")
                    logger.info(f"📄 Report saved as: {pdf_output_path.name}")
                else:
                    logger.error(f"❌ Failed to generate PDF report for {target_date}")
                    return 1

            except FileNotFoundError as e:
                logger.error(f"❌ File not found: {e}")
                logger.error(f"❌ Check that recordings directory exists for date {target_date}")
                return 1
            except PermissionError as e:
                logger.error(f"❌ Permission denied: {e}")
                logger.error(f"❌ Unable to create or write to reports directory")
                return 1
            except Exception as e:
                logger.error(f"❌ Violation report failed: {e}")
                return 1
            return
        
        if args.enhanced_violation_report:
            from .utils.report_generator import LogBasedReportGenerator
            from datetime import datetime
            from pathlib import Path

            # Show deprecation warning
            logger.warning("⚠️  DEPRECATION WARNING: --enhanced-violation-report is deprecated")
            logger.warning("⚠️  Please use --violation-report YYYY-MM-DD instead for PDF reports")
            logger.warning("⚠️  This command will be removed in a future version")

            try:
                # Parse date
                logger.info(f"📅 Parsing date: {args.enhanced_violation_report}")
                target_date = datetime.strptime(args.enhanced_violation_report, '%Y-%m-%d').date()
                logger.info(f"📅 Parsed successfully: {target_date}")
                
                logger.info(f"📊 Generating enhanced violation report from logs for {target_date}...")
                
                # Create report generator
                report_generator = LogBasedReportGenerator()
                
                # Generate reports
                reports = report_generator.generate_reports_for_date(target_date)
                
                if "error" in reports:
                    logger.error(f"❌ {reports['error']}")
                    return 1
                
                # Create reports directory
                reports_dir = Path("reports") / f"enhanced-{target_date}"
                reports_dir.mkdir(parents=True, exist_ok=True)
                
                # Save reports
                for report_name, report_content in reports.items():
                    if report_name != "error":
                        report_file = reports_dir / f"{report_name}.txt"
                        with open(report_file, 'w', encoding='utf-8') as f:
                            f.write(report_content)
                        logger.info(f"📝 Generated: {report_file}")
                
                logger.info(f"✅ Enhanced violation reports saved to: {reports_dir}")
                logger.info("📊 Reports include:")
                logger.info("   - Time-of-day formatted violation summary")
                logger.info("   - Per-audio-file bark analysis") 
                logger.info("   - Detailed violation breakdowns")
                
            except ValueError as e:
                logger.error(f"❌ Date parsing error: {e}")
                logger.error(f"❌ Invalid date format: {args.enhanced_violation_report}. Use YYYY-MM-DD")
                return 1
            except Exception as e:
                logger.error(f"Enhanced violation report failed: {e}")
                import traceback
                logger.error(f"Traceback: {traceback.format_exc()}")
                return 1
            return
        
        if args.export_violations:
            from .legal.database import ViolationDatabase
            
            try:
                # Use project-local violations/ directory  
                db = ViolationDatabase(violations_dir=Path('violations'))
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
        
        if args.list_violations:
            from .legal.database import ViolationDatabase
            
            try:
                # Use project-local violations/ directory  
                db = ViolationDatabase(violations_dir=Path('violations'))
                
                if db.violations:
                    logger.info(f"📋 Found {len(db.violations)} total violations:")
                    for i, violation in enumerate(db.violations, 1):
                        logger.info(f"  {i}. {violation.date} {violation.start_time} - {violation.end_time}")
                        logger.info(f"     Type: {violation.violation_type}, Duration: {violation.total_bark_duration/60:.1f}min")
                else:
                    logger.info("📋 No violations detected yet")
                    
            except Exception as e:
                logger.error(f"List violations failed: {e}")
                return 1
            return
        
        if args.convert_files:
            from .utils.audio_converter import AudioFileConverter
            from pathlib import Path
            
            try:
                converter = AudioFileConverter()
                file_paths = [Path(f) for f in args.convert_files]
                
                # Validate files exist
                for file_path in file_paths:
                    if not file_path.exists():
                        logger.error(f"File not found: {file_path}")
                        return 1
                
                results = converter.convert_specific_files(file_paths)
                
                if results['converted'] > 0:
                    logger.info(f"✅ Successfully converted {results['converted']} files")
                    logger.info(f"📁 Converted files:")
                    for converted_file in results['converted_files']:
                        logger.info(f"   {Path(converted_file).name}")
                elif results['total_files'] == 0:
                    logger.info(f"📁 No valid files to convert")
                else:
                    logger.info(f"ℹ️  All files already converted or failed")
                    
            except Exception as e:
                logger.error(f"Convert files failed: {e}")
                return 1
            return
        
        if args.convert_directory:
            from .utils.audio_converter import AudioFileConverter
            from pathlib import Path
            
            try:
                converter = AudioFileConverter()
                directory = Path(args.convert_directory)
                
                if not directory.exists():
                    logger.error(f"Directory not found: {directory}")
                    return 1
                
                results = converter.convert_directory(directory)
                
                if results['converted'] > 0:
                    logger.info(f"✅ Successfully converted {results['converted']} files")
                    logger.info(f"📁 Converted files:")
                    for converted_file in results['converted_files']:
                        logger.info(f"   {Path(converted_file).name}")
                elif results['total_files'] == 0:
                    logger.info(f"📁 No convertible files found in {directory}")
                else:
                    logger.info(f"ℹ️  All files already converted or failed")
                    
            except Exception as e:
                logger.error(f"Convert directory failed: {e}")
                return 1
            return
        
        if args.record:
            from .recording.manual_recorder import ManualRecorder
            from pathlib import Path
            
            try:
                output_path = Path(args.record)
                
                # Create and start manual recorder
                recorder = ManualRecorder(detector, output_path)
                recorder.start_recording()
                
            except Exception as e:
                logger.error(f"Recording failed: {e}")
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