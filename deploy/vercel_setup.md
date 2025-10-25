# Vercel Deployment Guide for SonicMuse Frontend

## Prerequisites

- Vercel account (free tier available)
- GitHub repository with frontend code
- Backend API deployed and accessible

## Step 1: Prepare Frontend for Production

### 1.1 Update Environment Variables
Create `.env.production` file:
```env
VITE_API_BASE=https://your-api-domain.com/api
```

### 1.2 Update API Configuration
Ensure your `src/api.ts` uses the environment variable:
```typescript
const API_BASE_URL = import.meta.env.VITE_API_BASE || 'http://localhost:8000';
```

### 1.3 Build Configuration
Update `vite.config.ts` if needed:
```typescript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  build: {
    outDir: 'dist',
    sourcemap: false,
    minify: 'terser',
  },
  server: {
    port: 5173,
  }
})
```

## Step 2: Deploy to Vercel

### Method 1: Vercel CLI (Recommended)

#### 2.1 Install Vercel CLI
```bash
npm install -g vercel
```

#### 2.2 Login to Vercel
```bash
vercel login
```

#### 2.3 Deploy from Frontend Directory
```bash
cd frontend
vercel
```

Follow the prompts:
- **Set up and deploy?** Yes
- **Which scope?** Your account
- **Link to existing project?** No (for first deployment)
- **What's your project's name?** sonicmuse-frontend
- **In which directory is your code located?** ./
- **Want to override the settings?** No

#### 2.4 Set Environment Variables
```bash
vercel env add VITE_API_BASE
# Enter: https://your-api-domain.com/api
```

#### 2.5 Deploy to Production
```bash
vercel --prod
```

### Method 2: GitHub Integration

#### 2.1 Connect GitHub Repository
1. Go to [Vercel Dashboard](https://vercel.com/dashboard)
2. Click "New Project"
3. Import your GitHub repository
4. Select the frontend folder as root directory

#### 2.2 Configure Build Settings
- **Framework Preset**: Vite
- **Root Directory**: frontend
- **Build Command**: npm run build
- **Output Directory**: dist

#### 2.3 Set Environment Variables
In Vercel dashboard:
1. Go to Project Settings
2. Navigate to Environment Variables
3. Add:
   - **Name**: VITE_API_BASE
   - **Value**: https://your-api-domain.com/api
   - **Environment**: Production, Preview, Development

#### 2.4 Deploy
Click "Deploy" button

## Step 3: Configure Custom Domain (Optional)

### 3.1 Add Domain in Vercel
1. Go to Project Settings → Domains
2. Add your custom domain (e.g., sonicmuse.com)
3. Follow DNS configuration instructions

### 3.2 Update DNS Records
Add CNAME record pointing to your Vercel deployment:
```
Type: CNAME
Name: www
Value: cname.vercel-dns.com
```

### 3.3 Update API CORS
Update your backend CORS settings to include the new domain:
```env
CORS_ALLOW_ORIGINS=https://your-domain.com,https://www.your-domain.com
```

## Step 4: Verify Deployment

### 4.1 Test Frontend
1. Visit your Vercel deployment URL
2. Test audio upload functionality
3. Test script mode
4. Verify API calls are working

### 4.2 Check Console for Errors
1. Open browser developer tools
2. Check Console tab for any errors
3. Check Network tab for API calls

### 4.3 Test Different Browsers
- Chrome
- Firefox
- Safari
- Edge

## Step 5: Production Optimizations

### 5.1 Enable Analytics
In Vercel dashboard:
1. Go to Analytics tab
2. Enable Web Analytics
3. Monitor performance metrics

### 5.2 Setup Monitoring
Add error tracking (optional):
```bash
npm install @sentry/react @sentry/tracing
```

### 5.3 Optimize Images
If you add images later:
```bash
npm install vite-plugin-imagemin
```

## Step 6: CI/CD Setup

### 6.1 Automatic Deployments
Vercel automatically deploys when you push to:
- **main branch**: Production deployment
- **other branches**: Preview deployments

### 6.2 GitHub Actions (Optional)
Create `.github/workflows/deploy.yml`:
```yaml
name: Deploy to Vercel
on:
  push:
    branches: [main]
    paths: ['frontend/**']

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-node@v2
        with:
          node-version: '18'
      - run: cd frontend && npm ci
      - run: cd frontend && npm run build
      - uses: amondnet/vercel-action@v20
        with:
          vercel-token: ${{ secrets.VERCEL_TOKEN }}
          vercel-org-id: ${{ secrets.ORG_ID }}
          vercel-project-id: ${{ secrets.PROJECT_ID }}
          working-directory: ./frontend
```

## Troubleshooting

### Common Issues

1. **Build Failures**:
   ```bash
   # Check build locally
   cd frontend
   npm run build
   
   # Check for TypeScript errors
   npm run type-check
   ```

2. **Environment Variables Not Working**:
   - Ensure variables start with `VITE_`
   - Redeploy after adding new variables
   - Check variable names match exactly

3. **API Connection Issues**:
   - Verify API URL is correct
   - Check CORS settings on backend
   - Test API endpoint directly

4. **Performance Issues**:
   - Enable Vercel Analytics
   - Check bundle size with `npm run build -- --analyze`
   - Optimize images and assets

### Debug Commands

```bash
# Check Vercel CLI version
vercel --version

# View deployment logs
vercel logs

# Check project status
vercel ls

# Remove deployment
vercel remove
```

## Cost Considerations

### Vercel Free Tier Limits
- **Bandwidth**: 100GB/month
- **Build minutes**: 6,000/month
- **Serverless functions**: 100GB-hours/month
- **Custom domains**: Unlimited

### Optimization Tips
1. **Enable compression** in Vite config
2. **Use CDN** for static assets
3. **Optimize images** before upload
4. **Monitor usage** in Vercel dashboard

## Security Best Practices

1. **Environment Variables**:
   - Never commit `.env` files
   - Use Vercel's environment variable system
   - Rotate API keys regularly

2. **API Security**:
   - Use HTTPS for all API calls
   - Implement rate limiting
   - Validate all inputs

3. **Content Security Policy**:
   ```typescript
   // Add to vite.config.ts
   export default defineConfig({
     plugins: [react()],
     server: {
       headers: {
         'Content-Security-Policy': "default-src 'self'; script-src 'self' 'unsafe-inline'"
       }
     }
   })
   ```

## Monitoring and Maintenance

### 1. Regular Updates
```bash
# Update dependencies
npm update

# Check for security vulnerabilities
npm audit
```

### 2. Performance Monitoring
- Use Vercel Analytics
- Monitor Core Web Vitals
- Check bundle size regularly

### 3. Backup Strategy
- Keep GitHub repository updated
- Export environment variables
- Document deployment process
