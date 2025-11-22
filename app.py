import os
import pandas as pd
import numpy as np
import pickle
import io
import base64
from flask import Flask, render_template, request, redirect, url_for, send_from_directory, flash, Response, send_file, make_response
from werkzeug.utils import secure_filename
from datetime import datetime
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "replace-with-a-secret-key-in-production")
UPLOAD_FOLDER = "uploads"
REPORTS_FOLDER = "reports"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(REPORTS_FOLDER, exist_ok=True)
ALLOWED_EXTENSIONS = {"csv", "xlsx"}
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["REPORTS_FOLDER"] = REPORTS_FOLDER

MODEL_PATH = "student_model.pkl"
model = pickle.load(open(MODEL_PATH, "rb"))

MAX_MARKS = {
    "Subject1": 100,
    "Subject2": 100,
    "Subject3": 100,
    "Subject4": 100,
    "Subject5": 100,
    "Subject6": 100,
    "Subject7": 100,
    "Subject8": 100,
    "Attendance": 100,
    "Assignments": 10
}

SUBJECT_NAMES = {
    "Subject1": "Subject 1",
    "Subject2": "Subject 2",
    "Subject3": "Subject 3",
    "Subject4": "Subject 4",
    "Subject5": "Subject 5",
    "Subject6": "Subject 6",
    "Subject7": "Subject 7",
    "Subject8": "Subject 8"
}

FEATURE_COLS = ["Subject1","Subject2","Subject3","Subject4","Subject5","Subject6","Subject7","Subject8","Attendance","Assignments"]
TOTAL_MAX = sum([MAX_MARKS[c] for c in ["Subject1","Subject2","Subject3","Subject4","Subject5","Subject6","Subject7","Subject8"]])

LABEL_MAPPING = {
    "Excellent": "Strong",
    "Average": "Needs Improvement",
    "At Risk": "At Risk"
}

def normalize_label(model_label):
    return LABEL_MAPPING.get(model_label, model_label)

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def generate_suggestion(row, pred_label):
    weak = []
    for subj in ["Subject1","Subject2","Subject3","Subject4","Subject5","Subject6","Subject7","Subject8"]:
        val = row.get(subj, 0)
        maxv = MAX_MARKS[subj]
        if maxv > 0 and (val / maxv) * 100 < 40:
            weak.append(f"{SUBJECT_NAMES.get(subj, subj)}")
    
    if pred_label == "Strong":
        base = "Excellent performance! Maintain consistency and help peers."
    elif pred_label == "Needs Improvement":
        base = "Good effort. Increase study hours on weak subjects and complete all assignments."
    else:
        base = "At Risk. Seek help from teachers immediately, focus on fundamentals and increase attendance."
    
    if weak:
        base += f" Focus on: {', '.join(weak)}."
    
    att_val = row.get("Attendance", 0)
    if att_val < 75:
        base += f" Improve attendance (current: {att_val}%)."
    
    return base

def calculate_class_statistics(df):
    stats = {}
    stats['total_students'] = len(df)
    stats['avg_marks'] = df['total_marks'].mean()
    stats['avg_attendance'] = df['Attendance'].mean()
    
    label_counts = df['predicted_label'].value_counts().to_dict()
    stats['strong_count'] = label_counts.get('Strong', 0)
    stats['needs_improvement'] = label_counts.get('Needs Improvement', 0)
    stats['at_risk'] = label_counts.get('At Risk', 0)
    
    stats['low_attendance'] = len(df[df['Attendance'] < 75])
    stats['incomplete_assignments'] = len(df[df['Assignments'] < MAX_MARKS['Assignments']])
    
    subject_cols = ["Subject1","Subject2","Subject3","Subject4","Subject5","Subject6","Subject7","Subject8"]
    subject_avg = {}
    for subj in subject_cols:
        pct = (df[subj].mean() / MAX_MARKS[subj]) * 100
        subject_avg[SUBJECT_NAMES.get(subj, subj)] = round(pct, 1)
    stats['subject_averages'] = subject_avg
    
    return stats

def create_visualizations(df):
    charts = {}
    
    plt.style.use('seaborn-v0_8-darkgrid')
    
    fig, ax = plt.subplots(figsize=(8, 5))
    label_counts = df['predicted_label'].value_counts()
    colors_pie = ['#28a745', '#ffc107', '#dc3545']
    ax.pie(label_counts.values, labels=label_counts.index, autopct='%1.1f%%', colors=colors_pie[:len(label_counts)])
    ax.set_title('Performance Distribution')
    
    buf = io.BytesIO()
    plt.tight_layout()
    plt.savefig(buf, format='png', dpi=100, bbox_inches='tight')
    buf.seek(0)
    charts['performance_pie'] = base64.b64encode(buf.getvalue()).decode()
    plt.close()
    
    fig, ax = plt.subplots(figsize=(10, 5))
    subject_cols = ["Subject1","Subject2","Subject3","Subject4","Subject5","Subject6","Subject7","Subject8"]
    subject_means = []
    subject_labels = []
    for subj in subject_cols:
        pct = (df[subj].mean() / MAX_MARKS[subj]) * 100
        subject_means.append(pct)
        subject_labels.append(SUBJECT_NAMES.get(subj, subj))
    
    bars = ax.barh(subject_labels, subject_means, color='steelblue')
    ax.set_xlabel('Average Percentage')
    ax.set_title('Subject-wise Class Average')
    ax.set_xlim(0, 100)
    
    for i, (bar, val) in enumerate(zip(bars, subject_means)):
        ax.text(val + 1, i, f'{val:.1f}%', va='center')
    
    buf = io.BytesIO()
    plt.tight_layout()
    plt.savefig(buf, format='png', dpi=100, bbox_inches='tight')
    buf.seek(0)
    charts['subject_bar'] = base64.b64encode(buf.getvalue()).decode()
    plt.close()
    
    return charts

def generate_pdf_report(df, stats, filename):
    pdf_path = os.path.join(app.config["REPORTS_FOLDER"], f"report_{filename}.pdf")
    doc = SimpleDocTemplate(pdf_path, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#003366'),
        spaceAfter=30,
        alignment=TA_CENTER
    )
    
    title = Paragraph("RGPV Academic Performance Report", title_style)
    elements.append(title)
    elements.append(Spacer(1, 0.3*inch))
    
    summary_data = [
        ['Metric', 'Value'],
        ['Total Students', str(stats['total_students'])],
        ['Average Marks', f"{stats['avg_marks']:.2f}"],
        ['Average Attendance', f"{stats['avg_attendance']:.1f}%"],
        ['Strong Performers', str(stats['strong_count'])],
        ['Needs Improvement', str(stats['needs_improvement'])],
        ['At Risk', str(stats['at_risk'])],
    ]
    
    summary_table = Table(summary_data, colWidths=[3*inch, 2*inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#003366')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    
    elements.append(summary_table)
    elements.append(PageBreak())
    
    top10 = df.nlargest(10, 'rank_score')[['StudentID', 'Name', 'total_marks', 'predicted_label', 'Attendance']]
    student_data = [['Student ID', 'Name', 'Total Marks', 'Performance', 'Attendance']]
    for _, row in top10.iterrows():
        student_data.append([
            str(row['StudentID']),
            str(row['Name']),
            f"{row['total_marks']:.0f}",
            str(row['predicted_label']),
            f"{row['Attendance']:.0f}%"
        ])
    
    top_table = Table(student_data, colWidths=[1*inch, 2*inch, 1.2*inch, 1.5*inch, 1.2*inch])
    top_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#28a745')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    
    elements.append(Paragraph("Top 10 Students", styles['Heading2']))
    elements.append(Spacer(1, 0.2*inch))
    elements.append(top_table)
    
    doc.build(elements)
    return pdf_path

@app.route("/")
def index():
    return render_template("index.html", max_marks=MAX_MARKS, subject_names=SUBJECT_NAMES)

@app.route("/student")
def student_dashboard():
    return render_template("student_dashboard.html", max_marks=MAX_MARKS, subject_names=SUBJECT_NAMES)

@app.route("/student/predict", methods=["POST"])
def student_predict():
    try:
        vals = []
        for f in FEATURE_COLS:
            vals.append(float(request.form.get(f, 0)))
        
        features = np.array([vals])
        pred_raw = model.predict(features)[0]
        pred = normalize_label(pred_raw)
        proba = model.predict_proba(features)[0]
        
        row = dict(zip(FEATURE_COLS, vals))
        suggestion = generate_suggestion(row, pred)
        
        subject_cols = ["Subject1","Subject2","Subject3","Subject4","Subject5","Subject6","Subject7","Subject8"]
        total_marks = sum([row[c] for c in subject_cols])
        percentage = (total_marks / TOTAL_MAX) * 100
        
        subject_performance = {}
        for subj in subject_cols:
            pct = (row[subj] / MAX_MARKS[subj]) * 100
            status = "Strong" if pct >= 70 else "Needs Improvement" if pct >= 40 else "Weak"
            subject_performance[SUBJECT_NAMES.get(subj, subj)] = {
                'marks': row[subj],
                'max': MAX_MARKS[subj],
                'percentage': round(pct, 1),
                'status': status
            }
        
        return render_template("student_dashboard.html",
                             max_marks=MAX_MARKS,
                             subject_names=SUBJECT_NAMES,
                             prediction=pred,
                             suggestion=suggestion,
                             total_marks=total_marks,
                             percentage=round(percentage, 1),
                             attendance=vals[8],
                             assignments=vals[9],
                             subject_performance=subject_performance)
    except Exception as e:
        flash(f"Error: {str(e)}")
        return redirect(url_for("student_dashboard"))

@app.route("/teacher")
def teacher_dashboard():
    return render_template("teacher_dashboard.html", max_marks=MAX_MARKS)

@app.route("/teacher/predict_batch", methods=["POST"])
def predict_batch():
    if "file" not in request.files:
        flash("No file selected")
        return redirect(url_for("teacher_dashboard"))
    
    file = request.files["file"]
    if file.filename == "":
        flash("No file selected")
        return redirect(url_for("teacher_dashboard"))
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        save_path = os.path.join(app.config["UPLOAD_FOLDER"], f"{timestamp}_{filename}")
        file.save(save_path)
        
        try:
            if filename.endswith('.csv'):
                df = pd.read_csv(save_path)
            else:
                df = pd.read_excel(save_path)
        except Exception as e:
            flash(f"Failed to read file: {str(e)}")
            return redirect(url_for("teacher_dashboard"))
        
        required_cols = set(["StudentID","Name"] + FEATURE_COLS)
        if not required_cols.issubset(set(df.columns)):
            missing = required_cols - set(df.columns)
            flash(f"Missing required columns: {', '.join(missing)}")
            return redirect(url_for("teacher_dashboard"))
        
        if len(df) > 200:
            flash("File contains more than 200 students. Please upload max 200 rows.")
            return redirect(url_for("teacher_dashboard"))
        
        for c in FEATURE_COLS:
            df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)
        
        X = df[FEATURE_COLS].values
        preds_raw = model.predict(X)
        preds = np.array([normalize_label(p) for p in preds_raw])
        proba = model.predict_proba(X)
        classes = model.classes_.tolist()
        
        idx_excellent = classes.index("Excellent") if "Excellent" in classes else None
        
        subject_cols = ["Subject1","Subject2","Subject3","Subject4","Subject5","Subject6","Subject7","Subject8"]
        df["total_marks"] = df[subject_cols].sum(axis=1)
        df["normalized_total"] = df["total_marks"] / float(TOTAL_MAX)
        
        if idx_excellent is not None:
            df["proba_excellent"] = proba[:, idx_excellent]
        else:
            df["proba_excellent"] = 0.0
        
        df["rank_score"] = df["proba_excellent"] * 0.7 + df["normalized_total"] * 0.3
        df["predicted_label"] = preds
        df["suggestion"] = df.apply(lambda r: generate_suggestion(r, r["predicted_label"]), axis=1)
        df["attendance_ok"] = df["Attendance"] >= 75
        df["assignments_full"] = df["Assignments"] >= MAX_MARKS["Assignments"]
        
        df_sorted = df.sort_values(by="rank_score", ascending=False).reset_index(drop=True)
        top_10 = df_sorted.head(10)
        bottom_10 = df_sorted.tail(10)
        at_risk_students = df[df["predicted_label"] == "At Risk"]
        
        stats = calculate_class_statistics(df)
        charts = create_visualizations(df)
        
        result_filename = f"results_{timestamp}_{filename}"
        result_path = os.path.join(app.config["UPLOAD_FOLDER"], result_filename)
        df.to_csv(result_path, index=False)
        
        excel_filename = f"results_{timestamp}.xlsx"
        excel_path = os.path.join(app.config["REPORTS_FOLDER"], excel_filename)
        with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
            df[['StudentID', 'Name', 'total_marks', 'predicted_label', 'Attendance', 'Assignments', 'suggestion']].to_excel(
                writer, sheet_name='All Students', index=False)
            top_10.to_excel(writer, sheet_name='Top 10', index=False)
            at_risk_students.to_excel(writer, sheet_name='At Risk', index=False)
        
        top10_records = top_10.to_dict(orient="records")
        bottom10_records = bottom_10.to_dict(orient="records")
        at_risk_records = at_risk_students.to_dict(orient="records")
        
        return render_template("teacher_dashboard.html",
                             max_marks=MAX_MARKS,
                             top10=top10_records,
                             bottom10=bottom10_records,
                             at_risk=at_risk_records,
                             stats=stats,
                             charts=charts,
                             result_file=result_filename,
                             excel_file=excel_filename,
                             total_count=len(df))
    else:
        flash("Only CSV and Excel files allowed.")
        return redirect(url_for("teacher_dashboard"))

@app.route("/admin")
def admin_dashboard():
    uploads = []
    if os.path.exists(app.config["UPLOAD_FOLDER"]):
        files = [f for f in os.listdir(app.config["UPLOAD_FOLDER"]) if f.startswith("results_")]
        for f in sorted(files, reverse=True)[:10]:
            uploads.append({
                'filename': f,
                'timestamp': f.split('_')[1] if len(f.split('_')) > 1 else 'Unknown'
            })
    
    return render_template("admin_dashboard.html", uploads=uploads)

@app.route("/download/<filename>")
def download_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename, as_attachment=True)

@app.route("/download_report/<filename>")
def download_report(filename):
    return send_from_directory(app.config["REPORTS_FOLDER"], filename, as_attachment=True)

@app.route("/generate_pdf/<csv_filename>")
def generate_pdf(csv_filename):
    try:
        csv_path = os.path.join(app.config["UPLOAD_FOLDER"], csv_filename)
        df = pd.read_csv(csv_path)
        stats = calculate_class_statistics(df)
        
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        pdf_path = generate_pdf_report(df, stats, timestamp)
        
        return send_file(pdf_path, as_attachment=True, download_name=f"performance_report_{timestamp}.pdf")
    except Exception as e:
        flash(f"Error generating PDF: {str(e)}")
        return redirect(url_for("teacher_dashboard"))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
