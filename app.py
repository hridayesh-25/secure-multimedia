import streamlit as st
import os
import sender_module
import receiver_module
import pandas as pd
import plotly.express as px
import streamlit as st

decrypted_folder = "decrypted_files"

files = os.listdir(decrypted_folder)

if files:
    latest_file = os.path.join(decrypted_folder, files[0])

    with open(latest_file, "rb") as f:
        st.download_button(
            label="Download Decrypted File",
            data=f,
            file_name=files[0],
            mime="application/octet-stream"
        )

os.makedirs("input_files", exist_ok=True)
os.makedirs("encrypted_files", exist_ok=True)
os.makedirs("decrypted_files", exist_ok=True)
os.makedirs("results", exist_ok=True)

st.set_page_config(
    page_title="Secure Multimedia Cloud System",
    layout="wide"
)

st.title("🔐 Secure Multimedia Cloud Transmission System")
st.markdown("Hybrid AES–RSA–Hash Architecture with Cloud Mediation")

page = st.sidebar.radio(
    "Navigation",
    ["Sender", "Receiver", "Analytics"]
)

# =====================================================
# 🟢 SENDER PAGE
# =====================================================
if page == "Sender":

    st.header("📤 Sender Mode")

    uploaded_file = st.file_uploader("Upload File to Encrypt", type=None)

    if uploaded_file is not None:

        input_path = os.path.join("input_files", uploaded_file.name)

        with open(input_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        st.success("File uploaded to sender successfully.")

        if st.button("Encrypt & Upload to Cloud"):

            with st.spinner("Encrypting and uploading..."):
                sender_module.sender_pipeline(input_path)

            st.success("File encrypted and uploaded to S3 successfully.")

# =====================================================
# 🔵 RECEIVER PAGE
# =====================================================
elif page == "Receiver":

    st.header("📥 Receiver Mode")

    if st.button("Download & Decrypt from Cloud"):

        with st.spinner("Downloading and decrypting..."):
            receiver_module.receiver_pipeline()

        st.success("File downloaded and decrypted successfully.")

# =====================================================
# 📊 ANALYTICS PAGE
# =====================================================
elif page == "Analytics":

    st.header("📊 System Performance Analytics")

    tab1, tab2 = st.tabs(["Crypto Analysis", "Cloud Analysis"])

    # -------------------------
    # Crypto Analytics
    # -------------------------
    with tab1:
        if os.path.exists("results/crypto_results.csv"):

            df = pd.read_csv("results/crypto_results.csv")

            st.dataframe(df)

            fig1 = px.line(
                df,
                x="File Size (bytes)",
                y="Crypto Time",
                color="Mode",
                markers=True,
                title="File Size vs Crypto Time"
            )
            st.plotly_chart(fig1, use_container_width=True)

            fig2 = px.line(
                df,
                x="File Size (bytes)",
                y="Overhead (%)",
                color="Mode",
                markers=True,
                title="File Size vs Overhead (%)"
            )
            st.plotly_chart(fig2, use_container_width=True)

        else:
            st.warning("crypto_results.csv not found.")

    # -------------------------
    # Cloud Analytics
    # -------------------------
    with tab2:
        if os.path.exists("results/cloud_results.csv"):

            df = pd.read_csv("results/cloud_results.csv")

            st.dataframe(df)

            fig1 = px.line(
                df,
                x="File Size (bytes)",
                y="Upload Time",
                markers=True,
                title="File Size vs Upload Time"
            )
            st.plotly_chart(fig1, use_container_width=True)

            fig2 = px.line(
                df,
                x="File Size (bytes)",
                y="End-to-End Time",
                markers=True,
                title="File Size vs End-to-End Time"
            )
            st.plotly_chart(fig2, use_container_width=True)

            fig3 = px.line(
                df,
                x="File Size (bytes)",
                y="Crypto Percentage (%)",
                markers=True,
                title="Crypto Contribution to End-to-End Time (%)"
            )
            st.plotly_chart(fig3, use_container_width=True)

        else:
            st.warning("cloud_results.csv not found.")