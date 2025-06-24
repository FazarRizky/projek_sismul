import streamlit as st
import os
import ffmpeg
import uuid
import tempfile
from pathlib import Path

# Konfigurasi folder
UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'output'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

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
        
        # Proses Intraframe (MJPEG)
        status_text.text("Memproses video intraframe (MJPEG)...")
        progress_bar.progress(25)
        
        ffmpeg.input(input_filepath).output(
            mjpeg_output, 
            vcodec='mjpeg'
        ).overwrite_output().run(quiet=True)
        
        progress_bar.progress(50)
        
        # Proses Interframe (MPEG4)
        status_text.text("Memproses video interframe (MPEG4)...")
        progress_bar.progress(75)
        
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
    
    st.title("Aplikasi Pengkodean Video")
    st.markdown("Aplikasi untuk mengkonversi video ke format **Intraframe (MJPEG)** dan **Interframe (MPEG4)**")
    
    # Sidebar dengan informasi
    with st.sidebar:
        st.header("Informasi")
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
        if st.button("Proses Video", type="primary"):
            with st.spinner("Memproses video..."):
                mjpeg_path, mpeg_path, mjpeg_name, mpeg_name = process_video(uploaded_file)
            
            if mjpeg_path and mpeg_path:
                st.success("Video berhasil diproses!")
                
                # Tampilkan hasil
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("Intraframe (MJPEG)")
                    if os.path.exists(mjpeg_path):
                        file_size = get_file_size(mjpeg_path)
                        st.write(f"Ukuran: {file_size}")
                        
                        with open(mjpeg_path, "rb") as file:
                            st.download_button(
                                label="Download MJPEG",
                                data=file.read(),
                                file_name=mjpeg_name,
                                mime="video/x-msvideo"
                            )
                
                with col2:
                    st.subheader("Interframe (MPEG4)")
                    if os.path.exists(mpeg_path):
                        file_size = get_file_size(mpeg_path)
                        st.write(f"Ukuran: {file_size}")
                        
                        with open(mpeg_path, "rb") as file:
                            st.download_button(
                                label="Download MPEG4",
                                data=file.read(),
                                file_name=mpeg_name,
                                mime="video/mp4"
                            )
                
                # Perbandingan ukuran file
                if os.path.exists(mjpeg_path) and os.path.exists(mpeg_path):
                    mjpeg_size = os.path.getsize(mjpeg_path)
                    mpeg_size = os.path.getsize(mpeg_path)
                    
                    st.subheader("Perbandingan Ukuran File")
                    
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