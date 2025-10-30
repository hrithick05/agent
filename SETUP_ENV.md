# Environment Variables Setup Guide

This project uses environment variables for configuration. Follow these steps to set up your `.env` file.

## Quick Setup

1. **Create a `.env` file in the project root** (same directory as this README)

2. **Copy the format from `ENV_TEMPLATE.txt`** or use the template below:

## Environment Variables Format

Create a file named `.env` in the project root with the following content:

```env
# Google Gemini API Configuration
GEMINI_API_KEY=AIzaSyBx3YFnU4tpVPW73nM53s6ki2ZN7n_qCDw

# Supabase Database Configuration
SUPABASE_URL=https://whfjofihihlhctizchmj.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6IndoZmpvZmloaWhsaGN0aXpjaG1qIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjEzNzQzNDMsImV4cCI6MjA3Njk1MDM0M30.OsJnOqeJgT5REPg7uxkGmmVcHIcs5QO4vdyDi66qpR0

# Supabase table name (optional, defaults to 'scraped_products')
SUPABASE_TABLE_NAME=scraped_products
```

## Step-by-Step Instructions

### Option 1: Manual Creation

1. Open a text editor (Notepad, VS Code, etc.)
2. Create a new file named `.env` in the project root directory
3. Copy and paste the content above
4. Save the file

### Option 2: Using Command Line (Windows PowerShell)

```powershell
# Navigate to project root
cd E:\Missile-ClassicV1-main

# Create .env file from template
Copy-Item ENV_TEMPLATE.txt .env

# Edit the .env file with your preferred editor
notepad .env
```

### Option 3: Using Command Line (Linux/Mac)

```bash
# Navigate to project root
cd /path/to/Missile-ClassicV1-main

# Create .env file from template
cp ENV_TEMPLATE.txt .env

# Edit the .env file
nano .env
```

## Variable Descriptions

### `GEMINI_API_KEY`
- **Required**: Yes
- **Description**: Your Google Gemini API key
- **How to get**: 
  1. Go to https://ai.google.dev/
  2. Sign in with your Google account
  3. Create an API key
  4. Copy the key and paste it here
- **Default**: Already set in code (but you can override with env var)

### `SUPABASE_URL`
- **Required**: Yes (for saving to database)
- **Description**: Your Supabase project URL
- **How to get**:
  1. Go to https://supabase.com/dashboard
  2. Select your project
  3. Go to Settings > API
  4. Copy the "Project URL"
- **Default**: Already set in code

### `SUPABASE_KEY`
- **Required**: Yes (for saving to database)
- **Description**: Your Supabase API key (anon/public key)
- **How to get**:
  1. Go to https://supabase.com/dashboard
  2. Select your project
  3. Go to Settings > API > Project API keys
  4. Copy the "anon" or "public" key (NOT the service_role key)
- **Default**: Already set in code

### `SUPABASE_TABLE_NAME`
- **Required**: No
- **Description**: The name of the table where scraped products will be saved
- **Default**: `scraped_products`

## Important Notes

- **No quotes needed**: Don't add quotes around values (e.g., `KEY="value"` is wrong)
- **No spaces**: Don't add spaces around the `=` sign
- **One line per variable**: Each variable should be on its own line
- **Comments**: Lines starting with `#` are comments and ignored

## Verification

After creating your `.env` file, the `langgraph_agent.py` will automatically load these variables when it runs. The script will:

1. First check for environment variables set in the system
2. Then check for values in the `.env` file
3. Finally, use hardcoded defaults if neither is found

You can verify it's working by running:
```bash
python AgentModule/langgraph_agent.py
```

If everything is set up correctly, the agent should run without errors about missing API keys.

