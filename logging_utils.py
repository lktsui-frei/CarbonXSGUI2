"""
Logging utilities for CarbonXS fitting operations.

This module provides functionality to log fitting operations with timestamped
log files that capture both console output and structured fitting data.
"""

import os
import sys
from datetime import datetime
from contextlib import contextmanager
from io import StringIO
import json


def get_log_directory():
    """
    Get the logs directory path, creating it if it doesn't exist.
    
    Returns:
        str: Path to the logs directory
    """
    log_dir = os.path.join(os.path.dirname(__file__), 'logs')
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    return log_dir


def generate_log_filename():
    """
    Generate a timestamped filename for the log file.
    
    Returns:
        str: Full path to the log file
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"fit_{timestamp}.log"
    return os.path.join(get_log_directory(), filename)


class StreamCapture:
    """
    Captures output from stdout/stderr while still displaying it.
    """
    def __init__(self, stream, log_file):
        self.stream = stream
        self.log_file = log_file
        self.original_stream = None
        
    def write(self, text):
        # Write to original stream
        if self.original_stream:
            self.original_stream.write(text)
            # Only flush if the stream supports it
            if hasattr(self.original_stream, 'flush'):
                self.original_stream.flush()
        # Write to log file
        self.log_file.write(text)
        self.log_file.flush()
        
    def flush(self):
        # Only flush if the stream supports it
        if self.original_stream and hasattr(self.original_stream, 'flush'):
            self.original_stream.flush()
        self.log_file.flush()


@contextmanager
def capture_fitting_log(initial_params=None, settings=None, mode='fit'):
    """
    Context manager to log fitting operations.
    
    Logs structured fitting data and provides a tee-style print function
    that writes to both console and log file.
    
    Args:
        initial_params: List of initial parameter values
        settings: Dictionary of fitting settings
        mode: 'fit' or 'calculate'
        
    Yields:
        dict: Context dictionary with log file path, log_result, and log_print functions
        
    Example:
        with capture_fitting_log(params, settings, 'fit') as log_ctx:
            # Use log_print instead of print for logged output
            log_ctx['log_print'](f"Starting fit...")
            result = fitter.fit(...)
            log_ctx['log_result'](final_params=result, success=True)
    """
    log_file_path = generate_log_filename()
    log_file = open(log_file_path, 'w', encoding='utf-8')
    
    # Write header
    log_file.write("=" * 80 + "\n")
    log_file.write(f"CarbonXS Fitting Log\n")
    log_file.write(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    log_file.write(f"Mode: {mode}\n")
    log_file.write("=" * 80 + "\n\n")
    
    # Log initial parameters and settings
    if initial_params is not None:
        log_file.write("INITIAL PARAMETERS:\n")
        log_file.write("-" * 80 + "\n")
        param_labels = [
            "Scale Factor", "Background Constant", "Background S", "Background S^2",
            "Background S^3", "Background S^4", "Background 1/S",
            "A (In Plane Cell Constant)", "d002 (Interlayer Spacing)",
            "La (Coherence Length)", "M (Number of Layers)", "SM (Width of M Distribution)",
            "DAB (In plane strain)", "del (Inter Plane Strain)",
            "Pr (Probability of Random Stacking)", "Pt (Probability of 3R Stacking)",
            "Debye Waller Factor", "PO (Preferred Orientation Factor)"
        ]
        for i, (label, value) in enumerate(zip(param_labels, initial_params)):
            log_file.write(f"  [{i:2d}] {label:45s} = {value:12.6f}\n")
        log_file.write("\n")
    
    if settings is not None:
        log_file.write("FITTING SETTINGS:\n")
        log_file.write("-" * 80 + "\n")
        for key, value in sorted(settings.items()):
            log_file.write(f"  {key:30s} = {value}\n")
        log_file.write("\n")
    
    log_file.write("FITTING OUTPUT:\n")
    log_file.write("-" * 80 + "\n")
    log_file.flush()
    
    def log_print(*args, **kwargs):
        """
        Print function that writes to both console and log file.
        Use this instead of print() for output you want logged.
        """
        # Print to console normally
        print(*args, **kwargs)
        # Also write to log file
        import io
        output = io.StringIO()
        print(*args, **kwargs, file=output)
        log_file.write(output.getvalue())
        log_file.flush()
    
    def log_result(final_params=None, success=None, message=None, **kwargs):
        """Log the final results of the fitting operation."""
        log_file.write("\n")
        log_file.write("=" * 80 + "\n")
        log_file.write("FITTING RESULTS:\n")
        log_file.write("-" * 80 + "\n")
        
        if success is not None:
            log_file.write(f"Success: {success}\n")
        if message is not None:
            log_file.write(f"Message: {message}\n")
        
        if final_params is not None:
            log_file.write("\nFINAL PARAMETERS:\n")
            param_labels = [
                "Scale Factor", "Background Constant", "Background S", "Background S^2",
                "Background S^3", "Background S^4", "Background 1/S",
                "A (In Plane Cell Constant)", "d002 (Interlayer Spacing)",
                "La (Coherence Length)", "M (Number of Layers)", "SM (Width of M Distribution)",
                "DAB (In plane strain)", "del (Inter Plane Strain)",
                "Pr (Probability of Random Stacking)", "Pt (Probability of 3R Stacking)",
                "Debye Waller Factor", "PO (Preferred Orientation Factor)"
            ]
            for i, (label, value) in enumerate(zip(param_labels, final_params)):
                log_file.write(f"  [{i:2d}] {label:45s} = {value:12.6f}\n")
        
        # Log any additional kwargs
        if kwargs:
            log_file.write("\nADDITIONAL INFO:\n")
            for key, value in sorted(kwargs.items()):
                if value is not None:
                    log_file.write(f"  {key}: {value}\n")
        
        log_file.write("\n")
        log_file.write("=" * 80 + "\n")
        log_file.write(f"Log completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        log_file.write("=" * 80 + "\n")
        log_file.flush()
    
    context = {
        'log_file_path': log_file_path,
        'log_result': log_result,
        'log_print': log_print
    }
    
    try:
        yield context
    finally:
        # Close log file
        log_file.close()
        print(f"Fitting log saved to: {log_file_path}")

