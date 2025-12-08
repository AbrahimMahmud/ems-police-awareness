"""
Main script to run the entire analysis pipeline.

This script executes all analysis steps in sequence:
1. Clean EMS data and create panel
2. Merge Twitter awareness data
3. Run regression analysis
4. Create visualizations

Usage:
    python scripts/run_analysis.py
"""

import sys
from pathlib import Path

# Add scripts directory to path
PROJECT_ROOT = Path(__file__).parent.parent
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

def run_step(step_num, script_name, description):
    """Run a single analysis step."""
    print("\n" + "=" * 80)
    print(f"STEP {step_num}: {description}")
    print("=" * 80)
    
    script_path = SCRIPTS_DIR / script_name
    
    if not script_path.exists():
        raise FileNotFoundError(f"Script not found: {script_path}")
    
    # Import and run the script
    import importlib.util
    spec = importlib.util.spec_from_file_location(f"step_{step_num}", script_path)
    module = importlib.util.module_from_spec(spec)
    
    try:
        spec.loader.exec_module(module)
        print(f"\n✓ Step {step_num} completed successfully")
    except Exception as e:
        print(f"\n✗ Step {step_num} failed with error:")
        print(f"  {type(e).__name__}: {e}")
        raise

def main():
    """Run the complete analysis pipeline."""
    print("=" * 80)
    print("EMS Police Awareness Research - Analysis Pipeline")
    print("=" * 80)
    print(f"Project root: {PROJECT_ROOT}")
    
    steps = [
        (1, "01_data_cleaning.py", "Clean EMS data and create panel"),
        (2, "02_merge_awareness.py", "Merge Twitter awareness data"),
        (3, "03_regression_analysis.py", "Run regression analysis"),
        (4, "04_visualizations.py", "Create visualizations"),
    ]
    
    for step_num, script_name, description in steps:
        try:
            run_step(step_num, script_name, description)
        except Exception as e:
            print(f"\nPipeline stopped at step {step_num}")
            print(f"Error: {e}")
            sys.exit(1)
    
    print("\n" + "=" * 80)
    print("✓ All analysis steps completed successfully!")
    print("=" * 80)
    print("\nOutput files:")
    print(f"  - Processed data: {PROJECT_ROOT / 'data' / 'processed'}")
    print(f"  - Tables: {PROJECT_ROOT / 'outputs' / 'tables'}")
    print(f"  - Figures: {PROJECT_ROOT / 'outputs' / 'figures'}")

if __name__ == "__main__":
    main()

