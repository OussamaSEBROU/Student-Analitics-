# demo_excel_final.py - Final Version with Excel Data Loading and Correct Image Paths

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from fuzzywuzzy import process, fuzz
import smtplib
from email.mime.text import MIMEText
import os
from datetime import datetime
import hashlib # For basic password hashing
import io # Needed for StringIO

# --- Page Config (MUST be the first Streamlit command) ---
st.set_page_config(page_title="نتائج تلاميذ مؤسسة القلم إمرو", layout="wide", initial_sidebar_state="expanded")

# --- Configuration ---
APP_TITLE = "نتائج تلاميذ مؤسسة القلم إمرو - مادة الذكاء الاصطناعي"
ADMIN_USERNAME = "admin" # Simple admin username
# VERY IMPORTANT: Replace with a securely hashed password in a real scenario
# For demonstration, using a simple hash. Generate a hash for a chosen password.
# Example: echo -n "your_password" | sha256sum
ADMIN_PASSWORD_HASH = "8c6976e5b5410415bde908bd4dee15dfb167a9c873fc4bb8a81f6f2ab448a918" # Example hash for 'password'
CONTACT_EMAIL = "oussama.sebrou@gmail.com"
VISITOR_LOG_FILE = "visitor_log.txt" # Log file in the same directory as the app
STUDENT_DATA_FILE = "student_data.xlsx" # Excel file name

# Email sending configuration (User must configure these in deployment environment)
EMAIL_HOST = os.environ.get("EMAIL_HOST", "smtp.gmail.com") # Default to Gmail SMTP
EMAIL_PORT = int(os.environ.get("EMAIL_PORT", 587)) # Default to Gmail TLS port
EMAIL_SENDER_USER = os.environ.get("EMAIL_SENDER_USER") # Sender email address (needs to be set as environment variable)
EMAIL_SENDER_PASSWORD = os.environ.get("EMAIL_SENDER_PASSWORD") # Sender email password (needs to be set as environment variable)

# --- Data Loading Function (Reads from Excel) ---
@st.cache_data # Cache the data loading
def load_student_data_from_excel(file_path):
    """Loads student data dynamically from all sheets in an Excel file."""
    try:
        # Read all sheets into a dictionary of DataFrames
        # sheet_name=None reads all sheets
        all_sheets_data = pd.read_excel(file_path, sheet_name=None)
    except FileNotFoundError:
        st.error(f"خطأ: لم يتم العثور على ملف البيانات '{file_path}'. تأكد من وجود الملف في نفس مجلد التطبيق.")
        return None
    except Exception as e:
        st.error(f"خطأ غير متوقع أثناء قراءة ملف Excel '{file_path}': {e}")
        return None

    processed_data = {}
    expected_cols = ["اسم التلميذ", "التقويم", "الفرض", "الإختبار", "المعدل"]
    expected_cols_alt = ["اسم التلميذة", "التقويم", "الفرض", "الإختبار", "المعدل"] # For girls' class

    for sheet_name, df in all_sheets_data.items():
        # Check for expected columns (handling 'اسم التلميذة')
        if list(df.columns) == expected_cols or list(df.columns) == expected_cols_alt:
            # Rename 'اسم التلميذة' to 'اسم التلميذ' for consistency
            if "اسم التلميذة" in df.columns:
                df = df.rename(columns={"اسم التلميذة": "اسم التلميذ"})

            # Use consistent internal column names
            df.columns = ["Name_Arabic", "Evaluation", "Test", "Exam", "Average"]
            df["Name"] = df["Name_Arabic"] # Keep consistent 'Name' column

            # Ensure numeric types
            for col in ["Evaluation", "Test", "Exam", "Average"]:
                df[col] = pd.to_numeric(df[col], errors='coerce')

            # Drop rows with any NaN values in numeric columns after conversion
            original_rows = len(df)
            df.dropna(subset=["Evaluation", "Test", "Exam", "Average"], inplace=True)
            if len(df) < original_rows:
                st.warning(f"تحذير في القسم '{sheet_name}': تم حذف بعض الصفوف بسبب بيانات غير رقمية في أعمدة العلامات.")

            # Drop rows where name is NaN or empty
            df.dropna(subset=["Name"], inplace=True)
            df = df[df["Name"].astype(str).str.strip() != ""]

            if not df.empty:
                 processed_data[sheet_name] = df
            else:
                 st.warning(f"تحذير: القسم '{sheet_name}' فارغ أو لا يحتوي على بيانات صالحة بعد المعالجة.")

        else:
            st.error(f"خطأ في تنسيق القسم '{sheet_name}': الأعمدة المتوقعة هي {expected_cols} أو {expected_cols_alt} ولكن تم العثور على {list(df.columns)}. سيتم تجاهل هذا القسم.")

    if not processed_data:
        st.error("لم يتم تحميل أي بيانات صالحة من الأقسام. يرجى التحقق من تنسيق ملف Excel.")
        return None

    return processed_data

# --- Helper Functions (Remain the same) ---

def find_student(name_input, df):
    """Finds the student using fuzzy matching."""
    if df is None or 'Name' not in df.columns:
        return None, 0
    names = df['Name'].tolist()
    if not names:
        return None, 0
    # Use token_set_ratio for better matching with different word orders or partial names
    match = process.extractOne(name_input.strip(), names, scorer=fuzz.token_set_ratio, score_cutoff=75) # Adjust cutoff score if needed
    if match:
        # Use .loc for safer indexing
        student_data = df.loc[df['Name'] == match[0]].iloc[0]
        return student_data, match[1] # Return data and score
    return None, 0

def generate_feedback(student_data):
    """Generates feedback based on student performance."""
    avg = student_data['Average']
    test = student_data['Test']
    exam = student_data['Exam']
    evaluation = student_data['Evaluation']
    feedback = []
    guidance = []

    # General Performance based on Average
    if avg >= 18:
        feedback.append(f"**أداء ممتاز جداً!** معدلك العام ({avg:.2f}) يعكس تفوقك واجتهادك الكبير في المادة. استمر على هذا المنوال الرائع.")
        guidance.append("حافظ على هذا المستوى العالي بالمراجعة المستمرة وحل تمارين إضافية لتوسيع معرفتك.")
    elif avg >= 15:
        feedback.append(f"**أداء جيد جداً.** معدلك العام ({avg:.2f}) يظهر فهماً جيداً للمادة وقدرة على تحقيق نتائج مميزة.")
        guidance.append("ركز على نقاط القوة لديك وحاول تحسين الجوانب التي تجد فيها بعض الصعوبة من خلال التمارين الإضافية.")
    elif avg >= 12:
        feedback.append(f"**أداء جيد.** معدلك العام ({avg:.2f}) مقبول، وهناك مجال للتحسن والتطور.")
        guidance.append("راجع الدروس بانتظام، ولا تتردد في طلب المساعدة من الأستاذ أو الزملاء في النقاط غير الواضحة.")
    elif avg >= 10:
        feedback.append(f"**أداء متوسط.** معدلك العام ({avg:.2f}) يتطلب المزيد من الجهد والمثابرة.")
        guidance.append("ضع خطة مراجعة منظمة، وركز على فهم المفاهيم الأساسية وحل التمارين بشكل مكثف.")
    else:
        feedback.append(f"**الأداء بحاجة إلى تحسين.** معدلك العام ({avg:.2f}) يشير إلى وجود صعوبات في المادة.")
        guidance.append("من الضروري تكثيف الجهود، والمراجعة الدقيقة للدروس، وطلب الدعم الفوري من الأستاذ لفهم النقاط الصعبة.")

    # Comparison: Test vs Exam (Evolution)
    if exam > test:
        feedback.append(f"**تطور ملحوظ!** نلاحظ تحسناً في أدائك بين الفرض ({test:.2f}) والاختبار ({exam:.2f}). هذا يدل على استيعابك للملاحظات وجهدك الإضافي.")
        guidance.append("استمر في هذا التطور الإيجابي وحافظ على وتيرة المراجعة.")
    elif exam < test:
        feedback.append(f"**تراجع في الأداء.** نلاحظ انخفاضاً في العلامة بين الفرض ({test:.2f}) والاختبار ({exam:.2f}).")
        guidance.append("راجع أخطاءك في الاختبار وحاول فهم أسباب التراجع. قد تحتاج إلى تغيير طريقة المراجعة أو تكثيف الجهد قبل الاختبارات القادمة.")
    else:
        feedback.append(f"**أداء مستقر** بين الفرض ({test:.2f}) والاختبار ({exam:.2f}).")
        guidance.append("حافظ على هذا الاستقرار مع السعي نحو التحسين المستمر.")

    # Comparison: Evaluation vs Test/Exam
    if evaluation >= 15 and (test < 12 or exam < 12):
         feedback.append("**ملاحظة هامة:** علامتك في التقويم المستمر جيدة، لكن هناك تراجع في الفرض أو الاختبار. ")
         guidance.append("قد يشير هذا إلى أن المشاركة والتفاعل في القسم جيدان، لكن هناك حاجة لتركيز أكبر أثناء المراجعة للامتحانات الكتابية. تأكد من فهم الأسئلة جيداً قبل الإجابة.")
    elif evaluation < 12 and (test >= 15 or exam >= 15):
         feedback.append("**ملاحظة هامة:** أداؤك في الفروض أو الاختبارات جيد، لكن علامة التقويم المستمر أقل من المتوقع.")
         guidance.append("حاول زيادة المشاركة والتفاعل في القسم، وإنجاز الواجبات المطلوبة في وقتها لتحسين علامة التقويم.")


    return "\n\n".join(feedback), "\n\n".join(guidance)

def create_charts(student_data):
    """Creates Plotly charts for student scores."""
    scores = {
        'التقويم': student_data['Evaluation'],
        'الفرض': student_data['Test'],
        'الإختبار': student_data['Exam']
    }
    df_scores = pd.DataFrame(list(scores.items()), columns=['التقييم', 'العلامة'])

    # Pie Chart
    fig_pie = px.pie(df_scores, values='العلامة', names='التقييم', title='توزيع العلامات حسب نوع التقييم',
                     hole=0.3, color_discrete_sequence=px.colors.sequential.RdBu)
    fig_pie.update_traces(textposition='inside', textinfo='percent+label+value')

    # Bar Chart
    fig_bar = px.bar(df_scores, x='التقييم', y='العلامة', title='مقارنة العلامات بين أنواع التقييم',
                     text='العلامة', color='التقييم', color_discrete_sequence=px.colors.qualitative.Pastel)
    fig_bar.update_traces(texttemplate='%{text:.2f}', textposition='outside')
    fig_bar.update_layout(yaxis_title="العلامة", xaxis_title="نوع التقييم")

    return fig_pie, fig_bar

def send_email(subject, body, to_email):
    """Sends an email using configured SMTP settings."""
    if not EMAIL_SENDER_USER or not EMAIL_SENDER_PASSWORD:
        return False, "خطأ: لم يتم تكوين بيانات اعتماد البريد الإلكتروني للمرسل (EMAIL_SENDER_USER, EMAIL_SENDER_PASSWORD). يرجى تكوينها كمتغيرات بيئة في بيئة النشر."

    msg = MIMEText(body, 'plain', 'utf-8')
    msg['Subject'] = subject
    msg['From'] = EMAIL_SENDER_USER
    msg['To'] = to_email

    try:
        with smtplib.SMTP(EMAIL_HOST, EMAIL_PORT) as server:
            server.starttls()
            server.login(EMAIL_SENDER_USER, EMAIL_SENDER_PASSWORD)
            server.sendmail(EMAIL_SENDER_USER, [to_email], msg.as_string())
        return True, "تم إرسال الرسالة بنجاح!"
    except smtplib.SMTPAuthenticationError:
        return False, "خطأ في المصادقة. تأكد من صحة اسم المستخدم وكلمة المرور للبريد الإلكتروني للمرسل، وتفعيل 'الوصول للتطبيقات الأقل أمانًا' أو استخدام كلمة مرور التطبيق إذا كنت تستخدم Gmail."
    except Exception as e:
        # Log the detailed error for debugging on the server side
        print(f"SMTP Error: {e}")
        return False, f"حدث خطأ أثناء إرسال البريد الإلكتروني. يرجى المحاولة مرة أخرى لاحقاً أو الاتصال بالمسؤول."

def log_visitor(page):
    """Logs visitor access to a file."""
    try:
        # Ensure the directory exists (useful for some deployment environments)
        log_dir = os.path.dirname(VISITOR_LOG_FILE)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)

        with open(VISITOR_LOG_FILE, "a", encoding='utf-8') as f:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            # Getting client IP in Streamlit Cloud/Render can be tricky and might require specific headers
            ip_address = "Unknown"
            user_agent = "Unknown"
            try:
                # This is a common way but might not work in all environments
                from streamlit.web.server.server import Server
                session_info = Server.get_current()._get_session_info(st.runtime.scriptrunner.get_script_run_ctx().session_id)
                if session_info:
                    ip_address = session_info.client.ip
                    user_agent = session_info.client.user_agent
            except Exception:
                 # Fallback or check headers if deployed behind proxy
                 pass # Keep as Unknown if unable to fetch

            f.write(f"{timestamp} - IP: {ip_address} - Page: {page} - UserAgent: {user_agent}\n")
    except Exception as e:
        print(f"Error logging visitor: {e}") # Log error to console/server logs

def check_password(hashed_password, user_password):
    """Verifies the provided password against the stored hash."""
    return hashlib.sha256(user_password.encode()).hexdigest() == hashed_password

# --- Load Data --- (Now from Excel)
try:
    all_data = load_student_data_from_excel(STUDENT_DATA_FILE)
    if all_data:
        CLASS_NAMES = list(all_data.keys())
    else:
        # Stop the app if data loading failed critically
        st.error("توقف التطبيق بسبب فشل تحميل بيانات الأقسام.")
        st.stop()
except Exception as e:
    st.error(f"خطأ فادح وغير متوقع عند محاولة تحميل البيانات: {e}")
    # Optionally log the full traceback for debugging
    # import traceback
    # st.error(traceback.format_exc())
    st.stop()


# --- Streamlit App Layout ---

st.title(APP_TITLE)

# --- Visitor Logging ---
if 'visitor_logged' not in st.session_state:
    log_visitor("App Load")
    st.session_state['visitor_logged'] = True


# --- Sidebar ---
st.sidebar.header("اختيار القسم والتلميذ")
selected_class = st.sidebar.selectbox("اختر القسم:", CLASS_NAMES, index=None, placeholder="اختر القسم أولاً...") # Use index=None and placeholder

if selected_class:
    df_class = all_data.get(selected_class) # Use .get for safety
    if df_class is not None:
        student_name_input = st.sidebar.text_input("أدخل اسم ولقب التلميذ:", key="student_name_input", placeholder="مثال: الحاج موسى عبد الغني")
        search_button = st.sidebar.button("بحث عن النتائج")

        if search_button and student_name_input:
            log_visitor(f"Search: {selected_class} - '{student_name_input}'")
            student_data, match_score = find_student(student_name_input, df_class)

            if student_data is not None:
                st.session_state['selected_student_data'] = student_data
                st.session_state['selected_class'] = selected_class # Store selected class
                st.sidebar.success(f"تم العثور على: {student_data['Name_Arabic']} (تطابق بنسبة {match_score}%)")
                # Clear previous error messages if any
                if 'search_error' in st.session_state: del st.session_state['search_error']
            else:
                st.session_state['selected_student_data'] = None
                st.session_state['search_error'] = "لم يتم العثور على تلميذ بهذا الاسم في القسم المحدد. يرجى التأكد من الاسم والقسم والمحاولة مرة أخرى."
                st.sidebar.error(st.session_state['search_error'])

        elif not student_name_input and search_button:
             st.sidebar.warning("يرجى إدخال اسم ولقب التلميذ للبحث.")
    else:
        st.sidebar.error(f"خطأ داخلي: لم يتم العثور على بيانات للقسم المحدد '{selected_class}'.")

# Display search error in main area if exists
if 'search_error' in st.session_state and not st.session_state.get('selected_student_data'):
    st.error(st.session_state['search_error'])


# --- Main Content Area ---
# Check if student data is loaded in session state
if 'selected_student_data' in st.session_state and st.session_state['selected_student_data'] is not None:
    student_data = st.session_state['selected_student_data']
    student_name = student_data['Name_Arabic'] # Use Arabic name for display
    current_class = st.session_state['selected_class'] # Get class from session

    st.header(f"نتائج التلميذ: {student_name}")
    st.subheader(f"القسم: {current_class}")

    # Display Results Table
    st.markdown("### النتائج الكاملة:")
    results_df = pd.DataFrame([student_data]) # Create a DataFrame for display
    # Select and rename columns for display
    display_df = results_df[['Evaluation', 'Test', 'Exam', 'Average']].rename(columns={
        'Evaluation': 'التقويم',
        'Test': 'الفرض',
        'Exam': 'الإختبار',
        'Average': 'المعدل'
    })
    st.dataframe(display_df.style.format("{:.2f}"), use_container_width=True)

    # Display Result Evolution (Test vs Exam)
    st.markdown("### تطور النتائج (الفرض مقابل الاختبار):")
    evolution_data = {
        'التقييم': ['الفرض', 'الإختبار'],
        'العلامة': [student_data['Test'], student_data['Exam']]
    }
    fig_evolution = px.line(pd.DataFrame(evolution_data), x='التقييم', y='العلامة', title="مقارنة بين علامة الفرض والاختبار", markers=True, text='العلامة')
    fig_evolution.update_traces(texttemplate='%{text:.2f}', textposition='top center')
    fig_evolution.update_layout(yaxis_title="العلامة", xaxis_title="نوع التقييم")
    st.plotly_chart(fig_evolution, use_container_width=True)


    # Display Charts
    st.markdown("### الرسوم البيانية:")
    try:
        fig_pie, fig_bar = create_charts(student_data)
        col1, col2 = st.columns(2)
        with col1:
            st.plotly_chart(fig_pie, use_container_width=True)
        with col2:
            st.plotly_chart(fig_bar, use_container_width=True)
    except Exception as e:
        st.error(f"حدث خطأ أثناء إنشاء الرسوم البيانية: {e}")


    # Display Feedback and Guidance
    st.markdown("### الملاحظات والتوجيهات:")
    try:
        feedback, guidance = generate_feedback(student_data)
        st.info(f"**ملاحظات:**\n\n{feedback}")
        st.warning(f"**توجيهات:**\n\n{guidance}")
    except Exception as e:
        st.error(f"حدث خطأ أثناء إنشاء الملاحظات والتوجيهات: {e}")


else:
    # Show initial welcome message only if no search error exists
     if 'search_error' not in st.session_state:
        st.info("يرجى اختيار القسم من القائمة الجانبية، ثم إدخال اسم التلميذ والضغط على زر البحث لعرض النتائج.")

# --- Exam Paper Section (Using Correct Relative Paths) ---
st.sidebar.markdown("---")
show_exam = st.sidebar.checkbox("عرض نموذج الاختبار وتصحيحه", key="show_exam_cb")

if show_exam:
    log_visitor("View Exam Paper")
    st.markdown("---")
    st.header("نموذج اختبار مادة الذكاء الاصطناعي وتصحيحه")
    st.write("المستوى: الثانية ثانوي رياضيات (نموذج)") # Specify it's an example

    # Corrected image paths based on user's GitHub screenshot
    exam_image_paths = [
        "1748355922145.jpg", # Exam Page 1 - Relative path
        "1748355927881.jpg"  # Exam Page 2 - Relative path
    ]
    correction_image_paths = [
        "IMG-20250522-WA0002.jpg", # Correction Page 1 - Relative path
        "IMG-20250522-WA0003.jpg"  # Correction Page 2 - Relative path
    ]

    st.subheader("نموذج الاختبار:")
    img_col1, img_col2 = st.columns(2)
    with img_col1:
        try:
            st.image(exam_image_paths[0], use_column_width=True)
        except FileNotFoundError:
             st.error(f"خطأ: لم يتم العثور على ملف الصورة '{exam_image_paths[0]}'. تأكد من وجوده في نفس مجلد التطبيق.")
        except Exception as e:
             st.error(f"خطأ في تحميل الصورة {os.path.basename(exam_image_paths[0])}: {e}")
    with img_col2:
        try:
            st.image(exam_image_paths[1], use_column_width=True)
        except FileNotFoundError:
             st.error(f"خطأ: لم يتم العثور على ملف الصورة '{exam_image_paths[1]}'. تأكد من وجوده في نفس مجلد التطبيق.")
        except Exception as e:
             st.error(f"خطأ في تحميل الصورة {os.path.basename(exam_image_paths[1])}: {e}")


    st.subheader("تصحيح الاختبار:")
    img_col3, img_col4 = st.columns(2)
    with img_col3:
         try:
            st.image(correction_image_paths[0], use_column_width=True)
         except FileNotFoundError:
             st.error(f"خطأ: لم يتم العثور على ملف الصورة '{correction_image_paths[0]}'. تأكد من وجوده في نفس مجلد التطبيق.")
         except Exception as e:
             st.error(f"خطأ في تحميل الصورة {os.path.basename(correction_image_paths[0])}: {e}")
    with img_col4:
         try:
            st.image(correction_image_paths[1], use_column_width=True)
         except FileNotFoundError:
             st.error(f"خطأ: لم يتم العثور على ملف الصورة '{correction_image_paths[1]}'. تأكد من وجوده في نفس مجلد التطبيق.")
         except Exception as e:
             st.error(f"خطأ في تحميل الصورة {os.path.basename(correction_image_paths[1])}: {e}")

# --- Contact Form Section ---
st.sidebar.markdown("---")
st.sidebar.header("تواصل معنا")
with st.sidebar.form(key='contact_form', clear_on_submit=True):
    contact_name = st.text_input("الاسم:")
    contact_subject = st.text_input("الموضوع:")
    contact_message = st.text_area("الرسالة:")
    submit_button = st.form_submit_button(label='إرسال الرسالة')

    if submit_button:
        if contact_name and contact_subject and contact_message:
            log_visitor(f"Contact Form Submission by {contact_name}")
            email_body = f"رسالة جديدة من نموذج التواصل في تطبيق نتائج التلاميذ:\n\nالاسم: {contact_name}\n\nالموضوع: {contact_subject}\n\nالرسالة:\n{contact_message}"
            email_subject = f"رسالة من تطبيق نتائج التلاميذ: {contact_subject}"
            success, message = send_email(email_subject, email_body, CONTACT_EMAIL)
            if success:
                st.sidebar.success(message)
            else:
                st.sidebar.error(message)
                st.sidebar.warning("تنبيه للمشرف: تأكد من تكوين متغيرات البيئة EMAIL_SENDER_USER و EMAIL_SENDER_PASSWORD في بيئة النشر.")
        else:
            st.sidebar.warning("يرجى ملء جميع حقول النموذج.")


# --- Admin Section ---
st.sidebar.markdown("---")
st.sidebar.header("قسم المشرف")

# Check login status
if not st.session_state.get('admin_logged_in', False):
    admin_user_input = st.sidebar.text_input("اسم المستخدم للمشرف:", key="admin_user")
    admin_pass_input = st.sidebar.text_input("كلمة المرور للمشرف:", type="password", key="admin_pass")
    login_button = st.sidebar.button("تسجيل الدخول للمشرف")

    if login_button:
        if admin_user_input == ADMIN_USERNAME and check_password(ADMIN_PASSWORD_HASH, admin_pass_input):
            st.session_state['admin_logged_in'] = True
            st.sidebar.success("تم تسجيل الدخول بنجاح!")
            st.rerun() # Rerun to show admin panel
        else:
            st.session_state['admin_logged_in'] = False
            st.sidebar.error("بيانات الدخول غير صحيحة.")
else:
    # Admin is logged in
    st.sidebar.success("أنت مسجل الدخول كمشرف.")
    st.sidebar.subheader("لوحة تحكم المشرف")

    # Display Visitor Log
    if st.sidebar.button("عرض سجل الزوار"):
        log_visitor("Admin View Logs")
        st.markdown("---")
        st.header("سجل زوار التطبيق")
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
        st.rerun() # Rerun to hide admin panel


# --- Footer ---
st.markdown("---")
st.markdown("Developed by Mr. Oussama SEBROU") # Corrected typo

