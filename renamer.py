"""
Rules for safe filenames and folder paths.
"""
import os
import shutil
from pathlib import Path
from typing import Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class FileRenamer:
    """Handles file renaming and organization."""
    
    def __init__(self, output_base_path: Path):
        self.output_base_path = Path(output_base_path)
        self.output_base_path.mkdir(parents=True, exist_ok=True)
    
    def organize_file(self, source_file: Path, category: str, new_filename: str, 
                     copy_mode: bool = True) -> Tuple[bool, Optional[Path], str]:
        """
        Organize a file into the appropriate category folder with new name.
        
        Args:
            source_file: Path to the source file
            category: Category folder name
            new_filename: New filename (without extension)
            copy_mode: If True, copy file; if False, move file
            
        Returns:
            Tuple of (success, new_file_path, message)
        """
        try:
            # Create category folder
            category_folder = self.output_base_path / self._sanitize_folder_name(category)
            category_folder.mkdir(parents=True, exist_ok=True)
            
            # Preserve original file extension
            original_extension = source_file.suffix
            safe_filename = self._sanitize_filename(new_filename)
            final_filename = f"{safe_filename}{original_extension}"
            
            # Handle naming collisions
            target_path = category_folder / final_filename
            target_path = self._handle_naming_collision(target_path)
            
            # Copy or move the file
            if copy_mode:
                shutil.copy2(source_file, target_path)
                operation = "copied"
            else:
                shutil.move(str(source_file), target_path)
                operation = "moved"
            
            message = f"Successfully {operation} to {target_path.relative_to(self.output_base_path)}"
            return True, target_path, message
            
        except Exception as e:
            error_msg = f"Error organizing file {source_file}: {e}"
            logger.error(error_msg)
            return False, None, error_msg
    
    def _sanitize_folder_name(self, folder_name: str) -> str:
        """Sanitize folder name for filesystem compatibility."""
        # Replace problematic characters
        problematic_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
        for char in problematic_chars:
            folder_name = folder_name.replace(char, '_')
        
        # Remove leading/trailing dots and spaces
        folder_name = folder_name.strip('. ')
        
        # Limit length
        folder_name = folder_name[:100]
        
        # Ensure it's not empty
        if not folder_name:
            folder_name = "Uncategorized"
        
        return folder_name
    
    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename for filesystem compatibility."""
        # Replace problematic characters
        problematic_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
        for char in problematic_chars:
            filename = filename.replace(char, '_')
        
        # Replace spaces with underscores
        filename = filename.replace(' ', '_')
        
        # Remove multiple consecutive underscores
        while '__' in filename:
            filename = filename.replace('__', '_')
        
        # Remove leading/trailing underscores and dots
        filename = filename.strip('_. ')
        
        # Limit length (leaving room for extension and collision suffix)
        filename = filename[:80]
        
        # Ensure it's not empty
        if not filename:
            filename = "unnamed_file"
        
        return filename
    
    def _handle_naming_collision(self, target_path: Path) -> Path:
        """Handle naming collisions by appending a suffix."""
        if not target_path.exists():
            return target_path
        
        base_name = target_path.stem
        extension = target_path.suffix
        parent_dir = target_path.parent
        
        counter = 1
        while True:
            new_name = f"{base_name}_{counter:03d}{extension}"
            new_path = parent_dir / new_name
            if not new_path.exists():
                return new_path
            counter += 1
            
            # Safety check to avoid infinite loop
            if counter > 999:
                # Use timestamp as fallback
                import time
                timestamp = int(time.time())
                new_name = f"{base_name}_{timestamp}{extension}"
                return parent_dir / new_name
    
    def create_summary_report(self, processed_files: list) -> str:
        """Create a summary report of processed files."""
        if not processed_files:
            return "No files were processed."
        
        report_lines = ["File Organization Summary", "=" * 50, ""]
        
        successful = [f for f in processed_files if f['success']]
        failed = [f for f in processed_files if not f['success']]
        
        report_lines.append(f"Total files processed: {len(processed_files)}")
        report_lines.append(f"Successfully organized: {len(successful)}")
        report_lines.append(f"Failed: {len(failed)}")
        report_lines.append("")
        
        if successful:
            report_lines.append("Successfully organized files:")
            report_lines.append("-" * 30)
            for file_info in successful:
                original = file_info['original_name']
                new_path = file_info['new_path']
                category = file_info['category']
                relative_path = new_path.relative_to(self.output_base_path) if new_path else "Unknown"
                report_lines.append(f"  {original} → {relative_path} [{category}]")
            report_lines.append("")
        
        if failed:
            report_lines.append("Failed files:")
            report_lines.append("-" * 15)
            for file_info in failed:
                original = file_info['original_name']
                error = file_info['error_message']
                report_lines.append(f"  {original}: {error}")
            report_lines.append("")
        
        return "\n".join(report_lines)