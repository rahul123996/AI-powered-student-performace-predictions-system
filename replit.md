# Academic Performance Prediction System

## Overview
This is an AI-powered Academic Decision Support System that predicts student academic performance using machine learning. The system helps identify at-risk students early and provides personalized recommendations for improvement.

## Purpose
- **Predict student performance** into categories: Strong, Needs Improvement, and At-Risk
- **Provide personalized study recommendations** based on individual performance patterns
- **Identify weak areas** subject-wise for targeted intervention
- **Generate comprehensive reports** for faculty and administration
- **Enable early intervention** for struggling students

## Current State
The application is fully functional with three role-based dashboards:

### 1. Student Dashboard (`/student`)
- Individual performance prediction
- Personalized study recommendations
- Subject-wise performance analysis
- Attendance and assignment tracking
- Clear visual indicators for weak areas

### 2. Teacher Dashboard (`/teacher`)
- Batch upload (CSV/Excel) for up to 200 students
- Class-wide analytics with visualizations
- Top 10 and Bottom 10 student rankings
- Early risk alerts for at-risk students
- PDF/Excel report export functionality
- Subject-wise class performance analysis

### 3. Admin Dashboard (`/admin`)
- System-wide oversight
- Batch management
- Historical data access
- System configuration view

## Key Features Implemented
✓ Academic performance prediction (Strong / Needs Improvement / At-Risk)
✓ Personalized study improvement recommendations  
✓ Subject-wise performance analysis
✓ Class average comparison and performance trends
✓ Early risk alerts for low-performing students
✓ Attendance impact analysis (75% threshold)
✓ Assignment completion tracking
✓ Visual analytics with pie charts and bar graphs
✓ PDF report generation with professional formatting
✓ Excel export with multiple sheets
✓ Batch processing for entire classes
✓ Role-based access control

## Project Structure
```
├── app.py                      # Main Flask application
├── model.py                    # ML model training script
├── student_model.pkl           # Trained RandomForest model
├── student_data.csv           # Training data
├── sample_class_data.csv      # Sample data template
├── templates/
│   ├── index.html             # Home page with dashboard links
│   ├── student_dashboard.html  # Student interface
│   ├── teacher_dashboard.html  # Teacher interface
│   └── admin_dashboard.html    # Admin interface
├── static/
│   ├── style.css              # Styling
│   └── logo.png               # University logo
├── uploads/                    # Uploaded CSV files
└── reports/                    # Generated PDF/Excel reports
```

## Technology Stack
- **Backend**: Flask (Python 3.11)
- **ML Model**: scikit-learn RandomForestClassifier
- **Data Processing**: pandas, numpy
- **Visualization**: matplotlib, seaborn
- **Reports**: reportlab (PDF), openpyxl (Excel)
- **Deployment**: Gunicorn WSGI server

## Data Schema
### Required CSV Columns for Batch Upload:
- `StudentID`: Unique identifier
- `Name`: Student name
- `Subject1` - `Subject8`: Subject marks (8 subjects, 100 marks each)
- `Attendance`: Percentage (0-100)
- `Assignments`: Number completed (0-10)

### Subject Configuration:
The system uses 8 generic subjects (Subject1-Subject8), each with a maximum of 100 marks.
- Total Maximum Marks: 800
- You can customize subject names in the app.py SUBJECT_NAMES dictionary

**Sample CSV Format** (see `sample_class_data.csv`):
```
StudentID,Name,Subject1,Subject2,Subject3,Subject4,Subject5,Subject6,Subject7,Subject8,Attendance,Assignments
S001,John Smith,85,90,78,82,75,88,92,86,92,9
```

## Machine Learning Model
- **Type**: RandomForestClassifier
- **Features**: 10 (8 subjects + Attendance + Assignments)
- **Target**: Performance category (Strong / Needs Improvement / At-Risk)
- **Prediction Method**: Multi-class classification with probability scores
- **Label Mapping**: Model outputs are normalized to required labels
  - "Excellent" → "Strong"
  - "Average" → "Needs Improvement"
  - "At Risk" → "At Risk"
- **Ranking**: Combines prediction probability (70%) and normalized marks (30%)

## Recent Changes
- **2025-11-09**: Complete system setup with three dashboards
  - Removed RGPV 5th semester specific scheme
  - Implemented generic 8-subject academic structure
  - Updated to use Subject1-Subject8 naming (100 marks each)
  - Added centralized label normalization
  - Enhanced Student Dashboard with personalized predictions
  - Enhanced Teacher Dashboard with analytics and visualizations
  - Created Admin Dashboard for system oversight
  - Added PDF/Excel export functionality
  - Integrated matplotlib/seaborn charts
  - Set up deployment configuration with Gunicorn

## User Preferences
- Clean, professional UI with customizable branding
- Role-based dashboards for different user types
- Comprehensive analytics with visual representations
- Easy-to-use file upload for batch processing
- Downloadable reports for offline analysis
- Generic subject naming for flexibility across institutions

## Project Architecture
- **Pattern**: MVC with Flask
- **Frontend**: Server-side rendered templates with responsive CSS
- **Backend**: Flask REST endpoints
- **Storage**: File-based (uploads, reports)
- **ML**: Pre-trained model loaded at startup with label normalization

## Deployment
- **Target**: Replit Autoscale deployment
- **Server**: Gunicorn with 2 workers
- **Port**: 5000
- **Environment**: Production-ready with proper WSGI server

## Customization Guide
To adapt this system for your institution:

1. **Update Branding**:
   - Replace `static/logo.png` with your institution's logo
   - Modify header titles in templates

2. **Customize Subject Names**:
   - Edit the `SUBJECT_NAMES` dictionary in `app.py`
   - Example: `"Subject1": "Mathematics"`, `"Subject2": "Physics"`, etc.

3. **Adjust Max Marks** (optional):
   - Modify the `MAX_MARKS` dictionary in `app.py`
   - Retrain the model with your data using `python model.py`

4. **Update Training Data**:
   - Add your historical student data to `student_data.csv`
   - Ensure columns match: Subject1-Subject8, Attendance, Assignments, Performance
   - Run `python model.py` to retrain the model

## Future Enhancements (if requested)
- Database integration for persistent storage
- User authentication and role management
- Historical trend analysis over multiple semesters
- Email notifications for risk alerts
- Mobile-responsive improvements
- Advanced visualization dashboards
- Comparative analysis across batches
- Custom subject configuration UI
