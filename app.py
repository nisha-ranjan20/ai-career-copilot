from flask import Flask, render_template, request,session,redirect
from db import engine, Base, SessionLocal
from pypdf import PdfReader
import google.generativeai as genai
from models import User,Report
import markdown
from flask import send_file
from reportlab.pdfgen import canvas
from flask import send_file, session
from reportlab.pdfgen import canvas


app = Flask(__name__)


app.secret_key = "nisha_secret_key"
import os

genai.configure(
    api_key=os.getenv("GEMINI_API_KEY")
)

print("API KEY LOADED")
model = genai.GenerativeModel("gemini-2.5-flash")
# Create tables
Base.metadata.create_all(bind=engine)

@app.route("/test-ai")
def test_ai():

    response = model.generate_content("Say Hello")

    return response.text
@app.route("/")
def home():
    return redirect("/login")

@app.route("/interview")
def interview():
    return render_template("interview.html")

# REGISTER
@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":
        print("REGISTER HIT")

        email = request.form["email"]
        password = request.form["password"]

        db = SessionLocal()

        # Check if email already exists
        existing_user = db.query(User).filter(
            User.email == email
        ).first()

        if existing_user:
            db.close()
            return "Email already exists"

        # Create new user
        user = User(
            email=email,
            password=password
        )

        db.add(user)
        db.commit()
        db.close()

        return redirect("/login")

    return render_template("register.html")
@app.route("/generate-interview", methods=["POST"])
def generate_interview():

    role = request.form["role"]

    prompt = f"""
Generate 15 interview questions for {role}.

Divide into:
1. Basic Questions
2. Technical Questions
3. HR Questions

Use proper markdown.
"""

    try:
        response = model.generate_content(prompt)
        questions = response.text

    except Exception as e:
       questions = f"""
Gemini Error:

{str(e)}
"""

    import markdown

    questions_html = markdown.markdown(questions)

    return render_template(
        "interview_result.html",
        questions=questions_html
    )
# LOGIN
@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        db = SessionLocal()

        user = db.query(User).filter(
            User.email == email,
            User.password == password
        ).first()

        db.close()

        if user:

            session["email"] = user.email

            return redirect("/dashboard")

        else:
            return "Invalid Email or Password"

    return render_template("login.html")

@app.route("/dashboard")
def dashboard():

    if "email" not in session:
        return redirect("/login")

    db = SessionLocal()

    count = db.query(Report).filter(
        Report.email == session["email"]
    ).count()

    recent_reports = db.query(Report).filter(
        Report.email == session["email"]
    ).all()

    db.close()

    return render_template(
        "dashboard.html",
        email=session["email"],
        
        count=count,
        reports=recent_reports
    )
    
@app.route("/upload", methods=["POST"])
def upload():

    global latest_report

    file = request.files["resume"]

    from pypdf import PdfReader

    pdf = PdfReader(file)

    text = ""

    for page in pdf.pages:
        text += page.extract_text()

    prompt = f"""
Analyze this resume and give output in proper markdown format.

Use these sections:

# Resume Score
# Strengths
#@ Areas for Improvement
# Skills Found
# Missing Skills
# Recommended Career
# Learning Roadmap

Resume:
{text}
"""


    
    try:
        response = model.generate_content(prompt)
        ai_result = response.text

    except Exception as e:
        ai_result = f"""
Gemini Error:

{str(e)}
"""

    

    latest_report = ai_result

    import markdown

    ai_html = markdown.markdown(
        ai_result,
        extensions=["fenced_code", "tables"]
    )

    return render_template(
        "result.html",
        ai_result=ai_html
    )
@app.route("/reports")
def reports():

    db = SessionLocal()

    all_reports = db.query(Report).all()

    return render_template(
        "reports.html",
        reports=all_reports
    )
@app.route("/download-report")
def download_report():

    global latest_report

    report = latest_report

    if not report:
        report = "No report available"

    from flask import send_file
    from reportlab.pdfgen import canvas
    import io

    buffer = io.BytesIO()

    pdf = canvas.Canvas(buffer)

    pdf.setTitle("AI Resume Analysis Report")

    y = 800

    pdf.setFont("Helvetica-Bold", 18)
    pdf.drawString(50, y, "AI Resume Analysis Report")

    y -= 40

    pdf.setFont("Helvetica", 12)

    for line in report.split("\n"):

        if y < 50:
            pdf.showPage()
            y = 800
            pdf.setFont("Helvetica", 12)

        pdf.drawString(50, y, line[:100])

        y -= 18

    pdf.save()

    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name="AI_Resume_Report.pdf",
        mimetype="application/pdf"
    )



@app.route("/chat", methods=["POST"])
def chat():

    question = request.form["question"]

    model = genai.GenerativeModel(
        "models/gemini-2.5-flash"
    )

    response = model.generate_content(question)

    return render_template(
        "chat.html",
        question=question,
        answer=response.text
    )
@app.route("/logout")
def logout():

    session.clear()

    return redirect("/login")
if __name__ == "__main__":
    app.run(debug=True)