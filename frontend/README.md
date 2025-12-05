# AgroRisk Copilot - Frontend

A simple, responsive web interface for the AgroRisk agricultural risk assessment system.

## Features

- **Risk Assessment Form**: Select region, district, crop, and optional month
- **Visual Risk Display**: Color-coded risk scores (🟢 Low, 🟡 Medium, 🔴 High)
- **Contributing Factors**: Top 5 factors affecting the risk score
- **Current Conditions**: Real-time weather and vegetation data
- **Crop Recommendations**: Alternative crops with better conditions
- **Regional Heatmap**: Interactive Leaflet map showing risk levels across districts
- **Bilingual Support**: Displays crop names in both English and Uzbek

## Technology Stack

- **HTML/CSS/JavaScript**: Pure vanilla JS, no build tools required
- **Leaflet.js**: Interactive maps via CDN
- **FastAPI Static Files**: Served directly by the API server

## Quick Start

1. **Start the API server** (from project root):
   ```bash
   cd api
   python main.py
   ```
   or
   ```bash
   uvicorn api.main:app --reload
   ```

2. **Access the frontend**:
   - Open browser to: `http://localhost:8000`
   - Or directly: `http://localhost:8000/static/index.html`

3. **Use the app**:
   - Select a region (e.g., "Tashkent Region")
   - Select a district (e.g., "Chirchiq")
   - Select a crop (e.g., "cotton")
   - (Optional) Select a specific month
   - Click "Check Risk"
   - View results and explore the regional map

## File Structure

```
frontend/
├── index.html    # Main HTML structure
├── style.css     # Responsive styling with risk color coding
├── app.js        # API integration and interactivity
└── README.md     # This file
```

## API Endpoints Used

- `GET /regions` - List all regions
- `GET /districts/{region}` - List districts in a region
- `GET /crops` - List all available crops
- `POST /predict` - Get risk assessment
- `GET /batch-predict` - Get predictions for all districts in a region (for map)

## Color Coding

- **🟢 Green (70-100)**: Low risk, good conditions for the crop
- **🟡 Yellow (40-69)**: Medium risk, proceed with caution
- **🔴 Red (0-39)**: High risk, not recommended

## Browser Support

- Chrome/Edge (latest)
- Firefox (latest)
- Safari (latest)
- Mobile browsers (responsive design)

## Customization

### Change API URL
Edit `app.js` line 2:
```javascript
const API_BASE_URL = 'http://your-api-url:port';
```

### Modify Colors
Edit `style.css` color variables for green/yellow/red themes.

### Add Languages
Extend the bilingual display in `app.js` by adding more translations.

## Troubleshooting

**Problem**: "Failed to load regions"
- **Solution**: Check that the API server is running on port 8000

**Problem**: Map not displaying
- **Solution**: Check browser console for Leaflet errors, ensure internet connection for CDN

**Problem**: Predictions failing
- **Solution**: Verify the model file exists at `models/agrorisk_model.joblib`

## Development

No build process needed! Just edit the files and refresh the browser.

For development with auto-reload:
```bash
# Use a simple HTTP server (alternative)
python -m http.server 8080
```

## Production Deployment

For production, consider:
1. Minifying CSS/JS files
2. Using a CDN for better performance
3. Adding authentication if needed
4. Setting up HTTPS
5. Caching static assets

## License

Part of the AgroRisk Copilot project.
