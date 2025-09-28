# Smart File Organizer

A Python-based tool for automatically organizing messy files (receipts, tickets, screenshots, PDFs, etc.) into structured folders. It extracts text via OCR and PDF parsers, classifies the file using an LLM, and then generates descriptive filenames and moves the files into appropriate subfolders.

## Features

- **Multi-format support**: Images (JPG, PNG, etc.), PDFs, Word documents, and text files
- **Nested folder processing**: Recursively processes all subdirectories in input folder
- **OCR text extraction**: Uses Tesseract for extracting text from images
- **Text preservation**: Saves extracted text alongside organized files for future reference
- **AI-powered classification**: Uses Anthropic's Claude models with improved consistency for broad categories
- **Smart error handling**: Failed files are organized into categorized error folders
- **Batch processing**: Optimized progress reporting for thousands of files
- **Safe file handling**: Copies files by default (with option to move), handles naming collisions
- **Rich CLI interface**: Progress bars and formatted output using Rich library
- **Dry run mode**: Preview what would be organized without actually moving files

## Installation

1. Clone this repository:
```bash
git clone <repository-url>
cd smart-file-organizer
```

2. Install Python dependencies:
```bash
pip install -r requirements.txt
```

3. Install Tesseract OCR (for image text extraction):

**macOS:**
```bash
brew install tesseract
```

**Ubuntu/Debian:**
```bash
sudo apt-get install tesseract-ocr
```

**Windows:**
Download and install from: https://github.com/UB-Mannheim/tesseract/wiki

4. Set up your Anthropic API key:
```bash
cp .env.example .env
# Edit .env and add your Anthropic API key
```

## Usage

### Basic Usage

```bash
python organize.py <input_folder> <output_folder>
```

### Examples

```bash
# Organize files from inbox to organized folder (copy mode)
python organize.py ./inbox ./organized

# Move files instead of copying them
python organize.py ./downloads ./sorted --move

# Dry run to see what would be organized
python organize.py ./receipts ./organized --dry-run

# Use specific API key
python organize.py ./inbox ./organized --api-key sk-your-key-here

# Verbose output for debugging
python organize.py ./inbox ./organized --verbose
```

### Command Line Options

- `input_folder`: Folder containing files to organize
- `output_folder`: Destination folder for organized files
- `--api-key`: Anthropic API key (alternatively set `ANTHROPIC_API_KEY` environment variable)
- `--move`: Move files instead of copying them (default is copy)
- `--dry-run`: Show what would be done without actually organizing files
- `--verbose`: Enable detailed logging output

## How It Works

1. **File Discovery**: Recursively scans the input folder and all subfolders for supported file types
2. **Text Extraction**: 
   - Images → OCR using Tesseract (saves extracted text alongside organized files)
   - PDFs → Text extraction using pdfminer
   - Word docs → Text extraction using python-docx
   - Text files → Direct reading
3. **AI Classification**: Sends extracted text to Anthropic Claude model for:
   - Category suggestion (e.g., "Receipts", "Bank Statements", "Travel Documents")
   - Descriptive filename generation (including vendor, date, type)
4. **File Organization**: 
   - Creates category subfolders in output directory
   - Renames files with descriptive names
   - Handles naming collisions safely
   - Preserves original file extensions
   - Saves extracted text as .txt files for future reference
   - Places failed files in organized error folders by failure type

## Input Folder Structure

The tool supports **nested folder structures** in the input directory. It will:
- Recursively scan all subdirectories
- Process all supported files regardless of folder depth
- Flatten the structure in the output (files are organized by category, not original folder structure)

Example input structure:
```
inbox/
├── 2023/
│   ├── receipts/
│   │   └── starbucks.jpg
│   └── documents/
│       └── contract.pdf
├── screenshots/
│   └── bank_statement.png
└── misc_files.txt
```

All files will be processed and organized by content category in the output folder.

## Supported File Types

- **Images**: JPG, JPEG, PNG, BMP, TIFF, GIF
- **Documents**: PDF, DOCX, DOC, TXT

## Example Output Structure

```
organized/
├── Receipts/
│   ├── uber_ride_receipt_2024-01-15_downtown.jpg
│   ├── uber_ride_receipt_2024-01-15_downtown_extracted_text.txt
│   ├── starbucks_coffee_receipt_2024-01-20.png
│   └── starbucks_coffee_receipt_2024-01-20_extracted_text.txt
├── Bank Statements/
│   ├── chase_statement_2024-01_checking.pdf
│   └── wells_fargo_statement_2024-01_savings.pdf
├── Travel Documents/
│   ├── united_boarding_pass_2024-02-10_sfo_jfk.pdf
│   └── amtrak_ticket_2024-02-15_nyc_boston.jpg
└── _Errors/
    ├── text_extraction_failed/
    │   ├── corrupted_image.jpg
    │   └── corrupted_image.jpg.error_info.txt
    ├── classification_failed/
    │   ├── unclear_document.pdf
    │   └── unclear_document.pdf.error_info.txt
    └── unsupported_format/
        ├── unknown_file.xyz
        └── unknown_file.xyz.error_info.txt
```

### Key Improvements

- **Broad Categories**: Uses consistent, broad categories (e.g., "Receipts" instead of "Uber Receipts", "Food Receipts")
- **Text Preservation**: OCR and extracted text saved as `_extracted_text.txt` files
- **Error Organization**: Failed files organized into `_Errors/` with subcategories by error type
- **Batch Processing**: Progress updates every 50 files for large batches (e.g., "Progress: 150/1000 processed")
- **Nested Input Support**: Processes files from any depth in input folder structure

## Configuration

### Environment Variables

- `ANTHROPIC_API_KEY`: Your Anthropic API key

### API Usage

The tool uses Anthropic's Claude-3-Haiku model by default. Each file processed requires one API call. Costs are typically minimal (a few cents per hundred files).

## Error Handling

- Files that can't be processed are left in their original location
- Detailed error messages are provided for failed files
- The tool continues processing even if individual files fail
- Use `--verbose` flag for detailed error information

## Development

### Project Structure

- `organize.py`: Main CLI entrypoint
- `extractors.py`: File type detection and text extraction
- `classifier.py`: LLM integration for file classification
- `renamer.py`: File organization and renaming logic
- `requirements.txt`: Python dependencies
- `.env.example`: Environment variable template

### Running Tests

```bash
# Create some test files in the inbox folder
mkdir -p inbox
echo "This is a test receipt from Starbucks on 2024-01-15" > inbox/receipt.txt

# Run the organizer in dry-run mode
python organize.py inbox organized --dry-run
```

## Troubleshooting

### Common Issues

1. **"pytesseract not found"**: Install Tesseract OCR system package
2. **"Anthropic API key required"**: Set up your API key in `.env` file
3. **"No text extracted"**: File might be corrupted or unsupported format - check `_Errors/text_extraction_failed/` folder
4. **"Could not classify file content"**: API issue or unclear content - check `_Errors/classification_failed/` folder
5. **Permission errors**: Check file/folder permissions
6. **Too many similar categories**: The tool now uses broad categories to avoid fragmentation

### Getting Help

Run with `--verbose` flag to see detailed error information:
```bash
python organize.py inbox organized --verbose
```

## License

This project is open source. See LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues for bugs and feature requests.