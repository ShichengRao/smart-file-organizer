# Smart File Organizer

A Python-based tool for automatically organizing messy files (receipts, tickets, screenshots, PDFs, etc.) into structured folders. It extracts text via OCR and PDF parsers, classifies the file using an LLM, and then generates descriptive filenames and moves the files into appropriate subfolders.

## Features

- **Multi-format support**: Images (JPG, PNG, etc.), PDFs, Word documents, and text files
- **OCR text extraction**: Uses Tesseract for extracting text from images
- **AI-powered classification**: Uses Anthropic's Claude models to categorize files and suggest descriptive names
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

1. **File Discovery**: Scans the input folder for supported file types
2. **Text Extraction**: 
   - Images → OCR using Tesseract
   - PDFs → Text extraction using pdfminer
   - Word docs → Text extraction using python-docx
   - Text files → Direct reading
3. **AI Classification**: Sends extracted text to Anthropic Claude model for:
   - Category suggestion (e.g., "Uber Receipts", "Bank Statements")
   - Descriptive filename generation (including vendor, date, type)
4. **File Organization**: 
   - Creates category subfolders
   - Renames files with descriptive names
   - Handles naming collisions safely
   - Preserves original file extensions

## Supported File Types

- **Images**: JPG, JPEG, PNG, BMP, TIFF, GIF
- **Documents**: PDF, DOCX, DOC, TXT

## Example Output Structure

```
organized/
├── Uber Receipts/
│   ├── uber_ride_receipt_2024-01-15_downtown.jpg
│   └── uber_eats_order_2024-01-20_pizza.png
├── Bank Statements/
│   ├── chase_statement_2024-01_checking.pdf
│   └── wells_fargo_statement_2024-01_savings.pdf
└── Travel Tickets/
    ├── united_boarding_pass_2024-02-10_sfo_to_nyc.pdf
    └── amtrak_ticket_2024-02-15_nyc_to_boston.jpg
```

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
3. **"No text extracted"**: File might be corrupted or unsupported format
4. **Permission errors**: Check file/folder permissions

### Getting Help

Run with `--verbose` flag to see detailed error information:
```bash
python organize.py inbox organized --verbose
```

## License

This project is open source. See LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues for bugs and feature requests.