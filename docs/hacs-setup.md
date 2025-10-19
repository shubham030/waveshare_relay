# HACS Setup Guide

This guide shows how to publish and use this integration with HACS (Home Assistant Community Store).

## For Users (Installing from HACS)

### Prerequisites
- Home Assistant with HACS installed
- HACS configured and working

### Installation Steps

1. **Add Custom Repository**:
   - Open Home Assistant
   - Go to **HACS** → **Integrations**
   - Click the **3-dot menu** (⋮) → **Custom repositories**
   - Add repository: `https://github.com/shubham030/waveshare_relay`
   - Category: **Integration**
   - Click **Add**

2. **Install Integration**:
   - In HACS Integrations, search for **"Waveshare Relay Hub"**
   - Click on the integration
   - Click **Download**
   - Restart Home Assistant

3. **Configure Integration**:
   - Go to **Settings** → **Devices & Services**
   - Click **Add Integration**
   - Search for **"Waveshare Relay Hub"**
   - Follow the configuration wizard

## For Developers (Publishing to HACS)

### Repository Structure

Your repository must have this structure for HACS compatibility:

```
waveshare_relay/
├── custom_components/
│   └── waveshare_relay/           # Integration files
│       ├── __init__.py
│       ├── manifest.json
│       ├── hub.py
│       ├── coordinator.py
│       ├── light.py
│       ├── switch.py
│       └── const.py
├── README.md                      # Main documentation
├── info.md                        # HACS info page
├── hacs.json                      # HACS configuration
├── LICENSE                        # License file
└── .github/
    └── workflows/
        └── test.yml              # CI/CD workflow
```

### Required Files for HACS

#### 1. `hacs.json`
```json
{
  "name": "Waveshare Relay Hub",
  "content_in_root": false,
  "filename": "waveshare_relay",
  "country": ["US", "GB", "DE", "FR", "IT", "ES", "NL", "SE", "NO", "DK", "FI", "BE", "AT", "CH", "AU", "CA", "JP", "CN", "IN"],
  "domains": ["light", "switch"],
  "homeassistant": "2023.1.0",
  "iot_class": "local_polling",
  "render_readme": true,
  "zip_release": false
}
```

#### 2. `info.md`
Short description for HACS store listing (max 150 words).

#### 3. `manifest.json`
```json
{
  "domain": "waveshare_relay",
  "name": "Waveshare Relay Hub",
  "codeowners": ["@shubham030"],
  "dependencies": [],
  "documentation": "https://github.com/shubham030/waveshare_relay",
  "iot_class": "local_polling",
  "issue_tracker": "https://github.com/shubham030/waveshare_relay/issues",
  "requirements": [],
  "version": "2.0.0",
  "config_flow": true,
  "platforms": ["light", "switch"],
  "homeassistant": "2023.1.0"
}
```

#### 4. `README.md`
Comprehensive documentation with:
- Installation instructions
- Configuration examples
- Usage examples
- Troubleshooting guide

### Publishing Steps

#### 1. Prepare Repository
```bash
# Clone/create your repository
git clone https://github.com/shubham030/waveshare_relay.git
cd waveshare_relay

# Ensure all required files are present
ls -la hacs.json info.md README.md LICENSE manifest.json

# Test the integration locally first
pytest tests/ -v
```

#### 2. Version Management
```bash
# Update version in manifest.json
{
  "version": "2.0.0"
}

# Create git tag for release
git tag -a v2.0.0 -m "Release version 2.0.0 - Production-ready improvements"
git push origin v2.0.0
```

#### 3. Submit to HACS

**Option A: Default Repository (Preferred)**
1. Fork [HACS/default](https://github.com/hacs/default)
2. Edit `custom_integrations.json`
3. Add your repository:
   ```json
   {
     "waveshare_relay": {
       "name": "Waveshare Relay Hub",
       "domain": "waveshare_relay",
       "description": "Production-ready integration for Waveshare Relay modules",
       "category": "integration"
     }
   }
   ```
4. Submit pull request
5. Wait for review and approval

**Option B: Custom Repository (Immediate)**
Users can add your repository directly:
```
https://github.com/shubham030/waveshare_relay
```

### HACS Validation

Before submitting, ensure your repository passes HACS validation:

#### 1. Required Files Check
- ✅ `hacs.json` present
- ✅ `info.md` present  
- ✅ `README.md` present
- ✅ `LICENSE` present
- ✅ `manifest.json` in correct location

#### 2. Code Quality Check
```bash
# Run linting
flake8 custom_components/waveshare_relay/

# Run tests
pytest tests/ -v

# Check manifest validity
python -c "import json; json.load(open('custom_components/waveshare_relay/manifest.json'))"
```

#### 3. Documentation Check
- ✅ Clear installation instructions
- ✅ Configuration examples
- ✅ Usage examples
- ✅ Troubleshooting section

### Release Management

#### Creating Releases
```bash
# Create release with proper versioning
git tag -a v2.0.0 -m "Release v2.0.0"
git push origin v2.0.0

# Or use GitHub releases UI
# - Go to GitHub repository
# - Click "Releases" → "Create new release"
# - Tag: v2.0.0
# - Title: "Version 2.0.0 - Production-ready improvements"
# - Description: Release notes
```

#### Version Scheme
Follow semantic versioning:
- `2.0.0` - Major version (breaking changes)
- `2.1.0` - Minor version (new features)
- `2.1.1` - Patch version (bug fixes)

### Testing HACS Installation

Test your HACS setup:

1. **Local Testing**:
   ```bash
   # Add to Home Assistant custom_components/
   cp -r custom_components/waveshare_relay /path/to/hass/custom_components/
   
   # Restart Home Assistant
   # Add integration via UI
   ```

2. **HACS Testing**:
   ```bash
   # Add repository to HACS
   # Install via HACS
   # Verify files are placed correctly
   # Test configuration and functionality
   ```

### Maintenance

#### Regular Updates
- Keep `manifest.json` version current
- Update `README.md` with new features
- Maintain compatibility with Home Assistant versions
- Respond to issues and PRs

#### HACS Requirements Compliance
- Maintain file structure
- Keep documentation updated
- Follow code quality standards
- Provide timely support

### Troubleshooting HACS Issues

#### Repository Not Found
- Check repository URL spelling
- Ensure repository is public
- Verify `hacs.json` is in root directory

#### Installation Fails
- Check `manifest.json` syntax
- Verify Home Assistant version compatibility
- Check required files are present

#### Integration Not Loading
- Check logs for import errors
- Verify all dependencies are available
- Test local installation first

For more information, see:
- [HACS Documentation](https://hacs.xyz/)
- [Home Assistant Integration Development](https://developers.home-assistant.io/)
- [HACS Integration Requirements](https://hacs.xyz/docs/publish/integration)