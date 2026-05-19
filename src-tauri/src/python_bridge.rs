use std::process::{Child, Command};
use std::sync::Mutex;
use tauri::Manager;

/// Python service state
pub struct PythonService {
    process: Option<Child>,
    port: u16,
}

/// Global state for Python service
pub struct PythonState {
    service: Mutex<Option<PythonService>>,
}

impl Default for PythonState {
    fn default() -> Self {
        Self {
            service: Mutex::new(None),
        }
    }
}

/// Start the Python service
/// Returns the port number the service is running on
#[tauri::command]
pub fn start_python_service(app: tauri::AppHandle) -> Result<u16, String> {
    let state = app.state::<PythonState>();
    let mut service_lock = state.service.lock().map_err(|e| e.to_string())?;

    // Check if already running
    if service_lock.is_some() {
        return Ok(8000);
    }

    // Determine the sidecar binary path
    let sidecar_name = if cfg!(target_os = "windows") {
        "python-service.exe"
    } else {
        "python-service"
    };

    // Try to start sidecar (bundled with app)
    let sidecar_result = Command::new(sidecar_name)
        .arg("--port")
        .arg("8000")
        .spawn();

    let process = match sidecar_result {
        Ok(p) => p,
        Err(_) => {
            // Fallback: try to run Python directly in development
            let python_result = Command::new("python")
                .arg("-m")
                .arg("uvicorn")
                .arg("main:app")
                .arg("--host")
                .arg("127.0.0.1")
                .arg("--port")
                .arg("8000")
                .current_dir("../python-service/src")
                .spawn();

            python_result.map_err(|e| format!("Failed to start Python service: {}", e))?
        }
    };

    let port = 8000;
    service_lock.replace(PythonService {
        process: Some(process),
        port,
    });

    Ok(port)
}

/// Stop the Python service
#[tauri::command]
pub fn stop_python_service(app: tauri::AppHandle) -> Result<(), String> {
    let state = app.state::<PythonState>();
    let mut service_lock = state.service.lock().map_err(|e| e.to_string())?;

    if let Some(mut service) = service_lock.take() {
        if let Some(mut process) = service.process.take() {
            process.kill().map_err(|e| format!("Failed to kill process: {}", e))?;
        }
    }

    Ok(())
}

/// Check if Python service is running
#[tauri::command]
pub fn python_service_status(app: tauri::AppHandle) -> Result<bool, String> {
    let state = app.state::<PythonState>();
    let service_lock = state.service.lock().map_err(|e| e.to_string())?;

    Ok(service_lock.is_some())
}

/// Get Python service port
#[tauri::command]
pub fn get_python_service_port(app: tauri::AppHandle) -> Result<u16, String> {
    let state = app.state::<PythonState>();
    let service_lock = state.service.lock().map_err(|e| e.to_string())?;

    match service_lock.as_ref() {
        Some(service) => Ok(service.port),
        None => Err("Python service not running".to_string()),
    }
}