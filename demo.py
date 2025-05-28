"""
Student Analytics Application - Al-Qalam Imrou Foundation
Enhanced UI and Guidance Logic Version

This application displays student results, provides analysis, and offers personalized guidance
based on performance in the Artificial Intelligence subject.

Author: Mr. Oussama SEBROU
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from fuzzywuzzy import process, fuzz
import smtplib
from email.mime.text import MIMEText
import os
from datetime import datetime
import hashlib  # For basic password hashing
import io  # Needed for StringIO

# --- Page Config (MUST be the first Streamlit command) ---
st.set_page_config(
    page_title="Student Analytics - Al-Qalam Imrou Foundation", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

# --- Configuration ---
APP_TITLE_EN = "Student Analytics - Al-Qalam Imrou Foundation"
APP_SUBTITLE_AR = "نتائج تلاميذ مؤسسة القلم إمرو - مادة الذكاء الاصطناعي"
ADMIN_USERNAME = "admin"  # Simple admin username
# VERY IMPORTANT: Replace with a securely hashed password in a real scenario
# For demonstration, using a simple hash. Generate a hash for a chosen password.
# Example: echo -n "your_password" | sha256sum
ADMIN_PASSWORD_HASH = "8c6976e5b5410415bde908bd4dee15dfb167a9c873fc4bb8a81f6f2ab448a918"  # Example hash for 'admin'
CONTACT_EMAIL = "oussama.sebrou@gmail.com"
VISITOR_LOG_FILE = "visitor_log.txt"  # Log file in the same directory as the app
# Email sending configuration (User must configure these in deployment environment)
EMAIL_HOST = os.environ.get("EMAIL_HOST", "smtp.gmail.com")  # Default to Gmail SMTP
EMAIL_PORT = int(os.environ.get("EMAIL_PORT", 587))  # Default to Gmail TLS port
EMAIL_SENDER_USER = os.environ.get("EMAIL_SENDER_USER", "")  # Must be set in environment
EMAIL_SENDER_PASSWORD = os.environ.get("EMAIL_SENDER_PASSWORD", "")  # Must be set in environment
EXCEL_FILE = "student_data.xlsx"  # Excel file with student data

# --- Custom CSS for better UI ---
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
        text-align: center;
    }
    .sub-header {
        font-size: 1.8rem;
        font-weight: 600;
        margin-bottom: 1.5rem;
        text-align: center;
    }
    .section-header {
        font-size: 1.5rem;
        font-weight: 600;
        margin-top: 1rem;
        margin-bottom: 0.5rem;
        padding-bottom: 0.5rem;
        border-bottom: 1px solid #f0f0f0;
    }
    .info-box {
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        background-color: #f8f9fa;
        border-left: 4px solid #4361ee;
    }
    .warning-box {
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        background-color: #fff3cd;
        border-left: 4px solid #ffc107;
    }
    .error-box {
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        background-color: #f8d7da;
        border-left: 4px solid #dc3545;
    }
    .success-box {
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        background-color: #d1e7dd;
        border-left: 4px solid #198754;
    }
    .metric-card {
        background-color: white;
        border-radius: 0.5rem;
        padding: 1rem;
        box-shadow: 0 0.125rem 0.25rem rgba(0, 0, 0, 0.075);
        margin-bottom: 1rem;
    }
    .metric-value {
        font-size: 2rem;
        font-weight: 700;
        text-align: center;
    }
    .metric-label {
        font-size: 1rem;
        text-align: center;
        color: #6c757d;
    }
    .guidance-section {
        background-color: #f8f9fa;
        border-radius: 0.5rem;
        padding: 1.5rem;
        margin-top: 1.5rem;
        border-left: 4px solid #20c997;
    }
    .footer {
        text-align: center;
        margin-top: 2rem;
        padding-top: 1rem;
        border-top: 1px solid #f0f0f0;
        color: #6c757d;
    }
    /* Make sidebar more professional */
    .css-1d391kg, .css-1lcbmhc {
        background-color: #f8f9fa;
    }
    /* Improve form fields */
    .stTextInput > div > div > input, 
    .stTextArea > div > div > textarea {
        border-radius: 0.25rem;
    }
    /* Improve buttons */
    .stButton > button {
        border-radius: 0.25rem;
        font-weight: 500;
    }
</style>
""", unsafe_allow_html=True)

# --- Helper Functions ---

def load_student_data():
    """
    Load student data from Excel file with all sheets.
    Each sheet represents a class section.
    """
    try:
        # Read Excel file with all sheets
        xls = pd.ExcelFile(EXCEL_FILE)
        
        # Dictionary to store dataframes for each section
        sections_data = {}
        
        # Process each sheet
        for sheet_name in xls.sheet_names:
            try:
                # Read the sheet into a dataframe
                df = pd.read_excel(EXCEL_FILE, sheet_name=sheet_name)
                
                # Check if dataframe is not empty and has expected columns
                if not df.empty and set(df.columns).intersection({'اسم التلميذ', 'اسم التلميذة', 'التقويم', 'الفرض', 'الإختبار', 'المعدل'}):
                    # Store in dictionary with sheet name as key
                    sections_data[sheet_name] = df
            except Exception as e:
                print(f"Error loading sheet {sheet_name}: {e}")
                continue
        
        return sections_data
    except Exception as e:
        print(f"Error loading Excel file: {e}")
        return {}

def find_student(section_data, student_name, threshold=70):
    """
    Find a student in the section data using fuzzy matching.
    Returns the student data if found, None otherwise.
    """
    if section_data is None or section_data.empty:
        return None
    
    # Determine which column has student names
    name_col = 'اسم التلميذ' if 'اسم التلميذ' in section_data.columns else 'اسم التلميذة'
    
    # Get all student names
    student_names = section_data[name_col].tolist()
    
    # Find the best match
    best_match, score = process.extractOne(student_name, student_names, scorer=fuzz.token_sort_ratio)
    
    if score >= threshold:
        # Return the student data as a dictionary
        student_data = section_data[section_data[name_col] == best_match].iloc[0].to_dict()
        return student_data
    
    return None

def generate_performance_charts(student_data):
    """
    Generate performance charts for the student.
    Returns a tuple of (comparison_chart, radar_chart, progress_chart)
    """
    # Extract scores
    evaluation = student_data.get('التقويم', 0)
    assignment = student_data.get('الفرض', 0)
    exam = student_data.get('الإختبار', 0)
    average = student_data.get('المعدل', 0)
    
    # Comparison bar chart
    fig_comparison = go.Figure()
    
    # Add bars for each assessment type
    fig_comparison.add_trace(go.Bar(
        x=['التقويم', 'الفرض', 'الإختبار', 'المعدل'],
        y=[evaluation, assignment, exam, average],
        text=[f"{evaluation:.2f}", f"{assignment:.2f}", f"{exam:.2f}", f"{average:.2f}"],
        textposition='auto',
        marker_color=['rgba(64, 144, 205, 0.8)', 'rgba(72, 181, 163, 0.8)', 
                     'rgba(244, 120, 96, 0.8)', 'rgba(237, 189, 78, 0.8)'],
        hoverinfo='y+text',
        name='النقاط'
    ))
    
    # Update layout
    fig_comparison.update_layout(
        title={
            'text': 'مقارنة النقاط في مختلف التقييمات',
            'y':0.9,
            'x':0.5,
            'xanchor': 'center',
            'yanchor': 'top'
        },
        xaxis_title="نوع التقييم",
        yaxis_title="النقاط (من 20)",
        yaxis=dict(range=[0, 20]),
        template='plotly_white',
        height=400,
    )
    
    # Radar chart for strengths and weaknesses
    fig_radar = go.Figure()
    
    fig_radar.add_trace(go.Scatterpolar(
        r=[evaluation, assignment, exam],
        theta=['التقويم', 'الفرض', 'الإختبار'],
        fill='toself',
        name='النقاط',
        line_color='rgb(67, 147, 195)',
        fillcolor='rgba(67, 147, 195, 0.2)'
    ))
    
    fig_radar.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 20]
            )
        ),
        title={
            'text': 'تحليل نقاط القوة والضعف',
            'y':0.95,
            'x':0.5,
            'xanchor': 'center',
            'yanchor': 'top'
        },
        showlegend=False,
        height=400,
    )
    
    # Progress chart (comparing assignment vs exam)
    fig_progress = go.Figure()
    
    # Calculate progress percentage
    progress = ((exam - assignment) / assignment * 100) if assignment > 0 else 0
    progress_color = 'green' if progress >= 0 else 'red'
    
    # Add line chart
    fig_progress.add_trace(go.Scatter(
        x=['الفرض', 'الإختبار'],
        y=[assignment, exam],
        mode='lines+markers+text',
        text=[f"{assignment:.2f}", f"{exam:.2f}"],
        textposition='top center',
        line=dict(color=progress_color, width=3),
        marker=dict(size=12),
        name='التطور'
    ))
    
    # Add annotation for progress percentage
    fig_progress.add_annotation(
        x=1.5,
        y=max(assignment, exam) + 1,
        text=f"نسبة التطور: {progress:.1f}%" if progress != 0 else "لا يوجد تغيير",
        showarrow=True,
        arrowhead=1,
        arrowcolor=progress_color,
        arrowsize=1,
        arrowwidth=2,
        font=dict(color=progress_color, size=14)
    )
    
    # Update layout
    fig_progress.update_layout(
        title={
            'text': 'تطور الأداء بين الفرض والإختبار',
            'y':0.9,
            'x':0.5,
            'xanchor': 'center',
            'yanchor': 'top'
        },
        xaxis_title="نوع التقييم",
        yaxis_title="النقاط (من 20)",
        yaxis=dict(range=[0, 20]),
        template='plotly_white',
        height=400,
    )
    
    # Pie chart for grade distribution
    fig_pie = px.pie(
        values=[evaluation, assignment, exam],
        names=['التقويم', 'الفرض', 'الإختبار'],
        title='توزيع النقاط حسب نوع التقييم',
        color_discrete_sequence=px.colors.sequential.Plasma_r,
        hole=0.4,
    )
    
    fig_pie.update_layout(
        height=400,
    )
    
    return fig_comparison, fig_radar, fig_progress, fig_pie

def generate_guidance(student_data):
    """
    Generate personalized guidance based on student performance.
    Returns a tuple of (strengths, weaknesses, recommendations, ethical_guidance)
    """
    # Extract scores
    name_col = 'اسم التلميذ' if 'اسم التلميذ' in student_data else 'اسم التلميذة'
    student_name = student_data.get(name_col, "")
    evaluation = student_data.get('التقويم', 0)
    assignment = student_data.get('الفرض', 0)
    exam = student_data.get('الإختبار', 0)
    average = student_data.get('المعدل', 0)
    
    # Calculate progress
    progress = ((exam - assignment) / assignment * 100) if assignment > 0 else 0
    
    # Determine performance level
    if average >= 18:
        performance_level = "ممتاز"
    elif average >= 16:
        performance_level = "جيد جداً"
    elif average >= 14:
        performance_level = "جيد"
    elif average >= 12:
        performance_level = "متوسط"
    elif average >= 10:
        performance_level = "مقبول"
    else:
        performance_level = "ضعيف"
    
    # Identify strengths
    strengths = []
    if evaluation >= 16:
        strengths.append("أداء ممتاز في التقويم المستمر")
    if assignment >= 16:
        strengths.append("أداء ممتاز في الفرض")
    if exam >= 16:
        strengths.append("أداء ممتاز في الاختبار")
    if progress > 10:
        strengths.append("تطور ملحوظ بين الفرض والاختبار")
    
    # If no specific strengths were identified
    if not strengths:
        if average >= 14:
            strengths.append("مستوى عام جيد في المادة")
        elif average >= 10:
            strengths.append("اجتياز المادة بنجاح")
    
    # Identify weaknesses
    weaknesses = []
    if evaluation < 10:
        weaknesses.append("ضعف في التقويم المستمر")
    if assignment < 10:
        weaknesses.append("ضعف في الفرض")
    if exam < 10:
        weaknesses.append("ضعف في الاختبار")
    if progress < -10:
        weaknesses.append("تراجع في المستوى بين الفرض والاختبار")
    
    # If no specific weaknesses were identified
    if not weaknesses and average < 10:
        weaknesses.append("مستوى عام ضعيف في المادة")
    
    # Generate recommendations
    recommendations = []
    
    # Recommendations based on evaluation score
    if evaluation < 12:
        recommendations.append("زيادة المشاركة في الأنشطة الصفية والتفاعل مع المعلم")
        recommendations.append("الالتزام بحضور جميع الحصص وتقديم الواجبات في موعدها")
    
    # Recommendations based on assignment score
    if assignment < 12:
        recommendations.append("تخصيص وقت أكبر للمراجعة قبل الفروض")
        recommendations.append("حل تمارين إضافية لتعزيز فهم المفاهيم الأساسية")
    
    # Recommendations based on exam score
    if exam < 12:
        recommendations.append("تطوير استراتيجية أفضل للمذاكرة قبل الاختبارات")
        recommendations.append("التركيز على فهم المفاهيم بدلاً من الحفظ")
    
    # Recommendations based on progress
    if progress < 0:
        recommendations.append("مراجعة أسباب التراجع في المستوى بين الفرض والاختبار")
        recommendations.append("طلب المساعدة من المعلم لتحديد نقاط الضعف وكيفية معالجتها")
    
    # General recommendations based on overall performance
    if average < 10:
        recommendations.append("حضور حصص تقوية إضافية")
        recommendations.append("تكوين مجموعة دراسة مع زملاء متفوقين")
    elif average < 14:
        recommendations.append("الاستمرار في العمل الجاد مع التركيز على تحسين نقاط الضعف")
    else:
        recommendations.append("الحفاظ على المستوى الجيد والسعي للتميز")
    
    # If no specific recommendations were generated
    if not recommendations:
        recommendations.append("الاستمرار في النهج الحالي مع السعي للتطوير المستمر")
    
    # Generate ethical guidance
    ethical_guidance = []
    
    # Personalized ethical guidance based on performance
    if performance_level in ["ممتاز", "جيد جداً"]:
        ethical_guidance.append("مساعدة الزملاء الذين يواجهون صعوبات في المادة")
        ethical_guidance.append("المشاركة في الأنشطة التطوعية لنشر المعرفة في مجال الذكاء الاصطناعي")
        ethical_guidance.append("الالتزام بأخلاقيات استخدام التكنولوجيا والذكاء الاصطناعي")
    elif performance_level in ["جيد", "متوسط"]:
        ethical_guidance.append("تبني روح المثابرة والتعلم المستمر")
        ethical_guidance.append("التعاون مع الزملاء في مجموعات دراسية لتبادل المعرفة")
        ethical_guidance.append("الاهتمام بالجوانب الأخلاقية للذكاء الاصطناعي وتطبيقاته")
    else:
        ethical_guidance.append("عدم الاستسلام للصعوبات والإيمان بالقدرة على التحسن")
        ethical_guidance.append("طلب المساعدة من المعلمين والزملاء دون تردد")
        ethical_guidance.append("التركيز على فهم المفاهيم الأساسية قبل الانتقال للمتقدمة")
    
    # Add general ethical guidance for all students
    ethical_guidance.append("الالتزام بالأمانة العلمية وتجنب الغش في الاختبارات")
    ethical_guidance.append("تطوير مهارات التفكير النقدي والإبداعي في استخدام التكنولوجيا")
    
    # Create personalized message
    personal_message = f"عزيزي الطالب {student_name}، أداؤك العام في مادة الذكاء الاصطناعي {performance_level}."
    
    if progress > 0:
        personal_message += f" لقد أظهرت تطوراً إيجابياً بنسبة {progress:.1f}% بين الفرض والاختبار، وهذا يدل على جهدك واهتمامك."
    elif progress < 0:
        personal_message += f" لوحظ تراجع بنسبة {abs(progress):.1f}% بين الفرض والاختبار، مما يستدعي مراجعة أسلوب الدراسة."
    else:
        personal_message += " لقد حافظت على مستوى ثابت بين الفرض والاختبار."
    
    return personal_message, strengths, weaknesses, recommendations, ethical_guidance

def log_visitor(action):
    """Log visitor actions to a file"""
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(VISITOR_LOG_FILE, "a", encoding='utf-8') as f:
            f.write(f"{timestamp} | {action}\n")
    except Exception as e:
        print(f"Error logging visitor: {e}")

def send_email(name, email, subject, message):
    """Send email using SMTP"""
    if not EMAIL_SENDER_USER or not EMAIL_SENDER_PASSWORD:
        return False, "لم يتم تكوين بيانات اعتماد البريد الإلكتروني للمرسل (EMAIL_SENDER_USER, EMAIL_SENDER_PASSWORD). يرجى تكوينها كمتغيرات بيئة في بيئة النشر."
    
    try:
        msg = MIMEText(f"من: {name}\nالبريد الإلكتروني: {email}\n\n{message}")
        msg['Subject'] = f"رسالة من تطبيق نتائج التلاميذ: {subject}"
        msg['From'] = EMAIL_SENDER_USER
        msg['To'] = CONTACT_EMAIL
        
        server = smtplib.SMTP(EMAIL_HOST, EMAIL_PORT)
        server.starttls()
        server.login(EMAIL_SENDER_USER, EMAIL_SENDER_PASSWORD)
        server.send_message(msg)
        server.quit()
        return True, "تم إرسال الرسالة بنجاح!"
    except Exception as e:
        return False, f"خطأ في إرسال البريد الإلكتروني: {str(e)}"

# --- Main Application ---
def main():
    # Load student data
    sections_data = load_student_data()
    
    # Initialize session state for student search
    if 'selected_section' not in st.session_state:
        st.session_state['selected_section'] = None
    if 'student_data' not in st.session_state:
        st.session_state['student_data'] = None
    if 'search_error' not in st.session_state:
        st.session_state['search_error'] = None
    if 'admin_logged_in' not in st.session_state:
        st.session_state['admin_logged_in'] = False
    
    # --- Header ---
    st.markdown(f'<h1 class="main-header">{APP_TITLE_EN}</h1>', unsafe_allow_html=True)
    st.markdown(f'<h2 class="sub-header">{APP_SUBTITLE_AR}</h2>', unsafe_allow_html=True)
    
    # Introduction text
    st.markdown("""
    <div class="info-box">
        <p>مرحباً بكم في نظام تحليل نتائج الطلاب الخاص بمؤسسة القلم إمرو. يوفر هذا النظام تحليلاً شاملاً لأداء الطلاب في مادة الذكاء الاصطناعي، 
        مع تقديم رسومات بيانية توضيحية وتوجيهات مخصصة لكل طالب بناءً على نتائجه.</p>
        <p>يرجى اختيار القسم من القائمة الجانبية، ثم إدخال اسم التلميذ للاطلاع على النتائج والتحليل.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # --- Sidebar ---
    st.sidebar.markdown("## اختيار القسم والتلميذ")
    
    # Section selection
    selected_section_name = st.sidebar.selectbox(
        "اختر القسم:",
        options=list(sections_data.keys()),
        format_func=lambda x: x,
        key="section_select"
    )
    
    if selected_section_name:
        st.session_state['selected_section'] = selected_section_name
        section_data = sections_data[selected_section_name]
        
        # Student name input
        student_name = st.sidebar.text_input(
            "أدخل اسم ولقب التلميذ:",
            placeholder="مثال: الحاج موسى عبد الغني"
        )
        
        # Search button
        if st.sidebar.button("بحث عن النتائج"):
            log_visitor(f"Search for student: {student_name} in section {selected_section_name}")
            
            if student_name:
                # Find student using fuzzy matching
                student_data = find_student(section_data, student_name)
                
                if student_data:
                    st.session_state['student_data'] = student_data
                    if 'search_error' in st.session_state: 
                        del st.session_state['search_error']
                else:
                    st.session_state['search_error'] = f"لم يتم العثور على تلميذ باسم '{student_name}' في القسم المحدد. يرجى التأكد من الاسم والقسم."
                    st.session_state['student_data'] = None
            else:
                st.session_state['search_error'] = "يرجى إدخال اسم التلميذ للبحث."
                st.session_state['student_data'] = None
    
    # --- Exam Paper Section ---
    st.sidebar.markdown("---")
    show_exam = st.sidebar.checkbox("عرض نموذج الاختبار وتصحيحه", key="show_exam_cb")
    
    # --- Contact Section ---
    st.sidebar.markdown("---")
    st.sidebar.markdown("## تواصل معنا")
    
    contact_name = st.sidebar.text_input("الاسم:", key="contact_name")
    contact_email = st.sidebar.text_input("البريد الإلكتروني:", key="contact_email")
    contact_subject = st.sidebar.text_input("الموضوع:", key="contact_subject")
    contact_message = st.sidebar.text_area("الرسالة:", key="contact_message", 
                                          placeholder="إذا كان هناك خلل في التطبيق أو لديك اقتراحات لتحسينه، يرجى إخبارنا هنا وسنعمل على حل المشكلة في أقرب وقت.")
    
    if st.sidebar.button("إرسال الرسالة"):
        log_visitor("Contact form submission")
        if contact_name and contact_email and contact_subject and contact_message:
            success, message = send_email(contact_name, contact_email, contact_subject, contact_message)
            if success:
                st.sidebar.success(message)
            else:
                st.sidebar.error(message)
                if "EMAIL_SENDER_USER" not in message:
                    st.sidebar.markdown("""
                    <div class="error-box">
                        خطأ: لم يتم تكوين بيانات اعتماد البريد الإلكتروني للمرسل
                        (EMAIL_SENDER_USER, EMAIL_SENDER_PASSWORD).
                        يرجى تكوينها كمتغيرات بيئة في بيئة النشر.
                    </div>
                    """, unsafe_allow_html=True)
                    
                    if not st.session_state['admin_logged_in']:
                        st.sidebar.markdown("""
                        <div class="warning-box">
                            تنبيه للمشرف: تأكد من تكوين متغيرات البيئة
                            EMAIL_SENDER_USER و
                            EMAIL_SENDER_PASSWORD
                            في بيئة النشر.
                        </div>
                        """, unsafe_allow_html=True)
        else:
            st.sidebar.error("يرجى ملء جميع الحقول المطلوبة.")
    
    # --- Admin Section ---
    st.sidebar.markdown("---")
    st.sidebar.markdown("## قسم المشرف")
    
    if not st.session_state['admin_logged_in']:
        admin_username = st.sidebar.text_input("اسم المستخدم:", key="admin_username")
        admin_password = st.sidebar.text_input("كلمة المرور:", type="password", key="admin_password")
        
        if st.sidebar.button("تسجيل الدخول"):
            log_visitor("Admin login attempt")
            if admin_username == ADMIN_USERNAME:
                # Hash the entered password and compare with stored hash
                entered_password_hash = hashlib.sha256(admin_password.encode()).hexdigest()
                if entered_password_hash == ADMIN_PASSWORD_HASH:
                    st.session_state['admin_logged_in'] = True
                    st.sidebar.success("تم تسجيل الدخول بنجاح!")
                else:
                    st.sidebar.error("كلمة المرور غير صحيحة.")
            else:
                st.sidebar.error("اسم المستخدم غير صحيح.")
    else:
        st.sidebar.success("أنت مسجل الدخول كمشرف.")
        st.sidebar.subheader("لوحة تحكم المشرف")
        
        # Display Visitor Log
        if st.sidebar.button("عرض سجل الزوار"):
            log_visitor("Admin View Logs")
            st.markdown("---")
            st.markdown('<h2 class="section-header">سجل زوار التطبيق</h2>', unsafe_allow_html=True)
            try:
                # Provide download button for large logs
                if os.path.exists(VISITOR_LOG_FILE):
                     with open(VISITOR_LOG_FILE, "r", encoding='utf-8') as f:
                        log_content = f.read()
                     st.download_button(
                         label="تحميل سجل الزوار الكامل",
                         data=log_content,
                         file_name="visitor_log.txt",
                         mime="text/plain"
                     )
                     # Display last N lines in text area
                     lines = log_content.strip().split('\n')
                     st.text_area("آخر 50 زيارة:", "\n".join(lines[-50:]), height=300)
                else:
                    st.info("سجل الزوار فارغ حالياً.")
            except Exception as e:
                st.error(f"خطأ في قراءة سجل الزوار: {e}")
        
        if st.sidebar.button("تسجيل الخروج للمشرف"):
            log_visitor("Admin Logout")
            st.session_state['admin_logged_in'] = False
            st.rerun()  # Rerun to hide admin panel
    
    # --- Main Content Area ---
    
    # Display error message if search failed
    if 'search_error' in st.session_state and st.session_state['search_error']:
        st.markdown(f"""
        <div class="error-box">
            {st.session_state['search_error']}
        </div>
        """, unsafe_allow_html=True)
    
    # Display info message if no search has been performed
    if not st.session_state['student_data'] and not ('search_error' in st.session_state and st.session_state['search_error']):
        st.markdown("""
        <div class="info-box">
            يرجى اختيار القسم من القائمة الجانبية، ثم إدخال اسم التلميذ والضغط على زر البحث لعرض النتائج.
        </div>
        """, unsafe_allow_html=True)
    
    # Display student results if found
    if st.session_state['student_data']:
        student_data = st.session_state['student_data']
        
        # Determine which column has student names
        name_col = 'اسم التلميذ' if 'اسم التلميذ' in student_data else 'اسم التلميذة'
        student_name = student_data[name_col]
        
        # Display student information
        st.markdown(f"""
        <h2 class="section-header">نتائج الطالب: {student_name}</h2>
        <div class="info-box">
            <strong>القسم:</strong> {st.session_state['selected_section']}
        </div>
        """, unsafe_allow_html=True)
        
        # Display scores in metric cards
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{student_data['التقويم']}</div>
                <div class="metric-label">التقويم</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{student_data['الفرض']}</div>
                <div class="metric-label">الفرض</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{student_data['الإختبار']}</div>
                <div class="metric-label">الإختبار</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{student_data['المعدل']}</div>
                <div class="metric-label">المعدل</div>
            </div>
            """, unsafe_allow_html=True)
        
        # Generate and display charts
        st.markdown('<h2 class="section-header">تحليل الأداء</h2>', unsafe_allow_html=True)
        
        fig_comparison, fig_radar, fig_progress, fig_pie = generate_performance_charts(student_data)
        
        # Display charts in tabs
        tab1, tab2, tab3, tab4 = st.tabs(["مقارنة النقاط", "نقاط القوة والضعف", "تطور الأداء", "توزيع النقاط"])
        
        with tab1:
            st.plotly_chart(fig_comparison, use_container_width=True)
        
        with tab2:
            st.plotly_chart(fig_radar, use_container_width=True)
        
        with tab3:
            st.plotly_chart(fig_progress, use_container_width=True)
        
        with tab4:
            st.plotly_chart(fig_pie, use_container_width=True)
        
        # Generate and display personalized guidance
        personal_message, strengths, weaknesses, recommendations, ethical_guidance = generate_guidance(student_data)
        
        st.markdown('<h2 class="section-header">التوجيهات والملاحظات</h2>', unsafe_allow_html=True)
        
        # Personal message
        st.markdown(f"""
        <div class="guidance-section">
            <h3>رسالة شخصية</h3>
            <p>{personal_message}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Strengths and weaknesses
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            <div class="success-box">
                <h3>نقاط القوة</h3>
                <ul>
            """, unsafe_allow_html=True)
            
            for strength in strengths:
                st.markdown(f"<li>{strength}</li>", unsafe_allow_html=True)
            
            st.markdown("</ul></div>", unsafe_allow_html=True)
        
        with col2:
            st.markdown("""
            <div class="error-box">
                <h3>نقاط تحتاج إلى تحسين</h3>
                <ul>
            """, unsafe_allow_html=True)
            
            for weakness in weaknesses:
                st.markdown(f"<li>{weakness}</li>", unsafe_allow_html=True)
            
            st.markdown("</ul></div>", unsafe_allow_html=True)
        
        # Recommendations
        st.markdown("""
        <div class="info-box">
            <h3>توصيات للتحسين</h3>
            <ul>
        """, unsafe_allow_html=True)
        
        for recommendation in recommendations:
            st.markdown(f"<li>{recommendation}</li>", unsafe_allow_html=True)
        
        st.markdown("</ul></div>", unsafe_allow_html=True)
        
        # Ethical guidance
        st.markdown("""
        <div class="guidance-section">
            <h3>التوجيه الأخلاقي والتربوي</h3>
            <ul>
        """, unsafe_allow_html=True)
        
        for guidance in ethical_guidance:
            st.markdown(f"<li>{guidance}</li>", unsafe_allow_html=True)
        
        st.markdown("</ul></div>", unsafe_allow_html=True)
    
    # Display exam paper if checkbox is checked
    if show_exam:
        log_visitor("View Exam Paper")
        st.markdown("---")
        st.markdown('<h2 class="section-header">نموذج اختبار مادة الذكاء الاصطناعي وتصحيحه</h2>', unsafe_allow_html=True)
        st.write("المستوى: الثانية ثانوي رياضيات (نموذج)")  # Specify it's an example
        
        # Updated paths assuming images are in the same directory as the script
        exam_image_paths = [
            "1748355922145.jpg",  # Exam Page 1 - Relative path
            "1748355927881.jpg"   # Exam Page 2 - Relative path
        ]
        correction_image_paths = [
            "IMG-20250522-WA0002.jpg",  # Correction Page 1 - Relative path
            "IMG-20250522-WA0003.jpg"   # Correction Page 2 - Relative path
        ]
        
        st.subheader("نموذج الاختبار:")
        img_col1, img_col2 = st.columns(2)
        with img_col1:
            try:
                st.image(exam_image_paths[0], use_column_width=True)
            except Exception as e:
                 st.error(f"خطأ في تحميل الصورة {os.path.basename(exam_image_paths[0])}: {e}")
        with img_col2:
            try:
                st.image(exam_image_paths[1], use_column_width=True)
            except Exception as e:
                 st.error(f"خطأ في تحميل الصورة {os.path.basename(exam_image_paths[1])}: {e}")
        
        st.subheader("تصحيح الاختبار:")
        img_col3, img_col4 = st.columns(2)
        with img_col3:
             try:
                st.image(correction_image_paths[0], use_column_width=True)
             except Exception as e:
                 st.error(f"خطأ في تحميل الصورة {os.path.basename(correction_image_paths[0])}: {e}")
        with img_col4:
             try:
                st.image(correction_image_paths[1], use_column_width=True)
             except Exception as e:
                 st.error(f"خطأ في تحميل الصورة {os.path.basename(correction_image_paths[1])}: {e}")
    
    # --- Footer ---
    st.markdown("""
    <div class="footer">
        <p>Developed by Mr. Oussama SEBROU</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
