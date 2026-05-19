mod python_bridge;

use python_bridge::PythonState;

#[tauri::command]
fn greet(name: &str) -> String {
    format!("Hello, {}! Welcome to SmartcardAgent.", name)
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .manage(PythonState::default())
        .invoke_handler(tauri::generate_handler![
            greet,
            python_bridge::start_python_service,
            python_bridge::stop_python_service,
            python_bridge::python_service_status,
            python_bridge::get_python_service_port,
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}