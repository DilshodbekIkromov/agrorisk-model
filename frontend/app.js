// API Configuration
const API_BASE_URL = 'http://localhost:5002/api';

// Global state
let currentRegion = null;
let currentCrop = null;
let leafletMap = null;
let currentAgroScore = 0;
let currentAssessmentId = null;
let currentApplicationId = null;

// DOM Elements
const regionSelect = document.getElementById('region');
const districtSelect = document.getElementById('district');
const cropSelect = document.getElementById('crop');
const riskForm = document.getElementById('riskForm');
const loadingDiv = document.getElementById('loading');
const resultsSection = document.getElementById('resultsSection');
const mapSection = document.getElementById('mapSection');
const showMapBtn = document.getElementById('showMapBtn');
const closeMapBtn = document.getElementById('closeMapBtn');
const btnProceedToLoan = document.getElementById('btnProceedToLoan');
const loanSection = document.getElementById('loanSection');
const loanForm = document.getElementById('loanForm');

// Initialize the app
async function init() {
    await loadRegions();
    await loadCrops();
    setupEventListeners();
}

// Setup event listeners
function setupEventListeners() {
    regionSelect.addEventListener('change', handleRegionChange);
    riskForm.addEventListener('submit', handleFormSubmit);
    showMapBtn.addEventListener('click', showRegionalMap);
    closeMapBtn.addEventListener('click', hideMap);

    if (btnProceedToLoan) {
        btnProceedToLoan.addEventListener('click', () => {
            loanSection.classList.remove('hidden');
            loanSection.scrollIntoView({ behavior: 'smooth' });
        });
    }

    if (loanForm) {
        loanForm.addEventListener('submit', handleLoanCalculation);
    }
}

// Load regions from API
async function loadRegions() {
    try {
        const response = await fetch(`${API_BASE_URL}/regions`);
        const data = await response.json();
        
        regionSelect.innerHTML = '<option value="">Select a region...</option>';
        data.regions.forEach(region => {
            const option = document.createElement('option');
            option.value = region;
            option.textContent = region;
            regionSelect.appendChild(option);
        });
    } catch (error) {
        console.error('Error loading regions:', error);
        showError('Failed to load regions. Please check if the API is running.');
    }
}

// Load crops from API
async function loadCrops() {
    try {
        const response = await fetch(`${API_BASE_URL}/crops`);
        const data = await response.json();
        
        cropSelect.innerHTML = '<option value="">Select a crop...</option>';
        data.crops.forEach(crop => {
            const option = document.createElement('option');
            option.value = crop.name;
            option.textContent = `${crop.name_uz} (${crop.name})`;
            cropSelect.appendChild(option);
        });
    } catch (error) {
        console.error('Error loading crops:', error);
        showError('Failed to load crops.');
    }
}

// Handle region change - load districts
async function handleRegionChange(e) {
    const region = e.target.value;
    currentRegion = region;
    
    if (!region) {
        districtSelect.disabled = true;
        districtSelect.innerHTML = '<option value="">Select a region first...</option>';
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}/districts/${encodeURIComponent(region)}`);
        const data = await response.json();
        
        districtSelect.disabled = false;
        districtSelect.innerHTML = '<option value="">Select a district...</option>';
        data.districts.forEach(district => {
            const option = document.createElement('option');
            option.value = district;
            option.textContent = district;
            districtSelect.appendChild(option);
        });
    } catch (error) {
        console.error('Error loading districts:', error);
        showError('Failed to load districts.');
    }
}

// Handle form submission
async function handleFormSubmit(e) {
    e.preventDefault();
    
    const region = regionSelect.value;
    const district = districtSelect.value;
    const crop = cropSelect.value;
    
    if (!region || !district || !crop) {
        showError('Please fill in all required fields.');
        return;
    }
    
    currentCrop = crop;
    
    // Show loading
    loadingDiv.classList.remove('hidden');
    resultsSection.classList.add('hidden');
    mapSection.classList.add('hidden');
    
    try {
        // Build request body
        const requestBody = {
            region: region,
            district: district,
            crop: crop
        };
        
        const response = await fetch(`${API_BASE_URL}/predict`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestBody)
        });
        
        if (!response.ok) {
            throw new Error('Prediction failed');
        }
        
        const data = await response.json();
        displayResults(data);
    } catch (error) {
        console.error('Error making prediction:', error);
        showError('Failed to get prediction. Please try again.');
    } finally {
        loadingDiv.classList.add('hidden');
    }
}

// Display prediction results
function displayResults(data) {
    // Update risk score circle
    const riskScoreCircle = document.getElementById('riskScoreCircle');
    const riskScoreValue = document.getElementById('riskScoreValue');
    const riskStatus = document.getElementById('riskStatus');
    const riskConfidence = document.getElementById('riskConfidence');
    
    riskScoreValue.textContent = Math.round(data.risk_score);

    // store score and assessment ID for loan flow
    currentAgroScore = data.risk_score;
    currentAssessmentId = data.assessment_id;
    
    // Set color class
    riskScoreCircle.className = 'risk-circle ' + data.risk_category;
    riskStatus.className = 'risk-status ' + data.risk_category;
    
    // Set status text
    const statusEmoji = {
        'green': '✅',
        'yellow': '⚠️',
        'red': '🚫'
    };
    riskStatus.textContent = `${statusEmoji[data.risk_category]} ${getRiskStatusText(data.risk_score)}`;
    
    // Set confidence
    riskConfidence.textContent = `Confidence: ${data.confidence || 'High'}`;
    
    // Update location info
    document.getElementById('locationText').textContent = `${data.location_info.region} / ${data.location_info.district}`;
    document.getElementById('cropText').textContent = `${data.crop_info.name_uz} (${data.crop_info.name})`;
    
    // Display top factors
    displayFactors(data.top_factors);
    
    // Display current conditions
    displayConditions(data.location_info.current_conditions);
    
    // Display recommendations
    if (data.recommendations && data.recommendations.length > 0) {
        displayRecommendations(data.recommendations);
    }

    // allow proceed to loan section after scoring
    if (btnProceedToLoan) {
        btnProceedToLoan.classList.remove('hidden');
    }
    
    // Show results section
    resultsSection.classList.remove('hidden');
    
    // Scroll to results
    resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

// Loan calculation handler
async function handleLoanCalculation(e) {
    e.preventDefault();

    if (!currentAssessmentId) {
        showError('Please complete crop risk assessment first');
        return;
    }

    // Gather form data
    const loanData = {
        assessment_id: currentAssessmentId,
        farmer_name: document.getElementById('farmerName').value,
        passport_id: document.getElementById('passportId').value,
        phone: document.getElementById('phoneNumber').value,
        years_farming: parseInt(document.getElementById('yearsFarming').value || 0),
        land_area: parseFloat(document.getElementById('landArea').value || 0),
        land_ownership: document.getElementById('landOwnership').value,
        loan_amount: parseFloat(document.getElementById('loanAmount').value || 0),
        loan_term: parseInt(document.getElementById('loanTerm').value || 12),
        annual_revenue: parseFloat(document.getElementById('annualRevenue').value || 0),
        net_profit: parseFloat(document.getElementById('netProfit').value || 0),
        total_assets: parseFloat(document.getElementById('totalAssets').value || 1),
        total_debt: parseFloat(document.getElementById('totalDebt').value || 0),
        collateral_value: parseFloat(document.getElementById('collateralValue').value || 0),
        previous_defaults: document.getElementById('previousDefaults').value === '1'
    };

    try {
        // Show loading
        loadingDiv.classList.remove('hidden');

        // Submit to Flask backend
        const response = await fetch(`${API_BASE_URL}/loan/submit`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(loanData)
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Failed to submit loan application');
        }

        const result = await response.json();
        currentApplicationId = result.application_id;

        // Display results
        displayCreditDecision(result);

    } catch (error) {
        console.error('Loan submission error:', error);
        showError('Failed to process loan application: ' + error.message);
    } finally {
        loadingDiv.classList.add('hidden');
    }
}

function displayCreditDecision(result) {
    const resultSection = document.getElementById('creditResultSection');
    const scoreDisplay = document.getElementById('creditScoreDisplay');
    const factorsDisplay = document.getElementById('creditFactors');

    let decision = result.decision.replace('_', ' ');
    let color = '#f39c12';

    if (result.decision === 'APPROVED') {
        color = '#27ae60';
    } else if (result.decision === 'REJECTED') {
        color = '#c0392b';
    }

    scoreDisplay.innerHTML = `
        <div class="risk-circle" style="background: ${color}">
            <span class="risk-score-value">${result.final_score}</span>
            <span class="risk-score-label">Credit Score</span>
        </div>
        <div class="risk-info">
            <h3 class="risk-status" style="color:${color}">${decision}</h3>
            <p class="risk-confidence">Agro Score: ${Math.round(result.agro_score)} | Financial Score: ${Math.round(result.financial_score)}</p>
            <p class="risk-confidence">Application ID: #${result.application_id}</p>
        </div>
    `;

    factorsDisplay.innerHTML = `
        <h3>Key Financial Ratios</h3>
        <div class="factor-row"><span>Collateral Coverage</span><strong>${result.factors.collateral_coverage}%</strong></div>
        <div class="factor-row"><span>Debt-to-Asset Ratio</span><strong>${result.factors.debt_to_asset_ratio}%</strong></div>
        <div class="factor-row"><span>Profit Margin</span><strong>${result.factors.profit_margin}%</strong></div>
        <div style="margin-top: 20px; text-align: center;">
            <button onclick="downloadPDF(${result.application_id})" class="submit-btn primary">
                📄 Download Full Report (PDF)
            </button>
        </div>
    `;

    resultSection.classList.remove('hidden');
    resultSection.scrollIntoView({ behavior: 'smooth' });
}

function downloadPDF(applicationId) {
    window.open(`${API_BASE_URL}/loan/download/${applicationId}`, '_blank');
}

// Display top contributing factors
function displayFactors(factors) {
    const factorsList = document.getElementById('factorsList');
    factorsList.innerHTML = '';
    
    if (!factors || factors.length === 0) {
        factorsList.innerHTML = '<li>No factor data available</li>';
        return;
    }
    
    factors.forEach(factor => {
        const li = document.createElement('li');
        
        const nameSpan = document.createElement('span');
        nameSpan.className = 'factor-name';
        nameSpan.textContent = formatFactorName(factor.feature);
        
        const valueSpan = document.createElement('span');
        valueSpan.className = 'factor-value';
        valueSpan.textContent = `Impact: ${factor.contribution.toFixed(1)}%`;
        
        const directionSpan = document.createElement('span');
        directionSpan.className = `factor-direction ${factor.direction === 'increases' ? 'increase' : 'decrease'}`;
        directionSpan.textContent = factor.direction === 'increases' ? '↑ Increases' : '↓ Decreases';
        
        li.appendChild(nameSpan);
        li.appendChild(valueSpan);
        li.appendChild(directionSpan);
        
        factorsList.appendChild(li);
    });
}

// Display current conditions
function displayConditions(conditions) {
    const conditionsGrid = document.getElementById('conditionsGrid');
    conditionsGrid.innerHTML = '';
    
    if (!conditions) {
        conditionsGrid.innerHTML = '<p>No condition data available</p>';
        return;
    }
    
    const conditionItems = [
        { label: 'Temperature', value: conditions.temperature, unit: '°C', icon: '🌡️' },
        { label: 'NDVI', value: conditions.ndvi, unit: '', icon: '🌱' },
        { label: 'Precipitation', value: conditions.precipitation, unit: 'mm', icon: '💧' }
    ];
    
    conditionItems.forEach(item => {
        const card = document.createElement('div');
        card.className = 'condition-card';
        
        card.innerHTML = `
            <h4>${item.icon} ${item.label}</h4>
            <div class="condition-value">
                ${typeof item.value === 'number' ? item.value.toFixed(2) : '--'}
                <span class="condition-unit">${item.unit}</span>
            </div>
        `;
        
        conditionsGrid.appendChild(card);
    });
}

// Display crop recommendations
function displayRecommendations(recommendations) {
    const recommendationsSection = document.getElementById('recommendationsSection');
    const recommendationsList = document.getElementById('recommendationsList');
    
    recommendationsList.innerHTML = '';
    
    recommendations.forEach(rec => {
        const card = document.createElement('div');
        card.className = 'recommendation-card';
        
        const scoreClass = rec.risk_score >= 70 ? 'green' : rec.risk_score >= 40 ? 'yellow' : 'red';
        
        card.innerHTML = `
            <h4>${rec.crop}</h4>
            <div class="recommendation-score ${scoreClass}">
                ${Math.round(rec.risk_score)}
            </div>
            <p class="recommendation-reason">${rec.reason || 'Alternative crop option'}</p>
        `;
        
        recommendationsList.appendChild(card);
    });
    
    recommendationsSection.classList.remove('hidden');
}

// Show regional map
async function showRegionalMap() {
    if (!currentRegion || !currentCrop) {
        showError('Please submit a prediction first.');
        return;
    }
    
    mapSection.classList.remove('hidden');
    
    // Initialize map if not already done
    if (!leafletMap) {
        leafletMap = L.map('map').setView([41.3775, 64.5853], 7);
        
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© OpenStreetMap contributors',
            maxZoom: 19
        }).addTo(leafletMap);
    }
    
    // Fetch batch predictions
    try {
        const url = `${API_BASE_URL}/batch-predict?region=${encodeURIComponent(currentRegion)}&crop=${encodeURIComponent(currentCrop)}`;
        
        const response = await fetch(url);
        const data = await response.json();
        
        // Clear existing markers
        leafletMap.eachLayer(layer => {
            if (layer instanceof L.CircleMarker) {
                leafletMap.removeLayer(layer);
            }
        });
        
        // Add markers for each district
        if (data.districts && data.districts.length > 0) {
            const bounds = [];
            
            data.districts.forEach(district => {
                const color = district.risk_category === 'green' ? '#28a745' : 
                             district.risk_category === 'yellow' ? '#ffc107' : '#dc3545';
                
                const marker = L.circleMarker([district.latitude, district.longitude], {
                    radius: 10,
                    fillColor: color,
                    color: '#fff',
                    weight: 2,
                    opacity: 1,
                    fillOpacity: 0.8
                }).addTo(leafletMap);
                
                marker.bindPopup(`
                    <strong>${district.district}</strong><br>
                    Risk Score: ${Math.round(district.risk_score)}<br>
                    Status: ${district.risk_category.toUpperCase()}
                `);
                
                bounds.push([district.latitude, district.longitude]);
            });
            
            // Fit map to show all markers
            if (bounds.length > 0) {
                leafletMap.fitBounds(bounds, { padding: [50, 50] });
            }
        }
    } catch (error) {
        console.error('Error loading map data:', error);
        showError('Failed to load regional map data.');
    }
    
    // Scroll to map
    mapSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
    
    // Invalidate map size (fixes display issues)
    setTimeout(() => {
        if (leafletMap) {
            leafletMap.invalidateSize();
        }
    }, 100);
}

// Hide map
function hideMap() {
    mapSection.classList.add('hidden');
}

// Helper function to format factor names
function formatFactorName(feature) {
    const nameMap = {
        'region_suitable': 'Region Suitability',
        'ndvi_score': 'Vegetation Health (NDVI)',
        'temp_match': 'Temperature Match',
        'water_match': 'Water Availability',
        'crop_drought_sens': 'Drought Sensitivity',
        'crop_frost_sens': 'Frost Sensitivity',
        'precipitation_annual_mm': 'Annual Precipitation',
        'lst_mean_c': 'Land Surface Temperature',
        'ndvi_mean': 'NDVI Mean'
    };
    
    return nameMap[feature] || feature.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
}

// Get risk status text
function getRiskStatusText(score) {
    if (score >= 70) return 'Low Risk - Good Conditions';
    if (score >= 40) return 'Medium Risk - Proceed with Caution';
    return 'High Risk - Not Recommended';
}

// Show error message
function showError(message) {
    alert(message);
}

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', init);
