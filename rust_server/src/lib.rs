use pyo3::prelude::*;
use std::net::TcpListener;
use std::io::Read;
use std::sync::{Arc, Mutex};
use std::thread;
use once_cell::sync::Lazy;

// Global frame buffer (stores the latest JPEG frame)
static FRAME_BUFFER: Lazy<Arc<Mutex<Option<Vec<u8>>>>> =
    Lazy::new(|| Arc::new(Mutex::new(None)));

/// Start the TCP server in a background thread.
/// It listens on port 8888 for incoming JPEG frames.
#[pyfunction]
fn start_tcp_server() -> PyResult<()> {
    let frame_buffer = FRAME_BUFFER.clone();
    thread::spawn(move || {
        let listener = TcpListener::bind("0.0.0.0:8888")
            .expect("Failed to bind to port 8888");
        println!("Rust TCP server listening on port 8888...");
        for stream in listener.incoming() {
            match stream {
                Ok(stream) => {
                    let buffer = frame_buffer.clone();
                    thread::spawn(move || {
                        handle_client(stream, buffer);
                    });
                }
                Err(e) => eprintln!("Connection failed: {}", e),
            }
        }
    });
    Ok(())
}

/// Handles an individual TCP connection.
/// Expects an 8-byte little‑endian header indicating the frame size,
/// followed by that many bytes (a JPEG‑encoded frame).
fn handle_client(mut stream: std::net::TcpStream, frame_buffer: Arc<Mutex<Option<Vec<u8>>>>) {
    let header_size = 8; // u64 (8 bytes)
    let mut header_buf = [0u8; 8];
    loop {
        // Read the 8-byte length header.
        if let Err(e) = stream.read_exact(&mut header_buf) {
            eprintln!("Failed to read header: {}", e);
            break;
        }
        let frame_size = u64::from_le_bytes(header_buf) as usize;
        let mut frame_data = vec![0u8; frame_size];
        if let Err(e) = stream.read_exact(&mut frame_data) {
            eprintln!("Failed to read frame data: {}", e);
            break;
        }
        // Update the global frame buffer with the latest frame.
        if let Ok(mut buffer) = frame_buffer.lock() {
            *buffer = Some(frame_data);
        }
    }
}

/// Returns the latest frame as a byte array (or None if no frame received yet).
#[pyfunction]
fn get_latest_frame() -> PyResult<Option<Vec<u8>>> {
    let buffer = FRAME_BUFFER.lock().unwrap();
    Ok(buffer.clone())
}

/// The module’s Python interface.
#[pymodule]
fn rust_server(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(start_tcp_server, m)?)?;
    m.add_function(wrap_pyfunction!(get_latest_frame, m)?)?;
    Ok(())
}
