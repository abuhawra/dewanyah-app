import streamlit as st
import pandas as pd
import requests

# --- إعدادات الصفحة ---
st.set_page_config(page_title="حسابات الديوانية", page_icon="💰", layout="wide")

# --- تهيئة متغير لتأكيد الحذف ---
if "confirm_delete_id" not in st.session_state:
    st.session_state.confirm_delete_id = None

# --- إعدادات الاتصال المباشر (REST API) ---
url = "https://zttkamtuccxgkugqzhwr.supabase.co/rest/v1/transactions"
key = st.secrets["SUPABASE_KEY"]

headers = {
    "apikey": key,
    "Authorization": f"Bearer {key}",
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}

st.title("💰 تطبيق حسابات الديوانية")

# --- القسم الأول: تسجيل عملية جديدة ---
st.header("➕ تسجيل عملية جديدة")
with st.container():
    col1, col2, col3 = st.columns(3)
    with col1:
        t_type = st.selectbox("نوع العملية", ["واردات", "مصاريف", "رصيد افتتاحي"])
    with col2:
        amount = st.number_input("المبلغ (ر.س)", min_value=0.0, step=1.0)
    with col3:
        desc = st.text_input("التفاصيل (البيان)")

    if st.button("حفظ العملية"):
        if amount > 0:
            data = {
                "transaction_type": t_type,
                "amount": amount,
                "description": desc
            }
            response = requests.post(url, headers=headers, json=data)
            
            if response.status_code in [200, 201]:
                st.success("تم تسجيل العملية بنجاح!")
                st.rerun() 
            else:
                st.error(f"حدث خطأ أثناء الحفظ: {response.text}")
        else:
            st.error("يرجى إدخال مبلغ أكبر من صفر.")

st.divider()

# --- القسم الثاني: جلب وعرض البيانات ---
get_response = requests.get(f"{url}?select=*&order=created_at.desc", headers=headers)

if get_response.status_code == 200 and len(get_response.json()) > 0:
    df = pd.DataFrame(get_response.json())
    
    # حساب الأرصدة
    total_income = df[df['transaction_type'] == 'واردات']['amount'].sum()
    total_expense = df[df['transaction_type'] == 'مصاريف']['amount'].sum()
    initial_balance = df[df['transaction_type'] == 'رصيد افتتاحي']['amount'].sum()
    
    current_balance = (initial_balance + total_income) - total_expense

    # --- عرض البطاقات الإحصائية مع خلفيات ملونة ونص أسود ---
    c1, c2, c3 = st.columns(3)
    
    # بطاقة الواردات (خلفية خضراء فاتحة، نص أسود)
    c1.markdown(f"""
    <div style="background-color: #d4edda; border: 1px solid #c3e6cb; padding: 20px; border-radius: 10px; direction: rtl; text-align: right; box-shadow: 0 4px 6px rgba(0,0,0,0.05);">
        <p style="font-size: 16px; margin-bottom: 0px; font-weight: bold; color: black;">إجمالي الواردات</p>
        <h2 style="color: black; margin-top: 5px; margin-bottom: 0px; font-size: 2.5rem;">{total_income} <span style="font-size: 1.5rem;">ر.س</span></h2>
    </div>
    """, unsafe_allow_html=True)

    # بطاقة المصاريف (خلفية حمراء فاتحة، نص أسود)
    c2.markdown(f"""
    <div style="background-color: #f8d7da; border: 1px solid #f5c6cb; padding: 20px; border-radius: 10px; direction: rtl; text-align: right; box-shadow: 0 4px 6px rgba(0,0,0,0.05);">
        <p style="font-size: 16px; margin-bottom: 0px; font-weight: bold; color: black;">إجمالي المصاريف</p>
        <h2 style="color: black; margin-top: 5px; margin-bottom: 0px; font-size: 2.5rem;">{total_expense} <span style="font-size: 1.5rem;">ر.س</span></h2>
    </div>
    """, unsafe_allow_html=True)

    # بطاقة الرصيد الحالي (خلفية زرقاء فاتحة، نص أسود)
    c3.markdown(f"""
    <div style="background-color: #d1ecf1; border: 1px solid #bee5eb; padding: 20px; border-radius: 10px; direction: rtl; text-align: right; box-shadow: 0 4px 6px rgba(0,0,0,0.05);">
        <p style="font-size: 16px; margin-bottom: 0px; font-weight: bold; color: black;">الرصيد الحالي</p>
        <h2 style="color: black; margin-top: 5px; margin-bottom: 0px; font-size: 2.5rem;">{current_balance} <span style="font-size: 1.5rem;">ر.س</span></h2>
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    # --- القسم الثالث: جدول العمليات الملون ونظام الحذف ---
    st.header("📑 آخر العمليات")

    # رسالة تأكيد الحذف
    if st.session_state.confirm_delete_id:
        target_row = df[df['id'] == st.session_state.confirm_delete_id]
        if not target_row.empty:
            target_desc = target_row.iloc[0]['description']
            target_amt = target_row.iloc[0]['amount']
            
            st.warning(f"⚠️ **تأكيد الحذف:** هل أنت متأكد أنك تريد حذف عملية ( {target_desc} ) بمبلغ {target_amt} ر.س بشكل نهائي؟")
            
            btn_col1, btn_col2, _ = st.columns([1, 1, 4])
            with btn_col1:
                if st.button("✅ نعم، احذف", type="primary"):
                    delete_url = f"{url}?id=eq.{st.session_state.confirm_delete_id}"
                    del_response = requests.delete(delete_url, headers=headers)
                    if del_response.status_code in [200, 204]:
                        st.session_state.confirm_delete_id = None
                        st.rerun()
                    else:
                        st.error("فشل الحذف.")
            with btn_col2:
                if st.button("❌ إلغاء"):
                    st.session_state.confirm_delete_id = None
                    st.rerun()
            st.markdown("---")
    
    # تصميم عناوين الجدول
    h1, h2, h3, h4, h5 = st.columns([2, 1.5, 1.5, 3, 1])
    h1.write("**التاريخ**")
    h2.write("**النوع**")
    h3.write("**المبلغ**")
    h4.write("**البيان**")
    h5.write("**إجراء**")
    
    st.markdown("---")
    
    # المرور على كل عملية وعرضها بالألوان
    for index, row in df.iterrows():
        c1, c2, c3, c4, c5 = st.columns([2, 1.5, 1.5, 3, 1])
        
        dt = pd.to_datetime(row['created_at']).strftime('%Y-%m-%d %H:%M')
        t_type_val = row['transaction_type']
        amt_val = row['amount']
        desc_val = row['description']
        
        if t_type_val == "مصاريف":
            colored_type = f":red[🔻 {t_type_val}]"
            colored_amt = f":red[- {amt_val} ر.س]"
        elif t_type_val == "واردات":
            colored_type = f":green[🔼 {t_type_val}]"
            colored_amt = f":green[+ {amt_val} ر.س]"
        else:
            colored_type = f":blue[💠 {t_type_val}]"
            colored_amt = f":blue[{amt_val} ر.س]"
        
        c1.write(dt)
        c2.markdown(colored_type)
        c3.markdown(colored_amt)
        c4.write(desc_val)
        
        if c5.button("🗑️", key=f"btn_{row['id']}", help="حذف هذه العملية"):
            st.session_state.confirm_delete_id = row['id']
            st.rerun()
else:
    st.info("لا توجد عمليات مسجلة بعد. ابدأ بإضافة رصيد افتتاحي.")
