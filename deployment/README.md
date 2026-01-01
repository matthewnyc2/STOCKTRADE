# Frontend Production Deployment

This directory contains all the configuration files and scripts for deploying the frontend to production.

## Configuration Files

### 1. `next.config.js`
Updated for production with optimizations:
- **Standalone output**: Enables serverless deployment
- **Image optimization**: WebP/AVIF support, responsive images
- **Compression**: Enabled for smaller bundle sizes
- **Source maps**: Disabled for production
- **Security headers**: X-Frame-Options, X-Content-Type-Options
- **Bundle optimization**: SWC minification, package imports

### 2. `Dockerfile`
Multi-stage build for optimized Docker image:
- **Builder stage**: Node.js 18 Alpine for building
- **Runner stage**: Nginx for serving
- **Security**: Non-root user
- **Optimizations**: Gzip compression, caching headers
- **Health checks**: Application health monitoring

### 3. `vercel.json`
Vercel deployment configuration:
- **Environment variables**: Production settings
- **Build optimization**: Cached static assets
- **Routing**: Custom redirects and rewrites
- **Analytics**: Built-in performance monitoring
- **Regions**: Optimized for Asian and US markets

### 4. `.env.production.template`
Production environment variables template:
- **API Configuration**: Endpoints and keys
- **Feature flags**: Toggle functionality
- **Performance**: Caching and optimization settings
- **Security**: CORS, headers, rate limiting
- **Third-party services**: Analytics, monitoring

### 5. `package.json`
Updated with production scripts:
- `build:prod`: Full production build pipeline
- `build:export`: Static export capability
- `docker:build`: Docker image creation
- `deploy:vercel`: Vercel deployment
- `type-check`: TypeScript validation

## Deployment Options

### Option 1: Vercel (Recommended)
```bash
# Install Vercel CLI
npm install -g vercel

# Deploy to production
vercel --prod

# Deploy preview branch
vercel
```

### Option 2: Docker
```bash
# Build Docker image
npm run docker:build

# Run with Docker Compose
docker-compose -f docker-compose.prod.yml up

# Build and push to registry
npm run docker:build && docker push your-registry/crypto-quant-lab-frontend
```

### Option 3: Automated Deployment
```bash
# Run the deployment script
chmod +x deploy.sh
./deploy.sh
```

## Deployment Process

1. **Pre-deployment Checklist**
   - Update `.env.production` with production values
   - Verify API endpoints are accessible
   - Check environment variables
   - Run local tests

2. **Build Process**
   ```bash
   # Full production build
   npm run build:prod

   # Check build size
   npm run build:analyze
   ```

3. **Deployment**
   - Choose deployment target (Vercel/Docker)
   - Execute deployment script
   - Monitor deployment logs
   - Verify application health

4. **Post-deployment**
   - Check application URLs
   - Verify API connectivity
   - Monitor performance metrics
   - Set up monitoring alerts

## Environment Variables

### Required
- `NODE_ENV=production`
- `API_URL=production-api-endpoint`
- `WS_URL=websocket-endpoint`

### Optional
- `SENTRY_DSN=error-tracking-dsn`
- `GOOGLE_ANALYTICS_ID=analytics-id`
- `FEATURE_FLAG_*`
- `CACHE_TTL=3600`

## Monitoring and Logging

### Vercel
- Built-in analytics and monitoring
- Performance metrics
- Error tracking
- Real-time logs

### Docker
- Health checks configured
- Nginx access/error logs
- Application performance monitoring
- Custom logging configuration

## Performance Optimizations

### Bundle Optimization
- Code splitting enabled
- Lazy loading for components
- Image optimization (WebP/AVIF)
- Gzip compression
- Caching headers

### Load Time
- Preconnect to external domains
- Critical CSS inlining
- Font loading optimization
- Resource hints

## Security

### Headers
- X-Frame-Options: DENY
- X-Content-Type-Options: nosniff
- X-XSS-Protection: 1; mode=block
- Referrer-Policy: strict-origin-when-cross-origin

### Docker Security
- Non-root user
- Read-only filesystem where possible
- Health checks
- Limited container privileges

## Troubleshooting

### Common Issues
1. **Build fails**: Check for TypeScript errors
2. **Deployment timeout**: Check package size
3. **API errors**: Verify environment variables
4. **Performance issues**: Check bundle analyzer

### Debug Commands
```bash
# Check build output
npm run build

# Analyze bundle size
npm run build:analyze

# Run Docker locally
docker-compose -f docker-compose.prod.yml up
```

## Contributing

When updating deployment configuration:
1. Test changes in staging environment
2. Update this documentation
3. Verify all tests pass
4. Test deployment process

## Support

For deployment issues:
1. Check Vercel/Docker logs
2. Verify environment variables
3. Review network configuration
4. Check API endpoints

## Next Steps

- Set up CI/CD pipeline
- Configure automated deployments
- Implement blue-green deployment
- Set up canary releases
- Configure A/B testing