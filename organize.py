#!/usr/bin/env python3
"""
Smart File Organizer - Main CLI entrypoint

Usage: python organize.py <input_folder> <output_folder> [options]
"""
import argparse
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

try:
    from rich.console import Console
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich.table import Table
    from rich.panel import Panel
except ImportError:
    Console = None
    Progress = None

from extractors import extract_text
from classifier import FileClassifier
from renamer import FileRenamer

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SmartFileOrganizer:
    """Main organizer class that coordinates all components."""
    
    def __init__(self, api_key: str, output_path: Path, copy_mode: bool = True, dry_run: bool = False):
        self.classifier = FileClassifier(api_key)
        self.renamer = FileRenamer(output_path)
        self.copy_mode = copy_mode
        self.dry_run = dry_run
        self.console = Console() if Console else None
    
    def organize_folder(self, input_folder: Path) -> List[Dict[str, Any]]:
        """
        Organize all files in the input folder.
        
        Returns:
            List of dictionaries containing processing results for each file
        """
        if not input_folder.exists() or not input_folder.is_dir():
            raise ValueError(f"Input folder does not exist or is not a directory: {input_folder}")
        
        # Find all files to process
        files_to_process = self._find_files_to_process(input_folder)
        
        if not files_to_process:
            self._print("No supported files found in the input folder.")
            return []
        
        self._print(f"Found {len(files_to_process)} files to process")
        
        processed_files = []
        
        # Process files with progress bar if rich is available
        if self.console and Progress:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=self.console
            ) as progress:
                task = progress.add_task("Processing files...", total=len(files_to_process))
                
                for i, file_path in enumerate(files_to_process, 1):
                    progress.update(task, description=f"Processing {i}/{len(files_to_process)} files")
                    result = self._process_single_file(file_path)
                    processed_files.append(result)
                    progress.advance(task)
                    
                    # Print periodic updates for large batches
                    if i % 50 == 0 or i == len(files_to_process):
                        successful = len([f for f in processed_files if f['success']])
                        failed = len([f for f in processed_files if not f['success']])
                        self._print(f"Progress: {i}/{len(files_to_process)} processed ({successful} successful, {failed} failed)")
        else:
            # Fallback without progress bar
            for i, file_path in enumerate(files_to_process, 1):
                result = self._process_single_file(file_path)
                processed_files.append(result)
                
                # Print periodic updates
                if i % 50 == 0 or i == len(files_to_process):
                    successful = len([f for f in processed_files if f['success']])
                    failed = len([f for f in processed_files if not f['success']])
                    self._print(f"Progress: {i}/{len(files_to_process)} processed ({successful} successful, {failed} failed)")
        
        # Organize failed files into error folders
        if not self.dry_run:
            self._organize_failed_files(processed_files)
        
        return processed_files
    
    def _find_files_to_process(self, input_folder: Path) -> List[Path]:
        """Find all supported files in the input folder."""
        supported_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.gif', 
                              '.pdf', '.docx', '.doc', '.txt'}
        
        files = []
        for file_path in input_folder.rglob('*'):
            if file_path.is_file() and file_path.suffix.lower() in supported_extensions:
                files.append(file_path)
        
        return sorted(files)
    
    def _process_single_file(self, file_path: Path) -> Dict[str, Any]:
        """Process a single file through the entire pipeline."""
        result = {
            'original_name': file_path.name,
            'original_path': file_path,
            'success': False,
            'category': None,
            'new_filename': None,
            'new_path': None,
            'error_message': None
        }
        
        try:
            # Step 1: Extract text
            file_type, extracted_text = extract_text(file_path)
            
            if not extracted_text:
                result['error_message'] = f"Could not extract text from {file_type} file"
                return result
            
            # Step 2: Classify file
            classification = self.classifier.classify_file(file_path.name, extracted_text)
            
            if not classification:
                result['error_message'] = "Could not classify file content"
                return result
            
            result['category'] = classification['category']
            result['new_filename'] = classification['new_filename']
            
            # Step 3: Organize file (unless dry run)
            if not self.dry_run:
                success, new_path, message = self.renamer.organize_file(
                    file_path, 
                    classification['category'], 
                    classification['new_filename'],
                    self.copy_mode,
                    extracted_text
                )
                
                if success:
                    result['success'] = True
                    result['new_path'] = new_path
                else:
                    result['error_message'] = message
            else:
                # Dry run - just simulate success
                result['success'] = True
                result['new_path'] = Path("DRY_RUN") / classification['category'] / f"{classification['new_filename']}{file_path.suffix}"
            
        except Exception as e:
            result['error_message'] = f"Unexpected error: {e}"
            logger.exception(f"Error processing {file_path}")
        
        return result
    
    def _organize_failed_files(self, processed_files: List[Dict[str, Any]]):
        """Organize failed files into appropriate error folders."""
        failed_files = [f for f in processed_files if not f['success']]
        
        if not failed_files:
            return
        
        # Create main errors folder
        errors_folder = self.renamer.output_base_path / "_Errors"
        errors_folder.mkdir(exist_ok=True)
        
        # Categorize errors and organize files
        error_categories = {
            "text_extraction_failed": "Could not extract text",
            "classification_failed": "Could not classify file content", 
            "unsupported_format": "Unsupported file format",
            "processing_error": "Unexpected error"
        }
        
        for file_info in failed_files:
            error_message = file_info['error_message'] or "Unknown error"
            source_file = file_info['original_path']
            
            # Determine error category
            if "extract text" in error_message.lower():
                error_category = "text_extraction_failed"
            elif "classify" in error_message.lower():
                error_category = "classification_failed"
            elif "unsupported" in error_message.lower():
                error_category = "unsupported_format"
            else:
                error_category = "processing_error"
            
            # Create error subfolder
            error_subfolder = errors_folder / error_category
            error_subfolder.mkdir(exist_ok=True)
            
            # Copy file to error folder
            try:
                if self.copy_mode:
                    import shutil
                    target_path = error_subfolder / source_file.name
                    # Handle naming collisions
                    target_path = self.renamer._handle_naming_collision(target_path)
                    shutil.copy2(source_file, target_path)
                    
                    # Create error info file
                    error_info_path = target_path.with_suffix(target_path.suffix + '.error_info.txt')
                    with open(error_info_path, 'w', encoding='utf-8') as f:
                        f.write(f"Original file: {source_file}\n")
                        f.write(f"Error category: {error_category}\n")
                        f.write(f"Error message: {error_message}\n")
                        f.write(f"Processing date: {datetime.now().isoformat()}\n")
                        
            except Exception as e:
                logger.error(f"Could not organize failed file {source_file}: {e}")
    
    def _print(self, message: str):
        """Print message using rich console if available, otherwise regular print."""
        if self.console:
            self.console.print(message)
        else:
            print(message)
    
    def print_summary(self, processed_files: List[Dict[str, Any]]):
        """Print a summary of the processing results."""
        if not processed_files:
            self._print("No files were processed.")
            return
        
        successful = [f for f in processed_files if f['success']]
        failed = [f for f in processed_files if not f['success']]
        
        # Print summary statistics
        summary_text = f"""
Processing Complete!

Total files: {len(processed_files)}
Successfully organized: {len(successful)}
Failed: {len(failed)}
Mode: {'DRY RUN' if self.dry_run else ('COPY' if self.copy_mode else 'MOVE')}
"""
        
        if self.console:
            self.console.print(Panel(summary_text.strip(), title="Summary", border_style="green"))
        else:
            print(summary_text)
        
        # Print detailed results table
        if self.console and successful:
            table = Table(title="Successfully Organized Files")
            table.add_column("Original Name", style="cyan")
            table.add_column("New Location", style="green")
            table.add_column("Category", style="yellow")
            
            for file_info in successful:
                original = file_info['original_name']
                new_path = str(file_info['new_path']) if file_info['new_path'] else "Unknown"
                category = file_info['category'] or "Unknown"
                table.add_row(original, new_path, category)
            
            self.console.print(table)
        
        # Print failed files
        if failed:
            self._print("\nFailed files:")
            for file_info in failed:
                error_msg = file_info['error_message'] or "Unknown error"
                self._print(f"  ❌ {file_info['original_name']}: {error_msg}")


def main():
    """Main CLI entrypoint."""
    parser = argparse.ArgumentParser(
        description="Smart File Organizer - Automatically organize files using OCR and AI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python organize.py ./inbox ./organized
  python organize.py ./downloads ./sorted --move --dry-run
  python organize.py ./receipts ./organized --api-key sk-...
        """
    )
    
    parser.add_argument('input_folder', type=Path, help='Input folder containing files to organize')
    parser.add_argument('output_folder', type=Path, help='Output folder for organized files')
    parser.add_argument('--api-key', help='Anthropic API key (or set ANTHROPIC_API_KEY env var)')
    parser.add_argument('--move', action='store_true', help='Move files instead of copying them')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be done without actually moving files')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose logging')
    
    args = parser.parse_args()
    
    # Set up logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Load environment variables
    if load_dotenv:
        load_dotenv()
    
    # Get API key
    api_key = args.api_key or os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        print("Error: Anthropic API key is required. Set ANTHROPIC_API_KEY environment variable or use --api-key")
        sys.exit(1)
    
    try:
        # Create organizer
        organizer = SmartFileOrganizer(
            api_key=api_key,
            output_path=args.output_folder,
            copy_mode=not args.move,
            dry_run=args.dry_run
        )
        
        # Process files
        processed_files = organizer.organize_folder(args.input_folder)
        
        # Print summary
        organizer.print_summary(processed_files)
        
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        if args.verbose:
            logger.exception("Detailed error information:")
        sys.exit(1)


if __name__ == '__main__':
    main()