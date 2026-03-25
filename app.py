import streamlit as st
import os
import sender_module
import receiver_module
import pandas as pd
import plotly.express as px
import time

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
    st.session_state.role = None

if not st.session_state.authenticated:

    st.title("Secure Multimedia System Login")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):

        if username == "sender" and password == "secure123":
            st.session_state.authenticated = True
            st.session_state.role = "sender"
            st.success("Sender login successful")
            st.rerun()

        elif username == "receiver" and password == "receive123":
            st.session_state.authenticated = True
            st.session_state.role = "receiver"
            st.success("Receiver login successful")
            st.rerun()

        else:
            st.error("Invalid credentials")

    st.stop()
    
    
if st.sidebar.button("Logout"):
    st.session_state.authenticated = False
    st.session_state.role = None
    st.rerun()

os.makedirs("input_files", exist_ok=True)
os.makedirs("encrypted_files", exist_ok=True)
os.makedirs("decrypted_files", exist_ok=True)
os.makedirs("results", exist_ok=True)

st.set_page_config(
    page_title="Secure Multimedia Cloud System",
    layout="wide"
)

st.title("🔐 Secure Multimedia Cloud Transmission System")
st.markdown("Hybrid AES–RSA–SHA256 Secure Architecture with Cloud Storage")

st.markdown("### System Architecture")

col1, col2, col3 = st.columns(3)

with col1:
    st.subheader("Sender")
    st.write("📤 Upload Multimedia File")
    st.write("🔐 AES Encryption")
    st.write("🔑 RSA Key Encryption")
    st.write("🧾 Digital Signature")

with col2:
    st.subheader("Cloud")
    st.write("☁ AWS S3 Storage")
    st.write("🔒 Encrypted File Stored")
    st.write("🚫 Cloud Cannot Read Data")

with col3:
    st.subheader("Receiver")
    st.write("📥 Download Encrypted File")
    st.write("🔓 RSA Key Decryption")
    st.write("🔓 AES File Decryption")
    st.write("✔ Integrity Verification")
    
st.markdown("---")
st.markdown("### Secure Transmission Flow")

st.write("Sender → AES Encryption → RSA Key Protection → ☁ Cloud Storage → Receiver Verification → Secure Decryption")

if st.session_state.role == "sender":
    page = st.sidebar.radio(
        "Navigation",
        ["Sender", "Analytics"]
    )

elif st.session_state.role == "receiver":
    page = st.sidebar.radio(
        "Navigation",
        ["Receiver", "Analytics"]
    )

# =====================================================
# 🟢 SENDER PAGE
# =====================================================
if page == "Sender":

    st.header("📤 Sender Mode")

    col1, col2 = st.columns([2,1])

    with col2:
        st.subheader("Security Layers")
        st.success("AES-256 File Encryption")
        st.success("RSA-2048 Key Protection")
        st.success("SHA-256 Integrity Check")
        st.success("RSA-PSS Digital Signature")

    uploaded_file = st.file_uploader("Upload File to Encrypt", type=None)

    if uploaded_file is not None:

        input_path = os.path.join("input_files", uploaded_file.name)

        with open(input_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        st.success("File uploaded successfully.")

        if st.button("Start Secure Transmission"):

            with st.status("Starting Encryption Pipeline...", expanded=True) as status:

                st.write("Generating AES-256 session key...")
                time.sleep(1)

                st.write("Encrypting file using AES...")
                time.sleep(1)

                st.write("Encrypting AES key using RSA-2048...")
                time.sleep(1)

                st.write("Generating SHA-256 hash...")
                time.sleep(1)

                st.write("Creating digital signature (RSA-PSS)...")
                time.sleep(1)

                st.write("Uploading encrypted package to AWS S3 cloud...")
                sender_module.sender_pipeline(input_path)
                time.sleep(1)

                status.update(label="Transmission Completed Successfully", state="complete")

            st.success("Encrypted file uploaded securely to cloud.")

# =====================================================
# 🔵 RECEIVER PAGE
# =====================================================
elif page == "Receiver":

    st.header("📥 Receiver Mode")

    col1, col2 = st.columns([2,1])

    with col2:
        st.subheader("Security Verification")
        st.info("Decrypt AES Key (RSA)")
        st.info("Decrypt File (AES)")
        st.info("Verify Digital Signature")
        st.info("Check SHA-256 Integrity")

    if st.button("Download & Start Secure Decryption"):

        with st.status("Starting Decryption Pipeline...", expanded=True) as status:

            st.write("Downloading encrypted package from cloud...")
            time.sleep(1)

            st.write("Decrypting AES key using RSA private key...")
            time.sleep(1)

            st.write("Decrypting file using AES-256...")
            time.sleep(1)

            st.write("Verifying digital signature...")
            time.sleep(1)

            st.write("Recomputing SHA-256 hash...")
            time.sleep(1)

            st.write("Checking file integrity...")
            time.sleep(1)

            decrypted_file = receiver_module.receiver_pipeline()

            status.update(label="Decryption & Verification Completed", state="complete")

        st.success("File successfully decrypted and verified.")

        with open(decrypted_file, "rb") as f:
            st.download_button(
                label="Download Decrypted File",
                data=f,
                file_name=os.path.basename(decrypted_file),
                mime="application/octet-stream"
            )

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

            # fig1 = px.line(
            #     df,
            #     x="File Size (bytes)",
            #     y="Crypto Time",
            #     color="Mode",
            #     markers=True,
            #     title="File Size vs Crypto Time"
            # )
            # fig1.update_layout(
            #     font=dict(size=18),  # increase overall font
            #     title_font=dict(size=20),
            #     xaxis_title_font=dict(size=18),
            #     yaxis_title_font=dict(size=18)
            # )
            # fig1.update_traces(
            #     line=dict(width=3),
            #     marker=dict(size=8)
            # )
            # # fig1.write_image("fig1.png", scale=3)
            # st.plotly_chart(fig1, use_container_width=True)

            fig2 = px.line(
                df,
                x="File Size (bytes)",
                y="Overhead (%)",
                color="Mode",
                markers=True,
                title="File Size vs Overhead (%)"
            )
            # fig1.update_layout(
            #     font=dict(size=18),  # increase overall font
            #     title_font=dict(size=20),
            #     xaxis_title_font=dict(size=18),
            #     yaxis_title_font=dict(size=18)
            # )
            # fig1.update_traces(
            #     line=dict(width=3),
            #     marker=dict(size=8)
            # )
            # fig1.write_image("fig1.png", scale=3)
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
            fig1.update_layout(
                font=dict(size=30),  # increase overall font
                title_font=dict(size=30),
                xaxis_title_font=dict(size=30),
                yaxis_title_font=dict(size=30)
            )
            fig1.update_traces(
                line=dict(width=5),
                marker=dict(size=13)
            )
            # fig1.write_image("fig1.png", scale=3)
            st.plotly_chart(fig1, use_container_width=True)

            fig2 = px.line(
                df,
                x="File Size (bytes)",
                y="End-to-End Time",
                markers=True,
                title="File Size vs End-to-End Time"
            )
            fig2.update_layout(
                font=dict(size=18),  # increase overall font
                title_font=dict(size=20),
                xaxis_title_font=dict(size=18),
                yaxis_title_font=dict(size=18)
            )
            fig2.update_traces(
                line=dict(width=3),
                marker=dict(size=8)
            )
            # fig2.write_image("fig2.png", scale=3)
            st.plotly_chart(fig2, use_container_width=True)

            fig3 = px.line(
                df,
                x="File Size (bytes)",
                y="Crypto Percentage (%)",
                markers=True,
                title="Crypto Contribution to End-to-End Time (%)"
            )
            fig3.update_layout(
                font=dict(size=18),  # increase overall font
                title_font=dict(size=20),
                xaxis_title_font=dict(size=18),
                yaxis_title_font=dict(size=18)
            )
            fig3.update_traces(
                line=dict(width=3),
                marker=dict(size=8)
            )
            # fig3.write_image("fig3.png", scale=3)
            st.plotly_chart(fig3, use_container_width=True)

        else:
            st.warning("cloud_results.csv not found.")