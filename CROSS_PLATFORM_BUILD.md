# Cross-Platform Build Guide

## The Reality

**PyInstaller is platform-specific**: It creates executables for the OS it's running on. You cannot create a Windows .exe on Linux directly with PyInstaller.

However, there are several legitimate solutions:

---

## Solution 1: GitHub Actions (Recommended - Free & Automated)

**Best for**: Open source projects, automated CI/CD, free Windows build resources

### Setup:
```bash
# Already created: .github/workflows/build-exe.yml
# Just push to GitHub with a tag:
git tag v1.0
git push origin v1.0
```

The workflow will:
- Run on GitHub's Windows servers
- Build the .exe automatically
- Create a release with the executable
- No local Windows machine needed

**Time to build**: ~5-10 minutes

---

## Solution 2: Docker with Windows Base Image

**Best for**: Self-hosted builds, offline builds, controlled environments

### Setup:
```bash
# Build Windows container (requires ~20GB space)
docker build -f Dockerfile.windows -t fsg-windows-builder .

# Run build inside container
docker run -v $(pwd)/dist:/app/dist fsg-windows-builder

# Result: dist/FinancialStatementGenerator.exe
```

**Time to build**: ~30-60 minutes (includes Windows container setup)

---

## Solution 3: Wine + PyInstaller on Linux

**Best for**: Local builds without cloud dependency

### Install Wine:
```bash
sudo apt-get install wine wine32 wine64 winetricks
```

### Install Python in Wine:
```bash
# Download Python Windows installer
wget https://www.python.org/ftp/python/3.11.2/python-3.11.2-amd64.exe

# Run in Wine
WINEARCH=win64 WINEPREFIX=~/wine wine python-3.11.2-amd64.exe /quiet
```

### Build in Wine:
```bash
~/wine/drive_c/Python311/python.exe -m pip install -r requirements.txt
~/wine/drive_c/Python311/python.exe build.py
```

**Pros**: Works offline, no cloud dependency
**Cons**: Complex setup, slow builds, disk space (~50GB)

---

## Solution 4: Simply Build on Windows

**Best for**: One-time builds, development machines, fastest results

### Steps:
```powershell
# On Windows machine
git clone <your-repo>
cd "WidowsFinancial Statements"
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python build.py
# Result: dist\FinancialStatementGenerator.exe
```

**Time to build**: ~10-15 minutes
**Simplest method**: Yes

---

## Solution 5: Remote Windows Server / VM

**Best for**: Developers without Windows machines

### Options:
- **Azure VMs**: Pay per hour (~$0.10-1.00/hr)
- **AWS EC2**: Pay per hour
- **DigitalOcean**: Not available (Linux only)
- **Linode**: Not available (Linux only)
- **Free options**: 
  - Azure free tier (limited)
  - AWS free tier (limited)
  - GitHub Actions (best free option)

### Process:
```bash
# Remote into Windows VM
# Follow: Solution 4 steps
```

---

## Recommended Path

### For Open Source / Public Project:
```bash
# Use GitHub Actions (free, automated, professional)
git tag v1.0.0
git push origin v1.0.0
# Automatic build on GitHub → releases page
```

### For Private / Internal Use:
```bash
# Option A: Build once on Windows, distribute .exe
# Option B: Use GitHub Actions (still free for private repos)
# Option C: Docker build once, distribute .exe
```

### For Development:
```bash
# Build on your development machine
# Test locally with: python -m streamlit run src/app.py
# Final build with build.py when on Windows
```

---

## Quick Reference: Which Solution?

| Solution | Cost | Setup Time | Build Time | Recommended For |
|----------|------|-----------|-----------|-----------------|
| GitHub Actions | Free | 2 min | 5-10 min | Public projects |
| Docker | Free | 30 min | 30-60 min | Self-hosted |
| Wine | Free | 45 min | 30-45 min | Linux-only machines |
| Windows VM | $10-30 | 5 min | 10-15 min | Quick one-time builds |
| Local Windows | Free | 0 min | 10-15 min | Regular dev work |

---

## Setting Up GitHub Actions (Step-by-Step)

1. **Push to GitHub**:
```bash
git remote add origin https://github.com/YOUR_USERNAME/WidowsFinancial.git
git push -u origin master
```

2. **Create tag to trigger build**:
```bash
git tag v1.0.0
git push origin v1.0.0
```

3. **Find executable**:
- Go to: https://github.com/YOUR_USERNAME/WidowsFinancial/releases
- Download: FinancialStatementGenerator.exe

**That's it!** No Windows machine needed.

---

## Current Status

✓ Linux executable ready: `dist/FinancialStatementGenerator`
✓ Build script updated: Cross-platform ready
✓ GitHub Actions configured: `.github/workflows/build-exe.yml`
✓ Docker setup available: `Dockerfile.windows`

To get Windows .exe:
1. **Option 1 (Recommended)**: Push to GitHub → Actions builds it → Download
2. **Option 2**: Run on Windows machine → `python build.py`
3. **Option 3**: Use Docker/Wine → Complex but possible

Choose the method that fits your workflow best!
