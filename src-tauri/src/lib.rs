mod python_bridge;

use python_bridge::PythonState;
use tauri::Manager;

#[tauri::command]
fn greet(name: &str) -> String {
    format!("Hello, {}! Welcome to SmartcardAgent.", name)
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_global_shortcut::Builder::default().build())
        .manage(PythonState::default())
        .invoke_handler(tauri::generate_handler![
            greet,
            python_bridge::start_python_service,
            python_bridge::stop_python_service,
            python_bridge::python_service_status,
            python_bridge::get_python_service_port,
        ])
        .setup(|app| {
            #[cfg(debug_assertions)]
            {
                use tauri_plugin_global_shortcut::{GlobalShortcutExt, Shortcut, Code, Modifiers};

                // Ctrl+Shift+I: 打开主窗口 DevTools
                let shortcut_main = Shortcut::new(Some(Modifiers::CONTROL | Modifiers::SHIFT), Code::KeyI);
                app.global_shortcut().on_shortcut(shortcut_main, |app, _shortcut, _event| {
                    if let Some(window) = app.get_webview_window("main") {
                        let _ = window.open_devtools();
                    }
                })?;
            }
            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}