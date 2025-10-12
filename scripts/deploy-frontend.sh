#!/bin/bash
# Frontend Deployment Script
# Builds and prepares frontend for production deployment

set -e  # Exit on error

echo "🚀 TaskifAI Frontend Deployment"
echo "================================"
echo ""

# Check we're in the right directory
if [ ! -f "frontend/package.json" ]; then
    echo "❌ Error: Run this script from the project root directory"
    exit 1
fi

cd frontend

# Verify environment configuration
echo "📋 Checking environment configuration..."
if ! grep -q "taskifai-demo-ak4kq.ondigitalocean.app" .env; then
    echo "❌ Error: .env file not configured for production"
    echo "   Expected VITE_API_URL=https://taskifai-demo-ak4kq.ondigitalocean.app"
    exit 1
fi
echo "✅ Environment configured for production"
echo ""

# Install dependencies
echo "📦 Installing dependencies..."
npm install
echo ""

# Build for production
echo "🔨 Building frontend..."
npm run build
echo ""

# Verify build
if [ ! -d "dist" ] || [ ! -f "dist/index.html" ]; then
    echo "❌ Error: Build failed - dist directory not created"
    exit 1
fi
echo "✅ Build successful"
echo ""

# Show build info
echo "📊 Build Information:"
echo "   Output directory: frontend/dist/"
echo "   Files to deploy:"
ls -lh dist/ | tail -n +2
echo ""

echo "✅ Frontend ready for deployment!"
echo ""
echo "📤 Next Steps:"
echo "1. Upload contents of frontend/dist/ to your static hosting"
echo "2. For DigitalOcean Spaces:"
echo "   - Use DigitalOcean Control Panel > Spaces"
echo "   - Upload all files from dist/ directory"
echo "   - Set cache headers appropriately"
echo "3. Clear browser cache: Open console and run:"
echo "   localStorage.clear(); location.reload();"
echo "4. Test login at: https://demo.taskifai.com"
