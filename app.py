import streamlit as st
import os
import ffmpeg
import uuid
import tempfile
import subprocess
import shutil
import requests
import zipfile
import platform
from pathlib import Path

# Konfigurasi folder
UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'output'
FFMPEG_FOLDER = 'ffmpeg_bin'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

def check_ffmpeg():
    """Cek apakah FFmpeg tersedia di sistem"""
    # Cek di sistem PATH
    if shutil.which("ffmpeg") is not None:
        return True
    
    # Cek di folder lokal
    local_ffmpeg = os.path.join(FFMPEG_FOLDER, "ffmpeg.exe" if platform.system() == "Windows" else "ffmpeg")
    if os.path.exists(local_ffmpeg):
        return True
    
    return False

def get_ffmpeg_path():
    """Dapatkan path ke FFmpeg executable"""
    # Cek di sistem PATH
    system_ffmpeg = shutil.which("ffmpeg")
    if system_ffmpeg:
        return system_ffmpeg
    
    # Cek di folder lokal
    local_ffmpeg = os.path.join(FFMPEG_FOLDER, "ffmpeg.exe" if platform.system() == "Windows" else "ffmpeg")
    if os.path.exists(local_ffmpeg):
        return local_ffmpeg
    
    return None

def download_ffmpeg_windows():
    """Download FFmpeg untuk Windows"""
    try:
        st.info("Mendownload FFmpeg untuk Windows...")
        
        # URL untuk FFmpeg Windows build
        ffmpeg_url = "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip"
        
        # Download file
        response = requests.get(ffmpeg_url, stream=True)
        response.raise_for_status()
        
        # Simpan ke file temporary
        with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as tmp_file:
            for chunk in response.iter_content(chunk_size=8192):
                tmp_file.write(chunk)
            tmp_file_path = tmp_file.name
        
        # Extract zip file
        os.makedirs(FFMPEG_FOLDER, exist_ok=True)
        with zipfile.ZipFile(tmp_file_path, 'r') as zip_ref:
            # Extract semua file
            zip_ref.extractall(FFMPEG_FOLDER)
        
        # Cari file ffmpeg.exe di dalam folder yang diekstrak
        for root, dirs, files in os.walk(FFMPEG_FOLDER):
            if 'ffmpeg.exe' in files:
                # Pindahkan ke root folder
                src = os.path.join(root, 'ffmpeg.exe')
                dst = os.path.join(FFMPEG_FOLDER, 'ffmpeg.exe')
                shutil.move(src, dst)
                break
        
        # Cleanup
        os.unlink(tmp_file_path)
        
        # Cleanup folder yang tidak diperlukan
        for item in os.listdir(FFMPEG_FOLDER):
            item_path = os.path.join(FFMPEG_FOLDER, item)
            if os.path.isdir(item_path) and item != 'ffmpeg.exe':
                shutil.rmtree(item_path)
        
        st.success("FFmpeg berhasil didownload!")
        return True
        
    except Exception as e:
        st.error(f"Gagal mendownload FFmpeg: {str(e)}")
        return False

def process_video(uploaded_file):
    """Proses video untuk menghasilkan format intraframe dan interframe"""
    try:
        # Generate unique ID untuk file
        unique_id = str(uuid.uuid4())
        
        # Simpan file yang diupload
        input_filename = f"{unique_id}_{uploaded_file.name}"
        input_filepath = os.path.join(UPLOAD_FOLDER, input_filename)
        
        with open(input_filepath, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        # Nama file output
        mjpeg_filename = f"intraframe_{unique_id}.avi"
        mpeg_filename = f"interframe_{unique_id}.mp4"
        mjpeg_output = os.path.join(OUTPUT_FOLDER, mjpeg_filename)
        mpeg_output = os.path.join(OUTPUT_FOLDER, mpeg_filename)
        
        # Progress bar
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # Dapatkan path FFmpeg
        ffmpeg_path = get_ffmpeg_path()
        
        # Proses Intraframe (MJPEG)
        status_text.text("Memproses video intraframe (MJPEG)...")
        progress_bar.progress(25)
        
        if ffmpeg_path != "ffmpeg":  # Jika menggunakan path custom
            # Gunakan subprocess untuk path custom
            subprocess.run([
                ffmpeg_path, '-i', input_filepath, 
                '-vcodec', 'mjpeg', '-y', mjpeg_output
            ], check=True, capture_output=True)
        else:
            # Gunakan ffmpeg-python untuk sistem yang sudah ada FFmpeg
            ffmpeg.input(input_filepath).output(
                mjpeg_output, 
                vcodec='mjpeg'
            ).overwrite_output().run(quiet=True)
        
        progress_bar.progress(50)
        
        # Proses Interframe (MPEG4)
        status_text.text("Memproses video interframe (MPEG4)...")
        progress_bar.progress(75)
        
        if ffmpeg_path != "ffmpeg":  # Jika menggunakan path custom
            subprocess.run([
                ffmpeg_path, '-i', input_filepath, 
                '-vcodec', 'mpeg4', '-y', mpeg_output
            ], check=True, capture_output=True)
        else:
            ffmpeg.input(input_filepath).output(
                mpeg_output, 
                vcodec='mpeg4'
            ).overwrite_output().run(quiet=True)
        
        progress_bar.progress(100)
        status_text.text("Pemrosesan selesai!")
        
        # Cleanup input file
        os.remove(input_filepath)
        
        return mjpeg_output, mpeg_output, mjpeg_filename, mpeg_filename
        
    except Exception as e:
        st.error(f"Error saat memproses video: {str(e)}")
        return None, None, None, None

def get_file_size(filepath):
    """Mendapatkan ukuran file dalam format yang mudah dibaca"""
    size = os.path.getsize(filepath)
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024.0:
            return f"{size:.2f} {unit}"
        size /= 1024.0
    return f"{size:.2f} TB"

def main():
    st.set_page_config(
        page_title="Video Encoding App",
        page_icon="🎬",
        layout="wide"
    )
    
    st.title("🎬 Aplikasi Pengkodean Video")
    st.markdown("Aplikasi untuk mengkonversi video ke format **Intraframe (MJPEG)** dan **Interframe (MPEG4)**")
    
    # Cek FFmpeg
    if not check_ffmpeg():
        st.warning("⚠️ FFmpeg tidak ditemukan di sistem!")
        
        if platform.system() == "Windows":
            st.info("Aplikasi dapat mendownload FFmpeg secara otomatis untuk Windows.")
            if st.button("📥 Download FFmpeg Otomatis"):
                with st.spinner("Mendownload FFmpeg..."):
                    if download_ffmpeg_windows():
                        st.success("FFmpeg berhasil diinstall! Silakan refresh halaman.")
                        st.experimental_rerun()
        
        st.markdown("""
        **Atau install manual:**
        
        **Windows:**
        1. Download FFmpeg dari https://ffmpeg.org/download.html
        2. Extract file ke folder (misal: C:\\ffmpeg)
        3. Tambahkan C:\\ffmpeg\\bin ke PATH environment variable
        4. Restart aplikasi
        
        **macOS:**
        ```bash
        brew install ffmpeg
        ```
        
        **Linux (Ubuntu/Debian):**
        ```bash
        sudo apt update
        sudo apt install ffmpeg
        ```
        """)
        return
    
    # Sidebar dengan informasi
    with st.sidebar:
        st.header("ℹ️ Informasi")
        st.markdown("""
        **Intraframe (MJPEG):**
        - Setiap frame dikodekan secara independen
        - Ukuran file lebih besar
        - Kualitas editing lebih baik
        
        **Interframe (MPEG4):**
        - Frame dikodekan dengan referensi frame lain
        - Ukuran file lebih kecil
        - Efisien untuk streaming
        """)
        
        # Tampilkan status FFmpeg
        ffmpeg_path = get_ffmpeg_path()
        st.success(f"✅ FFmpeg ditemukan: {ffmpeg_path}")
    
    # Upload file
    uploaded_file = st.file_uploader(
        "Pilih file video",
        type=['mp4', 'avi', 'mov', 'mkv', 'flv', 'wmv'],
        help="Pilih file video yang ingin diproses"
    )
    
    if uploaded_file is not None:
        # Tampilkan informasi file
        col1, col2 = st.columns(2)
        with col1:
            st.info(f"**Nama file:** {uploaded_file.name}")
        with col2:
            st.info(f"**Ukuran:** {uploaded_file.size / (1024*1024):.2f} MB")
        
        # Tombol proses
        if st.button("🚀 Proses Video", type="primary"):
            with st.spinner("Memproses video..."):
                mjpeg_path, mpeg_path, mjpeg_name, mpeg_name = process_video(uploaded_file)
            
            if mjpeg_path and mpeg_path:
                st.success("✅ Video berhasil diproses!")
                
                # Tampilkan hasil
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("🎞️ Intraframe (MJPEG)")
                    if os.path.exists(mjpeg_path):
                        file_size = get_file_size(mjpeg_path)
                        st.write(f"Ukuran: {file_size}")
                        
                        with open(mjpeg_path, "rb") as file:
                            st.download_button(
                                label="📥 Download MJPEG",
                                data=file.read(),
                                file_name=mjpeg_name,
                                mime="video/x-msvideo"
                            )
                
                with col2:
                    st.subheader("🎬 Interframe (MPEG4)")
                    if os.path.exists(mpeg_path):
                        file_size = get_file_size(mpeg_path)
                        st.write(f"Ukuran: {file_size}")
                        
                        with open(mpeg_path, "rb") as file:
                            st.download_button(
                                label="📥 Download MPEG4",
                                data=file.read(),
                                file_name=mpeg_name,
                                mime="video/mp4"
                            )
                
                # Perbandingan ukuran file
                if os.path.exists(mjpeg_path) and os.path.exists(mpeg_path):
                    mjpeg_size = os.path.getsize(mjpeg_path)
                    mpeg_size = os.path.getsize(mpeg_path)
                    
                    st.subheader("📊 Perbandingan Ukuran File")
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("MJPEG", get_file_size(mjpeg_path))
                    with col2:
                        st.metric("MPEG4", get_file_size(mpeg_path))
                    with col3:
                        ratio = (mjpeg_size / mpeg_size) if mpeg_size > 0 else 0
                        st.metric("Rasio MJPEG/MPEG4", f"{ratio:.2f}x")
    
    # Footer
    st.markdown("---")
    st.markdown("*Aplikasi ini menggunakan FFmpeg untuk pemrosesan video*")

if __name__ == "__main__":
    main()