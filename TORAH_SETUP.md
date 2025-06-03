# Torah Text File Setup

⚠️ **Important**: Due to GitHub file size limits, the `torah.txt` file (containing the Hebrew Torah text) is not included in this repository.

## 📥 To get the Torah text file:

1. **From the original source**: Copy your `torah.txt` file from your original Torah search application
2. **Place it in the project root**: The file should be at `./torah.txt` (same level as `app_web.py`)

## 📁 Expected File Structure

```
torah-sod/
├── app_web.py
├── torah.txt          ← Your Torah text file goes here
├── requirements.txt
└── other files...
```

## ✅ File Validation

The `torah.txt` file should:
- Be UTF-8 encoded
- Contain Hebrew text
- Have verse markers like `{א}`, `{ב}`, etc.
- Include chapter headers like `בראשית פרק-א`

## 🐳 For Docker Users

If using Docker, make sure your `torah.txt` file is in the project directory before running:

```bash
# Copy your torah.txt file to the project
cp /path/to/your/torah.txt ./torah.txt

# Then start the application
docker-compose up -d
```

## 🔍 Testing

Once you have the file in place, you can test it works:

```bash
# Check if file exists and has content
ls -la torah.txt
head -20 torah.txt

# Start the application
python app_web.py
```

The application will log "Loaded Torah file with X lines" when it successfully loads the text.

---

**Note**: Without the `torah.txt` file, the application will start but searches will return "Torah file not found or empty" errors.