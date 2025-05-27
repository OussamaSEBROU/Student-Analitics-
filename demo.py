# demo_fixed.py - Final Single File Version (Data Loading Fixed)

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
# Email sending configuration (User must configure these in deployment environment)
EMAIL_HOST = os.environ.get("EMAIL_HOST", "smtp.gmail.com") # Default to Gmail SMTP
EMAIL_PORT = int(os.environ.get("EMAIL_PORT", 587)) # Default to Gmail TLS port
EMAIL_SENDER_USER = os.environ.get("EMAIL_SENDER_USER") # Sender email address (needs to be set as environment variable)
EMAIL_SENDER_PASSWORD = os.environ.get("EMAIL_SENDER_PASSWORD") # Sender email password (needs to be set as environment variable)

# --- Data Loading Function (FIXED) ---
@st.cache_data # Cache the data loading
def load_student_data():
    # Define expected column names for clarity and robustness
    col_names = ['Name_Arabic', 'Evaluation', 'Test', 'Exam', 'Average']

    # Data for Class 1: قسم الأولى ثانوي علوم - ذكور
    data1 = """اسم التلميذ    التقويم    الفرض    الإختبار    المعدل
حواش عبد اللطيف    16.0    17.0    13.0    14.60
أداود طه    13.0    19.5    12.5    14.10
إمناسن محسن    17.75    18.5    19.75    18.65
الحاج موسى عبد العزيز    17.0    20.0    13.5    15.80
الحاج موسى عبد الغني    19.0    20.0    20.0    19.20
الهيشر عبد الرحمان    15.0    18.75    8.0    13.35
بازين بكير    12.0    19.0    16.5    15.60
باعمارة حسين    16.0    17.5    17.5    17.10
برنوص خالد    18.0    19.25    20.0    18.65
بن الناصر علي    16.0    19.0    19.75    18.50
بهدي حمزة    18.0    19.5    20.0    19.10
تحكوبيت نسيم    12.0    18.5    10.0    12.90
hمودة عبد المجيد    16.0    19.0    10.5    14.60
حواش إبراهيم    19.5    19.0    20.0    18.90
حواش محمد    18.0    19.5    19.75    19.00
دادي عدون سليم    15.0    19.5    11.5    14.90
داود سليمان    12.0    17.0    13.5    14.00
سكوتي عمر    19.0    20.0    20.0    19.00
طباخ علي    17.0    20.0    18.0    17.80
طباخ يحي زكرياء    13.0    19.0    10.0    13.00
طباخ يوسف الصديق    19.0    20.0    20.0    19.00
كراوة ياسين    20.0    20.0    20.0    19.90
لمدهكل عبد النور    10.0    19.25    18.5    15.65
لهزيل سلمان    19.0    20.0    20.0    19.60
نشاشبي عبد الحكيم    14.0    19.5    16.0    16.30
"""
    # Use sep=r'\s+' to handle one or more spaces as delimiter, skip first row (header), provide names
    df1 = pd.read_csv(io.StringIO(data1), sep=r'\s+', engine='python', skiprows=1, names=col_names)

    # Data for Class 2: قسم الثانية ثانوي تسيير واقتصاد
    data2 = """اسم التلميذ    التقويم    الفرض    الإختبار    المعدل
أميني ابراهيم    16.0    10.75    18.0    15.15
الحاج سعيد محمد رضا    19.0    20.0    19.5    19.40
الهيشر عبد الغني    14.0    19.75    15.0    15.15
بازين يوسف    16.0    19.75    10.5    14.15
بزملال سليم    18.0    20.0    20.0    19.60
بن زكري زكري    15.75    17.5    11.0    14.15
بوغلابة عادل    16.75    18.0    11.0    14.55
زاوي إلياس    14.0    18.75    9.0    13.35
شكال عفاري محمد    17.0    20.0    19.75    18.90
عبد النور عبد اللطيف    16.0    20.0    20.0    18.80
قصبي محمد أمين    15.0    16.75    19.5    16.75
"""
    df2 = pd.read_csv(io.StringIO(data2), sep=r'\s+', engine='python', skiprows=1, names=col_names)

    # Data for Class 3: قسم الثانية ثانوي رياضيات
    data3 = """اسم التلميذ    التقويم    الفرض    الإختبار    المعدل
بوكرموش ياسين    19.75    19.0    20.0    19.75
قصبي ياسر    19.75    20.0    20.0    19.95
قضي امين عيسى    18.0    18.5    18.5    18.70
مطياز لقمان الحكيم    20.0    19.0    20.0    19.80
"""
    df3 = pd.read_csv(io.StringIO(data3), sep=r'\s+', engine='python', skiprows=1, names=col_names)

    # Data for Class 4: قسم الثانية ثانوي علوم تجريبية 1 - ذكور
    data4 = """اسم التلميذ    التقويم    الفرض    الإختبار    المعدل
أداود لقمان    18.0    17.0    16.0    16.70
انشاشبي عبد الغني    17.0    19.5    19.5    18.90
بازين أمين حبيب الله    19.0    20.0    18.75    19.20
داود عبد الرحمان    17.0    19.5    20.0    18.90
داودي محمد بن بكير    19.5    20.0    19.5    19.65
رقيق الصادق رضوان    19.0    20.0    20.0    19.80
عبونة يوسف    19.75    20.0    19.75    19.65
عيسى ودادي عبد النور    18.0    18.5    10.5    14.70
محرزي يوسف    18.0    18.5    20.0    19.20
نجار يونس    16.0    19.75    18.5    17.35
"""
    df4 = pd.read_csv(io.StringIO(data4), sep=r'\s+', engine='python', skiprows=1, names=col_names)

    # Data for Class 5: قسم الثانية ثانوي علوم تجريبية 2 - بنات
    data5 = """اسم التلميذة    التقويم    الفرض    الإختبار    المعدل
اداود سناء    20.0    20.0    20.0    20.00
الشيهاني بشرى    19.75    19.75    20.0    19.90
الشيهاني زينب    19.0    20.0    19.5    19.20
الشيهاني وئام    20.0    20.0    19.75    19.70
العلواني رحمة    18.0    19.5    16.0    17.50
بعمور مريا    20.0    19.75    20.0    19.90
بن سليمان لينة    20.0    20.0    20.0    20.00
بهدي صبرينة    16.0    9.0    19.5    15.60
بوسنان إسراء    20.0    20.0    20.0    20.00
حاتة دليلة    18.0    8.0    15.0    14.40
hبيرش ياسمين    16.0    20.0    17.5    17.40
حواش عائشة إكرام    19.0    18.75    19.75    18.85
سيوسيو مروة    18.0    19.5    15.0    17.30
عدون سيرين    20.0    20.0    19.75    19.90
لالوت سلمى    20.0    20.0    20.0    20.00
نشاشبي كريمة    19.75    20.0    20.0    19.95
"""
    # Use specific names for this class initially
    col_names_girls = ['Name_Arabic', 'Evaluation', 'Test', 'Exam', 'Average']
    df5 = pd.read_csv(io.StringIO(data5), sep=r'\s+', engine='python', skiprows=1, names=col_names_girls)

    # Combine into a dictionary
    all_data = {
        "قسم الأولى ثانوي علوم - ذكور": df1,
        "قسم الثانية ثانوي تسيير واقتصاد": df2,
        "قسم الثانية ثانوي رياضيات": df3,
        "قسم الثانية ثانوي علوم تجريبية 1 - ذكور": df4,
        "قسم الثانية ثانوي علوم تجريبية 2 - بنات": df5
    }

    # Standardize column names and types AFTER combining
    for df in all_data.values():
        # Ensure the columns exist before trying to convert
        if all(col in df.columns for col in ['Evaluation', 'Test', 'Exam', 'Average']):
            # Keep a consistent 'Name' column for matching (using the Arabic name)
            df['Name'] = df['Name_Arabic']
            # Ensure numeric types
            for col in ['Evaluation', 'Test', 'Exam', 'Average']:
                 df[col] = pd.to_numeric(df[col], errors='coerce')
            # Handle potential NaN values resulting from coercion errors if any
            df.dropna(subset=['Evaluation', 'Test', 'Exam', 'Average'], inplace=True)
        else:
            # Handle cases where columns might be missing due to read errors
            print(f"Warning: DataFrame missing expected columns. Columns found: {df.columns}")
            # Optionally, raise an error or return an empty structure
            # raise ValueError(f"DataFrame missing expected columns. Columns found: {df.columns}")

    return all_data

# --- Helper Functions ---

def find_student(name_input, df):
    """Finds the student using fuzzy matching."""
    names = df['Name'].tolist()
    # Use token_set_ratio for better matching with different word orders or partial names
    match = process.extractOne(name_input.strip(), names, scorer=fuzz.token_set_ratio, score_cutoff=75) # Adjust cutoff score if needed
    if match:
        student_data = df[df['Name'] == match[0]].iloc[0]
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
                 # headers = st.experimental_get_query_params() # Older method
                 # headers = st.query_params # Newer method - needs checking
                 pass # Keep as Unknown if unable to fetch

            f.write(f"{timestamp} - IP: {ip_address} - Page: {page} - UserAgent: {user_agent}\n")
    except Exception as e:
        print(f"Error logging visitor: {e}") # Log error to console/server logs

def check_password(hashed_password, user_password):
    """Verifies the provided password against the stored hash."""
    return hashlib.sha256(user_password.encode()).hexdigest() == hashed_password

# --- Load Data ---
try:
    all_data = load_student_data()
    CLASS_NAMES = list(all_data.keys())
except Exception as e:
    st.error(f"خطأ فادح في تحميل بيانات التلاميذ: {e}")
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
    df_class = all_data[selected_class]
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

# --- Exam Paper Section (Using Relative Paths) ---
st.sidebar.markdown("---")
show_exam = st.sidebar.checkbox("عرض نموذج الاختبار وتصحيحه", key="show_exam_cb")

if show_exam:
    log_visitor("View Exam Paper")
    st.markdown("---")
    st.header("نموذج اختبار مادة الذكاء الاصطناعي وتصحيحه")
    st.write("المستوى: الثانية ثانوي رياضيات (نموذج)") # Specify it's an example

    # Updated paths assuming images are in the same directory as the script (demo.py)
    exam_image_paths = [
        "1000007226.jpg", # Exam Page 1 - Relative path
        "1000007227.jpg"  # Exam Page 2 - Relative path
    ]
    correction_image_paths = [
        "1000007228.jpg", # Correction Page 1 - Relative path
        "1000007229.jpg"  # Correction Page 2 - Relative path
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
st.markdown("Deloped by.Mr Oussama SEBROU")

