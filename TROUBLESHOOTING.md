# Troubleshooting Guide

## Setup Issues

### Python 3.12+ Compatibility Error
If you encounter an error like:
```
module pkgutil has no attribute ImpImporter
```

This is due to Python 3.12 removing deprecated features. 

**Solutions:**

1. **Use the Python 3.12 setup script:**
   ```bash
   ./setup-py312.sh
   ```

2. **Or manually install with Python 3.12 compatible versions:**
   ```bash
   cd backend
   rm -rf venv  # Remove old virtual environment
   python3 -m venv venv --upgrade-deps
   source venv/bin/activate
   pip install -r requirements-py312.txt
   ```

3. **Alternative: Use Python 3.11 or earlier:**
   ```bash
   # On Ubuntu/Debian
   sudo apt install python3.11 python3.11-venv
   python3.11 -m venv venv
   
   # On macOS with Homebrew
   brew install python@3.11
   python3.11 -m venv venv
   ```

### Meson Build Error
If you encounter an error like:
```
ERROR: Could not find a version that satisfies the requirement meson>=1.0.1
```

**Solutions:**

1. **Use the alternative setup script:**
   ```bash
   ./setup-alt.sh
   ```

2. **Manual installation with upgraded pip:**
   ```bash
   cd backend
   python3 -m venv venv
   source venv/bin/activate
   python -m pip install --upgrade pip setuptools wheel
   pip install -r requirements-flexible.txt
   ```

3. **If still failing, install packages individually:**
   ```bash
   pip install flask flask-cors python-dotenv
   pip install openai
   pip install azure-identity
   pip install pandas==1.5.3  # Use older version if needed
   pip install numpy==1.24.3
   pip install python-dateutil pydantic
   ```

### Python Version Issues
- Minimum required: Python 3.8+
- Recommended: Python 3.9 or 3.10
- Check your version: `python3 --version`

### Certificate Authentication Issues

1. **Certificate not found:**
   - Ensure certificate is in `backend/cert/apim-exp.pem`
   - Check file permissions: `chmod 600 backend/cert/apim-exp.pem`

2. **Azure AD token errors:**
   - Verify AZURE_SPN_CLIENT_ID and AZURE_TENANT_ID are correct
   - Ensure Service Principal has proper permissions

3. **Fallback to API key:**
   - Set `AUTH_METHOD=api_key` in `.env`
   - Provide valid AZURE_OPENAI_API_KEY

### Backend Connection Issues

1. **Port already in use:**
   ```bash
   # Find process using port 5000
   lsof -i :5000
   # Kill the process or use different port
   PORT=5001 python app.py
   ```

2. **Module not found errors:**
   - Ensure virtual environment is activated: `source venv/bin/activate`
   - Reinstall requirements: `pip install -r requirements.txt`

### Frontend Issues

1. **npm install failures:**
   - Clear npm cache: `npm cache clean --force`
   - Delete node_modules and package-lock.json, then reinstall:
     ```bash
     rm -rf node_modules package-lock.json
     npm install
     ```

2. **React app not starting:**
   - Check Node version: `node --version` (should be 16+)
   - Try different port: `PORT=3001 npm start`

### Common Environment Variable Issues

1. **Missing .env file:**
   ```bash
   cd backend
   cp .env.example .env
   # Edit .env with your credentials
   ```

2. **Environment variables not loading:**
   - Install python-dotenv: `pip install python-dotenv`
   - Check .env file location (should be in backend/ directory)

### Metric File Issues

1. **No metrics found:**
   - Ensure JSON files exist in correct directories
   - Check file naming: `YYYY-MM-DD_<type>.json`
   - Verify JSON format is valid

2. **Date parsing errors:**
   - Ensure timestamps are in ISO format
   - Check that all required fields exist in JSON

## Running in Production

For production deployment:

1. Use certificate authentication
2. Set `FLASK_ENV=production` and `FLASK_DEBUG=false`
3. Use a production WSGI server like Gunicorn:
   ```bash
   pip install gunicorn
   gunicorn -w 4 -b 0.0.0.0:5000 app:app
   ```
4. Build React for production:
   ```bash
   cd frontend
   npm run build
   ```

## Getting Help

If issues persist:
1. Check logs in terminal for detailed error messages
2. Verify all prerequisites are installed
3. Try the alternative setup script
4. Create an issue in the repository with error details