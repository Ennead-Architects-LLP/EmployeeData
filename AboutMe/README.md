# AboutMe Computer Information Collector

This application collects comprehensive computer information and can send it to the EmployeeData GitHub Pages website.

## Features

- **System Information Collection**: Gathers detailed computer specs including CPU, GPU, memory, OS, and more
- **GitHub Integration**: Sends data directly to the GitHub repository via repository dispatch API
- **Automatic Processing**: GitHub Actions automatically processes and displays the data on the website
- **Multiple Output Options**: Save locally, send to GitHub, or create GitHub issues

## Installation

1. **Install Python dependencies**:
   ```bash
   pip install requests psutil wmi
   ```

2. **Run the application**:
   ```bash
   python about_me.py
   ```

## Usage

### Basic Usage (Collect and Save Locally)
```bash
python about_me.py
```

### Send Data to GitHub Repository (Recommended)
```bash
python about_me.py --send-to-github --github-token YOUR_GITHUB_TOKEN
```

### Send Data as GitHub Issue (Alternative)
```bash
python about_me.py --send-as-issue --github-token YOUR_GITHUB_TOKEN
```

### Advanced Options
```bash
python about_me.py --send-to-github \
  --github-token YOUR_TOKEN \
  --repo-owner szhang \
  --repo-name EmployeeData \
  --output my_computer_info.json
```

## Command Line Arguments

- `--send-to-github`: Send data to GitHub repository (recommended method)
- `--send-as-issue`: Send data as GitHub issue (alternative method)
- `--github-token`: Your GitHub personal access token (required for sending)
- `--repo-owner`: GitHub repository owner (default: szhang)
- `--repo-name`: GitHub repository name (default: EmployeeData)
- `--output`: Output JSON filename (default: computer_info.json)
- `--no-save`: Don't save to local JSON file

## Getting a GitHub Token

1. Go to GitHub Settings → Developer settings → Personal access tokens
2. Click "Generate new token (classic)"
3. Select scopes: `repo` (Full control of private repositories)
4. Copy the token and use it with `--github-token`

## How It Works

1. **Data Collection**: The script gathers comprehensive system information
2. **GitHub Dispatch**: Data is sent to GitHub via repository dispatch API
3. **GitHub Actions**: Automatically processes the incoming data
4. **Website Display**: Data appears on the EmployeeData website in real-time

## Data Collected

- Computer name and user information
- Operating system details
- Hardware manufacturer and model
- CPU specifications
- GPU information and driver version
- Memory (RAM) details
- System serial number
- Collection timestamp

## Privacy

- All data is sent to the specified GitHub repository
- Data is processed and stored in the `assets/computer_data/` folder
- Individual computer data files are created with timestamps
- A master file (`all_computers.json`) contains all submissions

## Troubleshooting

### "GitHub token required" error
- Make sure you've provided a valid GitHub token with `--github-token`
- Ensure the token has `repo` permissions

### "Failed to send data" error
- Check your internet connection
- Verify the GitHub token is valid and not expired
- Ensure the repository exists and you have access

### WMI errors on Windows
- Run as Administrator if you encounter WMI permission errors
- Install Windows Management Framework if WMI is not available

## Example Output

The script will display a summary like:
```
=== Computer Information Summary ===
Computer Name: DESKTOP-ABC123
User: John Doe (johndoe)
OS: Windows 10
Manufacturer: Dell Inc.
Model: OptiPlex 7090
CPU: Intel(R) Core(TM) i7-10700 CPU @ 2.90GHz
Memory: 17179869184 bytes
GPU: NVIDIA GeForce RTX 3060
Serial Number: ABC123456
========================================
```
