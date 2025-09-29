#!/usr/bin/env python3
"""
Debug script to generate the exact same plot as the PDF to see what's happening.
"""

import sys
from pathlib import Path
from datetime import datetime
import matplotlib
matplotlib.use('Agg')  # Use non-GUI backend
import matplotlib.pyplot as plt

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from bark_detector.utils.pdf_generator import PDFGenerationService, PDFConfig
from bark_detector.legal.database import ViolationDatabase

def create_debug_plot():
    """Create the exact same plot as the PDF generator to debug intensity values."""

    # Load the data for 2025-09-23
    violation_db = ViolationDatabase()
    violations = violation_db.load_violations_new("2025-09-23")
    bark_events = violation_db.load_events("2025-09-23")

    config = PDFConfig()
    target_id = "8fdaba48-428a-411e-b1ad-42084ad43c0e"

    print(f"Loaded {len(violations)} violations and {len(bark_events)} events")

    # Create the exact same plot as _generate_activity_timeline
    fig, ax = plt.subplots(figsize=(12, 6))
    fig.patch.set_facecolor('white')

    # Create mapping of bark events to violation types for color coding
    bark_event_colors = {}
    for violation in violations:
        color = '#DC2626' if violation.type == "Continuous" else '#F59E0B'  # Red for continuous, orange for intermittent
        for bark_id in violation.barkEventIds:
            bark_event_colors[bark_id] = color

    # Track plotting for target event
    target_event_plotted = False
    plot_data = []

    # Plot all bark events as vertical lines (EXACT code from pdf_generator.py)
    for event in bark_events:
        # Parse event timestamp
        event_dt = datetime.fromisoformat(f"{event.realworld_date}T{event.realworld_time}.000Z")
        event_hour = event_dt.hour + event_dt.minute / 60

        # Only plot events within 6am-8pm window
        if 6 <= event_hour <= 20:
            # Determine color based on violation association
            color = bark_event_colors.get(event.bark_id, '#9CA3AF')  # Gray for non-violation events

            # Plot vertical line for bark event with height based on intensity
            intensity = getattr(event, 'intensity', config.default_intensity)
            # Use default intensity if intensity is 0.0 (missing/invalid data)
            if intensity == 0.0:
                intensity = config.default_intensity

            # This is the actual plot command from the PDF generator
            ax.plot([event_hour, event_hour], [0, intensity], color=color, alpha=0.7, linewidth=1.5)

            # Track our target event
            if event.bark_id == target_id:
                target_event_plotted = True
                plot_data.append({
                    'id': event.bark_id,
                    'time': event.realworld_time,
                    'hour': event_hour,
                    'raw_intensity': event.intensity,
                    'processed_intensity': intensity,
                    'color': color
                })
                print(f"\n*** TARGET EVENT PLOTTED ***")
                print(f"  ID: {event.bark_id}")
                print(f"  Time: {event.realworld_time}")
                print(f"  Hour: {event_hour}")
                print(f"  Raw intensity: {event.intensity}")
                print(f"  Processed intensity: {intensity}")
                print(f"  Plot command: ax.plot([{event_hour}, {event_hour}], [0, {intensity}], color='{color}', alpha=0.7, linewidth=1.5)")

    # Formatting for 6am-8pm window (EXACT code from pdf_generator.py)
    ax.set_xlim(5.5, 20.5)  # 6am to 8pm with slight margins
    ax.set_ylim(0, 1)
    ax.set_xlabel('Time of Day (6am - 8pm)', fontsize=12, fontweight='bold')
    ax.set_ylabel('Bark Intensity (0.0 - 1.0)', fontsize=12, fontweight='bold')
    ax.set_title(f'Bark Activity Chart for 2025-09-23 (6:00 AM - 8:00 PM)', fontsize=14, fontweight='bold', pad=20)

    # Set time ticks for 6am-8pm range
    ax.set_xticks(range(6, 21, 2))
    ax.set_xticklabels([f'{h:02d}:00' for h in range(6, 21, 2)], rotation=45)

    # Set y-axis ticks for intensity scale 0.0 to 1.0
    ax.set_yticks([0, 0.2, 0.4, 0.6, 0.8, 1.0])
    ax.set_yticklabels(['0.0', '0.2', '0.4', '0.6', '0.8', '1.0'])

    # Grid for both axes to show intensity levels
    ax.grid(True, alpha=0.3, linestyle='-', linewidth=0.5, axis='both')
    ax.set_facecolor('#FAFAFA')

    # Save the plot
    plt.tight_layout()
    plt.savefig('debug_activity_chart.png', dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()

    print(f"\nTarget event plotted: {target_event_plotted}")
    print(f"Plot saved as debug_activity_chart.png")

    return plot_data

if __name__ == "__main__":
    debug_data = create_debug_plot()