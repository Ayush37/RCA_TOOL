# Certificate Directory

Place your Azure Service Principal certificate file here.

## Required Certificate
- **File name**: `apim-exp.pem` (or update the path in `.env`)
- **Format**: PEM format certificate
- **Purpose**: Used for Azure AD authentication to access Azure OpenAI

## How to obtain the certificate:
1. Create an Azure Service Principal
2. Generate a certificate for the Service Principal
3. Export the certificate in PEM format
4. Place it in this directory

## Security Note
- Never commit the actual certificate file to version control
- Add `*.pem` and `*.pfx` to your `.gitignore`
- Keep the certificate file secure and restrict access